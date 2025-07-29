from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel, JsonValue

T = TypeVar("T")


class BddFileResponse(BaseModel, Generic[T]):
    code: int
    data: T | None
    message: str | None
    trace_id: str


class BddFilePaged(BaseModel, Generic[T]):
    total: int
    items: list[T]


class Biz(str, Enum):
    chat = "chat"
    knowledge_base = "knowledgeBase"


class FileStatus(str, Enum):
    ok = "ok"
    uploading = "uploading"
    merging = "merging"
    error = "error"


class UploadParams(BaseModel):
    filename: str
    biz: Biz
    biz_params: JsonValue


class BddFileInfo(BaseModel):
    id: int
    filename: str
    size: int
    hashcode: str
    upload_at: datetime
    user_id: str
    status: FileStatus
    biz: Biz
    biz_params: JsonValue


class SyncChatFileToLocalResult(BaseModel):
    is_success: bool
    file_info: BddFileInfo
    local_path: Path
    error_message: str | None


class SyncChatFileToRemoteStatus(str, Enum):
    success = "success"
    failed = "failed"
    skipped = "skipped"


class SyncChatFileToRemoteResult(BaseModel):
    status: SyncChatFileToRemoteStatus
    file_id: int | None
    error_message: str | None


class MultipartUploadFileStatus(BaseModel):
    file_id: int
    status: FileStatus
    part_size: int
    uploaded_parts: list[int] | None
    remaining_parts: list[int] | None
