import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional

import httpx

if TYPE_CHECKING:
    from speedpix.file import Files
    from speedpix.prediction import Predictions


class Client:
    """SpeedPix API 客户端"""

    __client: Optional[httpx.Client] = None
    __async_client: Optional[httpx.AsyncClient] = None

    def __init__(
        self,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        endpoint: Optional[str] = None,
        timeout: Optional[float] = 30.0,
        user_agent: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        初始化SpeedPix客户端

        Args:
            app_key: 应用密钥（必需）
            app_secret: 应用密码（必需）
            endpoint: API端点（可选，默认: https://openai.edu-aliyun.com）
            timeout: 请求超时时间（秒）
            user_agent: 用户代理字符串
            **kwargs: 其他httpx客户端参数

        使用示例:
            # 最简方式
            client = Client("your-app-key", "your-app-secret")

            # 指定所有参数
            client = Client(
                app_key="your-app-key",
                app_secret="your-app-secret",
                endpoint="https://custom-endpoint.com"
            )

            # 从环境变量读取
            client = Client()  # 需要设置相应环境变量
        """
        self.endpoint = endpoint or os.getenv("SPEEDPIX_ENDPOINT") or "https://openai.edu-aliyun.com"
        self.app_key = app_key or os.getenv("SPEEDPIX_APP_KEY", "")
        self.app_secret = app_secret or os.getenv("SPEEDPIX_APP_SECRET", "")
        self.user_agent = user_agent or "speed-pix-python/1.0.0"
        self.timeout = timeout
        self._client_kwargs = kwargs

        # endpoint 现在有默认值，不再必需
        if not self.app_key:
            msg = "app_key is required, set SPEEDPIX_APP_KEY env var or pass app_key parameter"
            raise ValueError(msg)
        if not self.app_secret:
            msg = "app_secret is required, set SPEEDPIX_APP_SECRET env var or pass app_secret parameter"
            raise ValueError(msg)

    @property
    def _client(self) -> httpx.Client:
        """懒加载同步客户端"""
        if not self.__client:
            self.__client = httpx.Client(
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
                **self._client_kwargs,
            )
        return self.__client

    @property
    def _async_client(self) -> httpx.AsyncClient:
        """懒加载异步客户端"""
        if not self.__async_client:
            self.__async_client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
                **self._client_kwargs,
            )
        return self.__async_client

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    async def __aenter__(self) -> "Client":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()

    def close(self) -> None:
        """关闭同步客户端连接"""
        if self.__client:
            self.__client.close()
            self.__client = None

    async def aclose(self) -> None:
        """关闭异步客户端连接"""
        if self.__async_client:
            await self.__async_client.aclose()
            self.__async_client = None

    def _build_url(self, path: str) -> str:
        """构建完整的 URL"""
        return f"{self.endpoint}{path}"

    def _prepare_headers(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """准备请求头"""
        # 生成认证头
        auth_headers = self._generate_header("POST", path, json_data, headers)

        # 合并请求头
        request_headers = {**auth_headers}
        if headers:
            request_headers.update(headers)

        return request_headers

    def _generate_header(
        self,
        http_method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        hdrs: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """生成阿里云 API 网关认证头

        参考: https://help.aliyun.com/zh/api-gateway/traditional-api-gateway/use-digest-authentication-to-call-an-api
        """
        timestamp = time.time()
        date_str = time.strftime(
            "%a, %d %b %Y %H:%M:%S GMT",
            time.gmtime(timestamp),
        ).replace("GMT", "GMT+00:00")
        timestamp_str = str(int(timestamp * 1000))
        uuid_str = str(uuid.uuid4())
        json_header = "application/json; charset=utf-8"

        headers = {
            "date": date_str,
            "x-ca-key": self.app_key,
            "x-ca-timestamp": timestamp_str,
            "x-ca-nonce": uuid_str,
            "x-ca-signature-method": "HmacSHA256",
            "x-ca-signature-headers": "x-ca-timestamp,x-ca-key,x-ca-nonce,x-ca-signature-method",
            "Content-Type": json_header,
            "Accept": json_header,
        }

        # 构建签名字符串
        signature_parts = [
            http_method,
            json_header,  # Accept
        ]

        # 处理请求体的 MD5
        if body:
            body_json = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
            h = hashlib.md5()  # noqa: S324
            h.update(body_json.encode("utf-8"))
            body_md5_str = base64.b64encode(h.digest()).decode("utf-8")
            headers["content-md5"] = body_md5_str
            signature_parts.append(body_md5_str)
        else:
            signature_parts.append("")

        signature_parts.extend(
            [
                json_header,  # Content-Type
                date_str,
                f"x-ca-key:{self.app_key}",
                f"x-ca-nonce:{uuid_str}",
                "x-ca-signature-method:HmacSHA256",
                f"x-ca-timestamp:{timestamp_str}",
                path,
            ]
        )

        # 生成签名
        signature_string = "\n".join(signature_parts)
        h = hmac.new(
            self.app_secret.encode("utf-8"),
            signature_string.encode("utf-8"),
            hashlib.sha256,
        )
        headers["x-ca-signature"] = base64.b64encode(h.digest()).decode("utf-8")

        return headers

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """同步请求方法"""
        url = self._build_url(path)
        json_data = kwargs.pop("json", None)
        headers = kwargs.pop("headers", None)

        request_headers = self._prepare_headers(path, json_data, headers)

        # print(f"请求 URL: {url}")
        # print(f"请求方法: {method}")
        # print(f"请求头: {request_headers}")
        # if json_data is not None:
        #     print(f"请求体: {json.dumps(json_data, ensure_ascii=False)}")
        # else:
        #     print("请求体: None")

        response = self._client.request(
            method=method,
            url=url,
            json=json_data,
            headers=request_headers,
            **kwargs,
        )

        response.raise_for_status()
        return response

    async def _async_request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """异步请求方法"""
        url = self._build_url(path)
        json_data = kwargs.pop("json", None)
        headers = kwargs.pop("headers", None)

        request_headers = self._prepare_headers(path, json_data, headers)

        response = await self._async_client.request(
            method=method,
            url=url,
            json=json_data,
            headers=request_headers,
            **kwargs,
        )

        response.raise_for_status()
        return response

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        """发送同步 POST 请求"""
        return self._request("POST", path, json=json, headers=headers, **kwargs)

    async def async_post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        """发送异步 POST 请求"""
        return await self._async_request(
            "POST", path, json=json, headers=headers, **kwargs
        )

    @property
    def predictions(self) -> "Predictions":
        """预测任务命名空间"""
        from speedpix.prediction import Predictions

        return Predictions(client=self)

    @property
    def files(self) -> "Files":
        """文件上传命名空间"""
        from speedpix.file import Files

        return Files(client=self)

    def invoke(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]],
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """原始调用方法，保持兼容性"""
        return self.post(path, json=json_data, headers=headers)

    async def async_invoke(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]],
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """异步原始调用方法，保持兼容性"""
        return await self.async_post(path, json=json_data, headers=headers)

    def run(
        self,
        workflow_id: str,
        input: Dict[str, Any],  # noqa: A002
        *,
        wait: bool = True,
        version_id: Optional[str] = None,
        alias_id: Optional[str] = "main",
        randomise_seeds: Optional[bool] = None,
        return_temp_files: Optional[bool] = None,
        resource_config_id: str = "default",
        polling_interval: float = 1.0,
    ) -> Any:
        """
        运行模型并返回结果

        Args:
            workflow_id: 工作流ID
            input: 输入参数
            wait: 是否等待完成，默认 True
            version_id: 版本ID（可选）
            alias_id: 别名ID（可选）
            resource_config_id: 资源配置ID，默认 "default"
            polling_interval: 轮询间隔（秒），默认 1.0

        Returns:
            如果 wait=True，返回预测结果（output）
            如果 wait=False，返回 Prediction 对象
        """
        prediction = self.predictions.create(
            workflow_id=workflow_id,
            input=input,
            version_id=version_id,
            alias_id=alias_id,
            randomise_seeds=randomise_seeds,
            return_temp_files=return_temp_files,
            resource_config_id=resource_config_id,
        )

        if not wait:
            return prediction

        prediction = prediction.wait(polling_interval=polling_interval)

        if prediction.error:
            from speedpix.exceptions import PredictionError

            raise PredictionError(prediction)

        return prediction.output

    async def async_run(
        self,
        workflow_id: str,
        input: Dict[str, Any],  # noqa: A002
        *,
        wait: bool = True,
        version_id: Optional[str] = None,
        alias_id: Optional[str] = "main",
        randomise_seeds: Optional[bool] = None,
        return_temp_files: Optional[bool] = None,
        resource_config_id: str = "default",
        polling_interval: float = 1.0,
    ) -> Any:
        """
        异步运行模型并返回结果

        Args:
            workflow_id: 工作流ID
            input: 输入参数
            wait: 是否等待完成，默认 True
            version_id: 版本ID（可选）
            alias_id: 别名ID（可选）
            resource_config_id: 资源配置ID，默认 "default"
            polling_interval: 轮询间隔（秒），默认 1.0

        Returns:
            如果 wait=True，返回预测结果（output）
            如果 wait=False，返回 Prediction 对象
        """
        prediction = await self.predictions.async_create(
            workflow_id=workflow_id,
            input=input,
            version_id=version_id,
            alias_id=alias_id,
            randomise_seeds=randomise_seeds,
            return_temp_files=return_temp_files,
            resource_config_id=resource_config_id,
        )

        if not wait:
            return prediction

        prediction = await prediction.async_wait(polling_interval=polling_interval)

        if prediction.error:
            from speedpix.exceptions import PredictionError

            raise PredictionError(prediction)

        return prediction.output
