import asyncio
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Literal, Optional

from speedpix.file import FileEncodingStrategy
from speedpix.resource import Namespace

if TYPE_CHECKING:
    from speedpix.client import Client


@dataclass
class Prediction:
    """SpeedPix 预测任务对象"""

    id: str
    status: Optional[
        Literal["waiting", "running", "succeeded", "failed", "canceled"]
    ] = None
    """预测任务的状态"""
    input: Optional[Dict[str, Any]] = None
    output: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    invoke_id: Optional[str] = None

    # 内部使用字段
    _client: Optional["Client"] = None
    _workflow_id: Optional[str] = None
    _alias_id: Optional[str] = None

    def __post_init__(self) -> None:
        """后处理，转换输出中的 URL 为 FileOutput 对象"""
        from speedpix.helpers import transform_output

        if self.output:
            self.output = transform_output(self.output)

    def wait(self, polling_interval: float = 1.0) -> "Prediction":
        """等待预测完成"""
        if not self._client or not self.id:
            raise ValueError("Cannot wait on prediction without client and ID")

        while self.status not in ["succeeded", "failed", "canceled"]:
            time.sleep(polling_interval)
            self.reload()

        return self

    def reload(self) -> "Prediction":
        """重新加载预测状态"""
        from speedpix.schema import ComfyProgressResponse, ComfyResultResponse

        if not self._client or not self.id:
            raise ValueError("Cannot reload prediction without client and ID")

        # 查询进度
        progress_response = self._client.post(
            "/scc/comfy_get_progress", json={"taskId": self.id}
        )
        progress_response = ComfyProgressResponse.from_dict(progress_response.json())
        if (
            not progress_response
            or not progress_response.data
            or not progress_response.data.status
        ):
            self.status = "failed"
            self.error = "No progress data returned"
            return self

        progress_data = progress_response.data
        self.status = progress_data.status.value  # type: ignore
        if not progress_response.data.status.finished():
            return self

        # 获取结果
        result_response = self._client.post(
            "/scc/comfy_get_result", json={"taskId": self.id}
        )
        result_reponse = ComfyResultResponse.from_dict(result_response.json())
        self.invoke_id = result_reponse.api_invoke_id
        if result_reponse.status != 10:
            self.status = "failed"
            self.error = (
                result_reponse.sub_err_message
                or result_reponse.err_message
                or "Task failed"
            )
            self.error_code = result_reponse.sub_err_code or result_reponse.err_code
            return self

        self.output = result_reponse.data and result_reponse.data.result
        if self.output:
            from speedpix.helpers import transform_output
            self.output = transform_output(self.output)
        return self

    async def async_wait(self, polling_interval: float = 1.0) -> "Prediction":
        """异步等待预测完成"""
        if not self._client or not self.id:
            raise ValueError("Cannot wait on prediction without client and ID")

        while self.status not in ["succeeded", "failed", "canceled"]:
            await asyncio.sleep(polling_interval)
            await self.async_reload()

        return self

    async def async_reload(self) -> "Prediction":
        """异步重新加载预测状态"""
        from speedpix.schema import ComfyProgressResponse, ComfyResultResponse

        if not self._client or not self.id:
            raise ValueError("Cannot reload prediction without client and ID")

        # 查询进度
        progress_response = await self._client.async_post(
            "/scc/comfy_get_progress", json={"taskId": self.id}
        )
        progress_response = ComfyProgressResponse.from_dict(progress_response.json())
        if (
            not progress_response
            or not progress_response.data
            or not progress_response.data.status
        ):
            self.status = "failed"
            self.error = "No progress data returned"
            return self

        progress_data = progress_response.data
        self.status = progress_data.status.value  # type: ignore
        if not progress_response.data.status.finished():
            return self

        # 获取结果
        result_response = await self._client.async_post(
            "/scc/comfy_get_result", json={"taskId": self.id}
        )
        result_reponse = ComfyResultResponse.from_dict(result_response.json())
        self.invoke_id = result_reponse.api_invoke_id
        if result_reponse.status != 10:
            self.status = "failed"
            self.error = (
                result_reponse.sub_err_message
                or result_reponse.err_message
                or "Task failed"
            )
            self.error_code = result_reponse.sub_err_code or result_reponse.err_code
            return self

        self.output = result_reponse.data and result_reponse.data.result
        if self.output:
            from speedpix.helpers import transform_output
            self.output = transform_output(self.output)
        return self


class Predictions(Namespace):
    """SpeedPix 预测任务命名空间"""

    def __init__(self, client: "Client") -> None:
        super().__init__(client)

    def create(
        self,
        workflow_id: str,
        input: Dict[str, Any],
        version_id: Optional[str] = None,
        alias_id: Optional[str] = "main",
        randomise_seeds: Optional[bool] = None,
        return_temp_files: Optional[bool] = None,
        resource_config_id: str = "default",
        file_encoding_strategy: Optional[FileEncodingStrategy] = None,
    ) -> Prediction:
        """
        创建预测任务
        file_encoding_strategy: "base64" 或 "url"
        """
        from speedpix.helpers import encode_json
        from speedpix.schema import ComfyPromptRequest, ComfyPromptResponse

        # 处理输入中的文件对象，将它们转换为 URL 或 base64
        processed_input = encode_json(input, self._client, file_encoding_strategy=file_encoding_strategy or "url")

        # 构造请求
        request = ComfyPromptRequest(
            workflow_id=workflow_id,
            inputs=processed_input,
            version_id=version_id,
            alias_id=alias_id,
            randomise_seeds=randomise_seeds,
            return_temp_files=return_temp_files,
        )

        # 设置资源配置头
        headers = {}
        if resource_config_id:
            headers["X-SP-RESOURCE-CONFIG-ID"] = resource_config_id

        # 发送请求
        response = self._client.post(
            "/scc/comfy_prompt", json=request.to_dict(), headers=headers
        )

        try:
            response_json = response.json()
        except Exception as e:
            raise Exception(f"Failed to parse JSON response: {e}") from e

        result = ComfyPromptResponse.from_dict(response_json)

        if result.err_code:
            # 构建更易读的错误消息，避免中文转义问题
            error_parts = []
            if result.err_message:
                error_parts.append(f"错误: {result.err_message}")
            if result.sub_err_message:
                error_parts.append(f"详细: {result.sub_err_message}")
            if result.err_code:
                error_parts.append(f"错误码: {result.err_code}")
            if result.sub_err_code:
                error_parts.append(f"子错误码: {result.sub_err_code}")

            error_message = " | ".join(error_parts) if error_parts else "Unknown error"
            raise Exception(f"Failed to create prediction: {error_message}")

        if not result.data:
            raise Exception("Failed to create prediction: No data returned")

        # 创建 Prediction 对象
        prediction = Prediction(
            id=result.data.task_id,
            input=processed_input,
            status=result.data.status.value,  # type: ignore
            _client=self._client,
            _workflow_id=workflow_id,
            _alias_id=alias_id,
        )

        return prediction

    async def async_create(
        self,
        workflow_id: str,
        input: Dict[str, Any],
        version_id: Optional[str] = None,
        alias_id: Optional[str] = "main",
        randomise_seeds: Optional[bool] = None,
        return_temp_files: Optional[bool] = None,
        resource_config_id: str = "default",
        file_encoding_strategy: Optional[FileEncodingStrategy] = None,
    ) -> Prediction:
        """
        异步创建预测任务
        file_encoding_strategy: "base64" 或 "url"
        """
        from speedpix.helpers import async_encode_json
        from speedpix.schema import ComfyPromptRequest, ComfyPromptResponse

        # 异步处理输入中的文件对象，将它们转换为 URL 或 base64
        processed_input = await async_encode_json(input, self._client, file_encoding_strategy=file_encoding_strategy or "url")

        # 构造请求
        request = ComfyPromptRequest(
            workflow_id=workflow_id,
            inputs=processed_input,
            version_id=version_id,
            alias_id=alias_id,
            randomise_seeds=randomise_seeds,
            return_temp_files=return_temp_files,
        )

        # 设置资源配置头
        headers = {}
        if resource_config_id:
            headers["X-SP-RESOURCE-CONFIG-ID"] = resource_config_id

        # 发送请求
        response = await self._client.async_post(
            "/scc/comfy_prompt", json=request.to_dict(), headers=headers
        )
        result = ComfyPromptResponse.from_dict(response.json())

        if result.err_code:
            # 构建更易读的错误消息，避免中文转义问题
            error_parts = []
            if result.err_message:
                error_parts.append(f"错误: {result.err_message}")
            if result.sub_err_message:
                error_parts.append(f"详细: {result.sub_err_message}")
            if result.err_code:
                error_parts.append(f"错误码: {result.err_code}")
            if result.sub_err_code:
                error_parts.append(f"子错误码: {result.sub_err_code}")

            error_message = " | ".join(error_parts) if error_parts else "Unknown error"
            raise Exception(f"Failed to create prediction: {error_message}")

        if not result.data:
            raise Exception("Failed to create prediction: No data returned")

        # 创建 Prediction 对象
        prediction = Prediction(
            id=result.data.task_id,
            input=processed_input,
            status=result.data.status.value,  # type: ignore
            _client=self._client,
            _workflow_id=workflow_id,
            _alias_id=alias_id,
        )

        return prediction

    def get(self, prediction_id: str) -> Prediction:
        """获取预测任务状态"""
        prediction = Prediction(id=prediction_id, _client=self._client)
        return prediction.reload()

    async def async_get(self, prediction_id: str) -> Prediction:
        """异步获取预测任务状态"""
        prediction = Prediction(id=prediction_id, _client=self._client)
        return await prediction.async_reload()

    def cancel(self, prediction_id: str) -> Prediction:
        """取消预测任务（如果支持）"""
        from speedpix.schema import PredictResultStatusCode

        # 暂不支持取消，这里只是接口占位
        prediction = Prediction(id=prediction_id, _client=self._client)
        prediction.status = PredictResultStatusCode.TASK_FAILED.value
        prediction.error = "Canceled"
        return prediction

    async def async_cancel(self, prediction_id: str) -> Prediction:
        """异步取消预测任务（如果支持）"""
        from speedpix.schema import PredictResultStatusCode

        # 暂不支持取消，这里只是接口占位
        prediction = Prediction(id=prediction_id, _client=self._client)
        prediction.status = PredictResultStatusCode.TASK_FAILED.value
        prediction.error = "Canceled"
        return prediction
