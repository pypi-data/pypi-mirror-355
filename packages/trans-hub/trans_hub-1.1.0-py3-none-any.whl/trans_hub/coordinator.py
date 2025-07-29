# trans_hub/coordinator.py (v1.1 最终版)
"""
本模块包含 Trans-Hub 引擎的主协调器 (Coordinator)。
它采用动态引擎发现机制，并负责编排所有核心工作流，包括任务处理、重试、
速率限制、请求处理和垃圾回收等。
"""

import re
import time
from typing import Any, Dict, Generator, List, Optional

import structlog

from trans_hub.config import TransHubConfig
from trans_hub.engine_registry import ENGINE_REGISTRY
from trans_hub.engines.base import BaseTranslationEngine
from trans_hub.interfaces import PersistenceHandler
from trans_hub.rate_limiter import RateLimiter
from trans_hub.types import (
    ContentItem,
    EngineBatchItemResult,
    EngineError,
    EngineSuccess,
    TranslationResult,
    TranslationStatus,
)
from trans_hub.utils import get_context_hash

# 获取一个 logger
logger = structlog.get_logger(__name__)


class Coordinator:
    """同步版本的主协调器。
    实现了动态引擎加载、重试、速率限制等所有核心功能。
    """

    def __init__(
        self,
        config: TransHubConfig,
        persistence_handler: PersistenceHandler,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        """初始化协调器。"""
        self.config = config
        self.handler = persistence_handler
        self.active_engine_name = config.active_engine
        self.rate_limiter = rate_limiter

        logger.info(
            "正在初始化 Coordinator...", available_engines=list(ENGINE_REGISTRY.keys())
        )

        if self.active_engine_name not in ENGINE_REGISTRY:
            raise ValueError(
                f"指定的活动引擎 '{self.active_engine_name}' 不可用。"
                f"可能原因：1. 引擎不存在；2. 缺少相关依赖（如 'openai' 或 'translators'）。"
                f"当前可用引擎: {list(ENGINE_REGISTRY.keys())}"
            )

        engine_class = ENGINE_REGISTRY[self.active_engine_name]

        engine_config_data = getattr(
            config.engine_configs, self.active_engine_name, None
        )
        if not engine_config_data:
            raise ValueError(
                f"在配置中未找到活动引擎 '{self.active_engine_name}' 的配置。"
            )

        engine_config_instance = engine_class.CONFIG_MODEL(
            **engine_config_data.model_dump()
        )

        self.active_engine: BaseTranslationEngine[Any] = engine_class(
            config=engine_config_instance
        )
        logger.info(
            f"Coordinator 初始化完成。活动引擎: '{self.active_engine_name}', "
            f"速率限制器: {'已启用' if self.rate_limiter else '未启用'}"
        )

    def process_pending_translations(
        self,
        target_lang: str,
        batch_size: int = 50,
        limit: Optional[int] = None,
        max_retries: Optional[int] = None,
        initial_backoff: Optional[float] = None,
    ) -> Generator[TranslationResult, None, None]:
        """处理指定语言的待翻译任务，内置重试和速率限制逻辑。

        在处理过程中，如果一个任务关联了 business_id，它的 last_seen_at 时间戳会被更新。
        """
        self._validate_lang_codes([target_lang])

        # 如果未提供重试参数，则从配置中获取
        max_retries = (
            max_retries
            if max_retries is not None
            else self.config.retry_policy.max_attempts
        )
        initial_backoff = (
            initial_backoff
            if initial_backoff is not None
            else self.config.retry_policy.initial_backoff
        )

        logger.info(
            f"开始处理 '{target_lang}' 的待翻译任务 (max_retries={max_retries})"
        )

        content_batches = self.handler.stream_translatable_items(
            lang_code=target_lang,
            statuses=[TranslationStatus.PENDING, TranslationStatus.FAILED],
            batch_size=batch_size,
            limit=limit,
        )

        for batch in content_batches:
            logger.debug(f"正在处理一个包含 {len(batch)} 个内容的批次。")
            texts_to_translate = [item.value for item in batch]

            # 未来优化点: 为了将原始 context 字典传递给引擎，
            # ContentItem DTO 和 stream_translatable_items 方法需要被重构以携带它。
            # 当前，我们无法直接获取原始 context，因此将其设为 None。
            # 这对于我们现有的引擎（translators, debug）是可接受的。
            context_for_engine = None

            engine_results: List[EngineBatchItemResult] = []
            for attempt in range(max_retries + 1):
                try:
                    if self.rate_limiter:
                        self.rate_limiter.acquire(1)

                    engine_results = self.active_engine.translate_batch(
                        texts=texts_to_translate,
                        target_lang=target_lang,
                        context=context_for_engine,
                    )

                    has_retryable_errors = any(
                        isinstance(r, EngineError) and r.is_retryable
                        for r in engine_results
                    )

                    if not has_retryable_errors:
                        logger.info(
                            f"批次处理成功或仅包含不可重试错误 (尝试次数: {attempt + 1})。"
                        )
                        break

                    logger.warning(
                        f"批次中包含可重试的错误 (尝试次数: {attempt + 1}/{max_retries + 1})。",
                        extra_info="将在退避后重试批次...",
                    )

                except Exception as e:
                    logger.error(
                        f"引擎在处理批次时抛出异常 (尝试次数: {attempt + 1})",
                        exc_info=True,
                    )
                    engine_results = [
                        EngineError(error_message=str(e), is_retryable=True)
                    ] * len(batch)

                if attempt < max_retries:
                    backoff_time = initial_backoff * (2**attempt)
                    logger.info(f"退避 {backoff_time:.2f} 秒后重试...")
                    time.sleep(backoff_time)
                else:
                    logger.error(
                        f"已达到最大重试次数 ({max_retries})，放弃当前批次的重试。"
                    )

            final_results_to_save: List[TranslationResult] = []
            for item, engine_result in zip(batch, engine_results):
                retrieved_business_id = self.handler.get_business_id_for_content(
                    content_id=item.content_id, context_hash=item.context_hash
                )

                # 核心修正：如果找到了 business_id，就更新它的活跃时间！
                # 这确保了被处理的任务不会被 GC 错误地清理。
                if retrieved_business_id:
                    self.handler.touch_source(retrieved_business_id)

                result = self._convert_to_translation_result(
                    item=item,
                    engine_result=engine_result,
                    target_lang=target_lang,
                    retrieved_business_id=retrieved_business_id,
                )
                final_results_to_save.append(result)
                yield result

            if final_results_to_save:
                self.handler.save_translations(final_results_to_save)

    def _convert_to_translation_result(
        self,
        item: ContentItem,
        engine_result: EngineBatchItemResult,
        target_lang: str,
        retrieved_business_id: Optional[str] = None,
    ) -> TranslationResult:
        """内部辅助方法，将引擎原始输出转换为统一的 TranslationResult DTO。"""
        if isinstance(engine_result, EngineSuccess):
            return TranslationResult(
                original_content=item.value,
                translated_content=engine_result.translated_text,
                target_lang=target_lang,
                status=TranslationStatus.TRANSLATED,
                engine=self.active_engine_name,
                from_cache=False,
                context_hash=item.context_hash,
                business_id=retrieved_business_id,
            )
        elif isinstance(engine_result, EngineError):
            return TranslationResult(
                original_content=item.value,
                translated_content=None,
                target_lang=target_lang,
                status=TranslationStatus.FAILED,
                engine=self.active_engine_name,
                error=engine_result.error_message,
                from_cache=False,
                context_hash=item.context_hash,
                business_id=retrieved_business_id,
            )
        else:
            raise TypeError(
                f"未知的引擎结果类型: {type(engine_result)}。预期 EngineSuccess 或 EngineError。"
            )

    def request(
        self,
        target_langs: List[str],
        text_content: str,
        business_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        source_lang: Optional[str] = None,
    ) -> None:
        """统一的翻译请求入口。"""
        self._validate_lang_codes(target_langs)
        if source_lang:
            self._validate_lang_codes([source_lang])

        logger.debug(
            "收到翻译请求",
            business_id=business_id,
            target_langs=target_langs,
            text_content=text_content[:30] + "...",
        )
        context_hash = get_context_hash(context)
        content_id: Optional[int] = None

        if business_id:
            source_result = self.handler.update_or_create_source(
                text_content=text_content,
                business_id=business_id,
                context_hash=context_hash,
            )
            content_id = source_result.content_id

        with self.handler.transaction() as cursor:
            if content_id is None:
                cursor.execute(
                    "SELECT id FROM th_content WHERE value = ?", (text_content,)
                )
                row = cursor.fetchone()
                if row:
                    content_id = row["id"]
                else:
                    cursor.execute(
                        "INSERT INTO th_content (value) VALUES (?)", (text_content,)
                    )
                    content_id = cursor.lastrowid

            if content_id is None:
                raise RuntimeError("无法为翻译任务确定 content_id。")

            insert_sql = """
                INSERT OR IGNORE INTO th_translations
                (content_id, lang_code, context_hash, status, source_lang_code, engine_version)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params_to_insert = []
            for lang in target_langs:
                cursor.execute(
                    "SELECT status FROM th_translations WHERE content_id = ? AND lang_code = ? AND context_hash = ?",
                    (content_id, lang, context_hash),
                )
                existing_translation = cursor.fetchone()

                if (
                    existing_translation
                    and existing_translation["status"]
                    == TranslationStatus.TRANSLATED.value
                ):
                    continue

                params_to_insert.append(
                    (
                        content_id,
                        lang,
                        context_hash,
                        TranslationStatus.PENDING.value,
                        source_lang,
                        self.active_engine.VERSION,
                    )
                )

            if params_to_insert:
                cursor.executemany(insert_sql, params_to_insert)
                logger.info(
                    f"为 content_id={content_id} 确保了 {cursor.rowcount} 个新的 PENDING 任务。"
                )

    def run_garbage_collection(
        self, retention_days: Optional[int] = None, dry_run: bool = False
    ) -> dict:
        """运行垃圾回收进程。"""
        # 核心修正：如果未提供 retention_days，则从配置中获取
        if retention_days is None:
            retention_days = self.config.gc_retention_days

        logger.info(
            f"Coordinator 正在启动垃圾回收 (retention_days={retention_days}, dry_run={dry_run})..."
        )
        return self.handler.garbage_collect(
            retention_days=retention_days, dry_run=dry_run
        )

    def _validate_lang_codes(self, lang_codes: List[str]):
        """内部辅助方法：校验语言代码列表中的每个代码是否符合标准格式。"""
        lang_code_pattern = re.compile(r"^[a-z]{2,3}(-[A-Z]{2})?$")

        for code in lang_codes:
            if not lang_code_pattern.match(code):
                raise ValueError(
                    f"提供的语言代码 '{code}' 格式无效。 "
                    "请使用标准格式，例如 'en', 'de', 'zh-CN'。"
                )

    def close(self):
        """关闭协调器及其持有的资源。"""
        logger.info("正在关闭 Coordinator...")
        self.handler.close()
