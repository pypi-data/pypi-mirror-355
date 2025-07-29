"""trans_hub/types.py (v0.1 - 最终最终修正版 - 修正 Ruff 警告)

本模块定义了 Trans-Hub 引擎的核心数据传输对象 (DTOs)、枚举和数据结构。
它是应用内部数据契约的“单一事实来源”，已根据最终版文档进行更新。
所有与外部或模块间交互的数据结构都应在此定义。
"""
from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, Field

# 移除未使用的导入
# from typing import Dict, Any


# ==============================================================================
#  枚举 (Enumerations)
# ==============================================================================


class TranslationStatus(str, Enum):
    """表示翻译记录在数据库中的生命周期状态。"""

    PENDING = "PENDING"
    TRANSLATING = "TRANSLATING"
    TRANSLATED = "TRANSLATED"
    FAILED = "FAILED"
    APPROVED = "APPROVED"


# ==============================================================================
#  引擎层 DTOs
# ==============================================================================


class EngineSuccess(BaseModel):
    """代表从翻译引擎返回的单次 *成功* 的翻译结果。"""

    translated_text: str
    detected_source_lang: Optional[str] = None


class EngineError(BaseModel):
    """代表从翻译引擎返回的单次 *失败* 的翻译结果。"""

    error_message: str
    is_retryable: bool


EngineBatchItemResult = Union[EngineSuccess, EngineError]

# ==============================================================================
#  协调器与持久化层 DTOs
# ==============================================================================


class TranslationResult(BaseModel):
    """由 `Coordinator` 返回给最终用户的综合结果对象，包含了完整的上下文信息。"""

    # 核心内容
    original_content: str
    translated_content: Optional[str] = None
    target_lang: str

    # 状态与元数据
    status: TranslationStatus
    engine: Optional[str] = None
    from_cache: bool  # 结果是否来自缓存。
    error: Optional[str] = None

    # 来源与上下文标识
    business_id: Optional[str] = Field(
        default=None, description="与此内容关联的业务ID。"
    )
    context_hash: str = Field(
        description="用于区分不同上下文翻译的哈希值。现在总是非NULL。"
    )


class SourceUpdateResult(BaseModel):
    """`PersistenceHandler.update_or_create_source` 方法的返回结果。"""

    content_id: int
    is_newly_created: bool


class ContentItem(BaseModel):
    """[修正] 内部处理时，代表一个待翻译任务的结构化对象。
    不再包含 business_id，因为它应该由 Coordinator 动态从 th_sources 获取。
    """

    content_id: int
    value: str
    context_hash: str  # 现在是 NOT NULL


# ==============================================================================
#  常量
# ==============================================================================

# 定义一个特殊的字符串，用于表示“全局”或“无上下文”的翻译。
GLOBAL_CONTEXT_SENTINEL = "__GLOBAL__"
