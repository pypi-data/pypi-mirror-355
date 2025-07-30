import base64
import io
import mimetypes
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import GeneratorType
from typing import TYPE_CHECKING, Any, Optional

import requests

from speedpix.file import FileEncodingStrategy

if TYPE_CHECKING:
    from speedpix.client import Client

try:
    import numpy as np  # type: ignore

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


@dataclass
class FileOutput:
    """文件输出包装器"""

    url: str
    _content: Optional[bytes] = None

    def read(self) -> bytes:
        """读取文件内容"""
        if self._content is None:
            response = requests.get(self.url, timeout=100)
            response.raise_for_status()
            self._content = response.content
        # 在这里，_content 已经不是 None 了
        if self._content is None:
            raise RuntimeError("Failed to read file content")
        return self._content

    def save(self, path: str) -> None:
        """保存文件到本地"""
        with open(path, "wb") as f:
            f.write(self.read())

    async def async_read(self) -> bytes:
        """异步读取文件内容"""
        if self._content is None:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(self.url, timeout=100)
                response.raise_for_status()
                self._content = response.content

        if self._content is None:
            raise RuntimeError("Failed to read file content")
        return self._content

    async def async_save(self, path: str) -> None:
        """异步保存文件到本地"""
        import aiofiles
        content = await self.async_read()
        async with aiofiles.open(path, "wb") as f:
            await f.write(content)


def encode_json(
    obj: Any,
    client: "Client",
    file_encoding_strategy: Optional[FileEncodingStrategy] = None,
) -> Any:
    """
    返回对象的 JSON 兼容版本，将文件对象转换为可用的 URL。
    file_encoding_strategy: "base64" 或 "url"
    """
    if isinstance(obj, dict):
        return {
            key: encode_json(
                value, client, file_encoding_strategy=file_encoding_strategy
            )
            for key, value in obj.items()
        }
    if isinstance(obj, (list, set, frozenset, GeneratorType, tuple)):
        return [
            encode_json(value, client, file_encoding_strategy=file_encoding_strategy)
            for value in obj
        ]
    if isinstance(obj, str):
        if not (
            obj.startswith(("/", "./", "../", "~")) or (len(obj) > 1 and obj[1] == ":")
        ):
            return obj

        try:
            path = Path(obj)
            if path.is_file():
                with path.open("rb") as f:
                    return encode_json(
                        f, client, file_encoding_strategy=file_encoding_strategy
                    )
        except (OSError, ValueError):
            pass
        return obj
    if isinstance(obj, Path):
        with obj.open("rb") as f:
            return encode_json(f, client, file_encoding_strategy=file_encoding_strategy)
    if isinstance(obj, io.IOBase):
        if file_encoding_strategy == "base64":
            obj.seek(0, 2)
            size = obj.tell()
            obj.seek(0)
            if size > 1024 * 1024:
                raise ValueError("文件过大，base64 编码仅支持小于 1MB 的文件")
            return base64_encode_file(obj)
        # 上传文件并返回访问 URL
        file_obj = client.files.create(obj)
        return file_obj.access_url
    if HAS_NUMPY:
        if isinstance(obj, np.integer):  # type: ignore
            return int(obj)
        if isinstance(obj, np.floating):  # type: ignore
            return float(obj)
        if isinstance(obj, np.ndarray):  # type: ignore
            return obj.tolist()
    return obj


async def async_encode_json(
    obj: Any,
    client: "Client",
    file_encoding_strategy: Optional[FileEncodingStrategy] = None,
) -> Any:
    """
    异步返回对象的 JSON 兼容版本，将文件对象转换为可用的 URL。
    file_encoding_strategy: "base64" 或 "url"
    """
    if isinstance(obj, dict):
        return {
            key: (
                await async_encode_json(
                    value, client, file_encoding_strategy=file_encoding_strategy
                )
            )
            for key, value in obj.items()
        }
    if isinstance(obj, (list, set, frozenset, GeneratorType, tuple)):
        return [
            (
                await async_encode_json(
                    value, client, file_encoding_strategy=file_encoding_strategy
                )
            )
            for value in obj
        ]
    if isinstance(obj, str):
        # 检查字符串是否为有效的文件路径
        path = Path(obj)
        if path.exists() and path.is_file():
            with path.open("rb") as file:
                return await async_encode_json(
                    file, client, file_encoding_strategy=file_encoding_strategy
                )
        return obj
    if isinstance(obj, Path):
        with obj.open("rb") as file:
            return await async_encode_json(
                file, client, file_encoding_strategy=file_encoding_strategy
            )
    if isinstance(obj, io.IOBase):
        if file_encoding_strategy == "base64":
            obj.seek(0, 2)
            size = obj.tell()
            obj.seek(0)
            if size > 1024 * 1024:
                raise ValueError("文件过大，base64 编码仅支持小于 1MB 的文件")
            return base64_encode_file(obj)
        # 异步上传文件并返回访问 URL
        file_obj = await client.files.async_create(obj)
        return file_obj.access_url
    if HAS_NUMPY:
        if isinstance(obj, np.integer):  # type: ignore
            return int(obj)
        if isinstance(obj, np.floating):  # type: ignore
            return float(obj)
        if isinstance(obj, np.ndarray):  # type: ignore
            return obj.tolist()
    return obj


def base64_encode_file(file: io.IOBase) -> str:
    """
    Base64 编码文件。

    Args:
        file: 要上传的文件句柄。
    Returns:
        str: Base64 编码的数据 URI。
    """
    file.seek(0)
    body = file.read()

    # 确保文件句柄是字节格式
    body = body.encode("utf-8") if isinstance(body, str) else body
    encoded_body = base64.b64encode(body).decode("utf-8")

    mime_type = (
        mimetypes.guess_type(getattr(file, "name", ""))[0] or "application/octet-stream"
    )
    return f"data:{mime_type};base64,{encoded_body}"


def transform_output(value: Any) -> Any:
    """
    转换预测输出，处理返回的 URL 格式。
    将 URL 字符串转换为 FileOutput 对象以支持 .save() 和 .read() 方法。
    """

    def transform(obj: Any) -> Any:
        if isinstance(obj, Mapping):
            return {k: transform(v) for k, v in obj.items()}
        if isinstance(obj, Sequence) and not isinstance(obj, str):
            return [transform(item) for item in obj]
        # 检查是否为 HTTP/HTTPS URL，如果是则转换为 FileOutput 对象
        if isinstance(obj, str) and (obj.startswith("http://") or obj.startswith("https://")):
            return FileOutput(url=obj)
        return obj

    return transform(value)
