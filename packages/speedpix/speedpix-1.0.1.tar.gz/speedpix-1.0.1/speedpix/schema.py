from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from dataclass_wizard import DumpMeta, JSONWizard


class JSONe(JSONWizard):
    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        DumpMeta(key_transform="SNAKE").bind_to(cls)


class PredictResultStatusCode(Enum):
    TASK_INPROGRESS = "running"
    TASK_FAILED = "failed"
    TASK_QUEUE = "waiting"
    TASK_FINISH = "succeeded"

    def finished(self) -> bool:
        return self in (
            PredictResultStatusCode.TASK_FAILED,
            PredictResultStatusCode.TASK_FINISH,
        )


# 网关响应
@dataclass
class GatewayResponse(JSONe):
    status: Optional[int] = 0
    err_code: Optional[str] = ""
    err_message: Optional[str] = ""
    sub_err_code: Optional[str] = ""
    sub_err_message: Optional[str] = ""
    api_invoke_id: Optional[str] = ""


# 提交任务请求
@dataclass
class ComfyPromptRequest(JSONe):
    workflow_id: str
    version_id: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None
    alias_id: Optional[str] = "main"
    randomise_seeds: Optional[bool] = None
    return_temp_files: Optional[bool] = None


# 提交任务请求响应
@dataclass
class ComfyPromptResponseData(JSONe):
    task_id: str
    status: Optional[PredictResultStatusCode] = PredictResultStatusCode.TASK_INPROGRESS
    estimated_duration_in_seconds: Optional[float] = None


@dataclass
class ComfyPromptResponse(GatewayResponse):
    data: Optional[ComfyPromptResponseData] = None


# 查询进度响应
@dataclass
class ComfyProgressResponseData(JSONe):
    task_id: str
    progress: float
    eta_relative: int
    message: Optional[str] = ""
    status: Optional[PredictResultStatusCode] = PredictResultStatusCode.TASK_INPROGRESS


@dataclass
class ComfyProgressResponse(GatewayResponse):
    data: Optional[ComfyProgressResponseData] = None


# 查询结果响应
@dataclass
class ComfyResultResponseData(JSONe):
    task_id: str
    images: Optional[List[str]] = None
    info: Optional[Dict[str, str]] = None
    parameters: Optional[Dict[str, str]] = None
    status: Optional[PredictResultStatusCode] = PredictResultStatusCode.TASK_INPROGRESS
    imgs_bytes: Optional[List[str]] = None
    result: Optional[Dict] = None

    def get_output(self) -> Any:
        """获取输出结果，只使用 result 字段"""
        return self.result


@dataclass
class ComfyResultResponse(GatewayResponse):
    data: Optional[ComfyResultResponseData] = None
