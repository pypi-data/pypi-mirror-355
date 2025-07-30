"""SpeedPix Python SDK

A Python client library for the SpeedPix API, providing a simple interface
for AI image generation workflows similar to Replicate's API.

Basic usage:
    >>> import speedpix
    >>> client = speedpix.Client(
    ...     endpoint="your-endpoint.com",
    ...     app_key="your-app-key",
    ...     app_secret="your-app-secret"
    ... )
    >>>
    >>> # Method 1: Direct run
    >>> output = client.run(
    ...     workflow_id="your-workflow-id",
    ...     input={"prompt": "A beautiful landscape"}
    ... )
    >>>
    >>> # Method 2: Create and wait
    >>> prediction = client.predictions.create(
    ...     workflow_id="your-workflow-id",
    ...     input={"prompt": "A beautiful landscape"}
    ... )
    >>> result = prediction.wait()
    >>> print(result.output)
"""

from typing import Any, Dict, Optional

from speedpix.client import Client
from speedpix.exceptions import PredictionError, SpeedPixException
from speedpix.file import File, Files
from speedpix.helpers import (
    FileOutput,
    async_encode_json,
    encode_json,
    transform_output,
)
from speedpix.prediction import Prediction, Predictions
from speedpix.resource import Namespace
from speedpix.schema import (
    ComfyProgressResponse,
    ComfyPromptRequest,
    ComfyPromptResponse,
    ComfyResultResponse,
    PredictResultStatusCode,
)

# 默认客户端实例，类似 replicate 的使用方式
_default_client: Optional[Client] = None


def _get_default_client() -> Client:
    """获取默认客户端实例"""
    global _default_client
    if _default_client is None:
        _default_client = Client()
    return _default_client


def run(
    workflow_id: str,
    input: Dict[str, Any],  # noqa: A002
    *,
    wait: bool = True,
    version_id: Optional[str] = None,
    alias_id: Optional[str] = None,
    resource_config_id: str = "default",
    polling_interval: float = 1.0,
    client: Optional[Client] = None,
) -> Any:
    """
    全局 run 函数，类似 replicate.run()

    Args:
        workflow_id: 工作流ID
        input: 输入参数
        wait: 是否等待完成，默认 True
        version_id: 版本ID（可选）
        alias_id: 别名ID（可选）
        resource_config_id: 资源配置ID，默认 "default"
        polling_interval: 轮询间隔（秒），默认 1.0
        client: 客户端实例，如果不提供则使用默认客户端

    Returns:
        如果 wait=True，返回预测结果（output）
        如果 wait=False，返回 Prediction 对象
    """
    if client is None:
        client = _get_default_client()

    return client.run(
        workflow_id=workflow_id,
        input=input,
        wait=wait,
        version_id=version_id,
        alias_id=alias_id,
        resource_config_id=resource_config_id,
        polling_interval=polling_interval,
    )


async def async_run(
    workflow_id: str,
    input: Dict[str, Any],  # noqa: A002
    *,
    wait: bool = True,
    version_id: Optional[str] = None,
    alias_id: Optional[str] = None,
    resource_config_id: str = "default",
    polling_interval: float = 1.0,
    client: Optional[Client] = None,
) -> Any:
    """
    全局异步 run 函数，类似 replicate.async_run()

    Args:
        workflow_id: 工作流ID
        input: 输入参数
        wait: 是否等待完成，默认 True
        version_id: 版本ID（可选）
        alias_id: 别名ID（可选）
        resource_config_id: 资源配置ID，默认 "default"
        polling_interval: 轮询间隔（秒），默认 1.0
        client: 客户端实例，如果不提供则使用默认客户端

    Returns:
        如果 wait=True，返回预测结果（output）
        如果 wait=False，返回 Prediction 对象
    """
    if client is None:
        client = _get_default_client()

    return await client.async_run(
        workflow_id=workflow_id,
        input=input,
        wait=wait,
        version_id=version_id,
        alias_id=alias_id,
        resource_config_id=resource_config_id,
        polling_interval=polling_interval,
    )


__version__ = "1.0.0"
__all__ = [
    "Client",
    "ComfyProgressResponse",
    "ComfyPromptRequest",
    "ComfyPromptResponse",
    "ComfyResultResponse",
    "File",
    "FileOutput",
    "Files",
    "Namespace",
    "PredictionError",
    "PredictResultStatusCode",
    "Prediction",
    "Predictions",
    "SpeedPixException",
    "async_encode_json",
    "async_run",
    "encode_json",
    "run",
    "transform_output",
]
