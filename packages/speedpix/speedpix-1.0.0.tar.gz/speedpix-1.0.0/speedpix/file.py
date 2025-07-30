import io
import mimetypes
import os
import pathlib
from typing import BinaryIO, Literal, Optional, TypedDict, Union

from typing_extensions import NotRequired, Unpack

from speedpix.resource import Namespace, Resource

FileEncodingStrategy = Literal["base64", "url"]

class File(Resource):
    """
    SpeedPix 文件上传后的文件对象
    """

    path: str
    """文件路径"""

    expire_time: Optional[str]
    """过期时间"""

    upload_url: str
    """上传 URL"""

    access_url: str
    """访问 URL，用于后续推理"""

    object_key: str
    """对象键"""

    # 本地文件信息
    name: Optional[str] = None
    """文件名"""

    content_type: Optional[str] = None
    """内容类型"""

    size: Optional[int] = None
    """文件大小（字节）"""

    @property
    def url(self) -> str:
        """获取文件的访问 URL"""
        return self.access_url

    def __str__(self) -> str:
        """字符串表示返回访问 URL"""
        return self.access_url


class Files(Namespace):
    """文件管理命名空间"""

    class CreateFileParams(TypedDict):
        """创建文件的参数"""

        filename: NotRequired[str]
        """文件名"""

        content_type: NotRequired[str]
        """内容类型"""

    def create(
        self,
        file: Union[str, pathlib.Path, BinaryIO, io.IOBase],
        **params: Unpack["Files.CreateFileParams"],
    ) -> File:
        """
        上传文件到 SpeedPix，可以用作模型输入

        Args:
            file: 文件路径或文件对象
            **params: 可选参数

        Returns:
            File: 上传后的文件对象
        """
        if isinstance(file, (str, pathlib.Path)):
            file_path = pathlib.Path(file)
            params["filename"] = params.get("filename", file_path.name)
            with open(file, "rb") as f:
                return self.create(f, **params)
        elif not isinstance(file, (io.IOBase, BinaryIO)):
            raise ValueError(
                "不支持的文件类型。必须是文件路径或文件对象。"
            )

        # 准备文件信息
        filename = params.get("filename", os.path.basename(getattr(file, "name", "file")))
        content_type = (
            params.get("content_type")
            or mimetypes.guess_type(filename)[0]
            or "application/octet-stream"
        )

        # 获取文件大小
        file.seek(0, 2)  # 移动到文件末尾
        file_size = file.tell()
        file.seek(0)  # 回到文件开头

        # 1. 调用 /scc/sp_create_temp_file_upload_sign 获取上传签名
        sign_response = self._client._request(
            "POST",
            "/scc/sp_create_temp_file_upload_sign",
            json={
                "contentType": content_type,
                "originalFilename": filename,
            },
        )

        sign_data = sign_response.json().get("data", {})
        upload_url = sign_data.get("uploadUrl")

        if not upload_url:
            raise ValueError("获取上传签名失败")

        # 2. 使用 PUT 方法上传文件到指定 URL
        file.seek(0)  # 确保从文件开头读取
        upload_response = self._client._client.put(
            upload_url,
            content=file.read(),
            headers={
                "Content-Type": content_type,
                "Content-Length": str(file_size),
            },
        )

        upload_response.raise_for_status()

        # 3. 返回文件对象
        file_obj = File(
            path=sign_data.get("path", ""),
            expire_time=sign_data.get("expireTime"),
            upload_url=upload_url,
            access_url=sign_data.get("accessUrl", ""),
            object_key=sign_data.get("objectKey", ""),
            name=filename,
            content_type=content_type,
            size=file_size,
        )

        return file_obj

    async def async_create(
        self,
        file: Union[str, pathlib.Path, BinaryIO, io.IOBase],
        **params: Unpack["Files.CreateFileParams"],
    ) -> File:
        """
        异步上传文件到 SpeedPix

        Args:
            file: 文件路径或文件对象
            **params: 可选参数

        Returns:
            File: 上传后的文件对象
        """
        if isinstance(file, (str, pathlib.Path)):
            file_path = pathlib.Path(file)
            params["filename"] = params.get("filename", file_path.name)
            with open(file_path, "rb") as f:
                return await self.async_create(f, **params)
        elif not isinstance(file, (io.IOBase, BinaryIO)):
            raise ValueError(
                "不支持的文件类型。必须是文件路径或文件对象。"
            )

        # 准备文件信息
        filename = params.get("filename", os.path.basename(getattr(file, "name", "file")))
        content_type = (
            params.get("content_type")
            or mimetypes.guess_type(filename)[0]
            or "application/octet-stream"
        )

        # 获取文件大小
        file.seek(0, 2)  # 移动到文件末尾
        file_size = file.tell()
        file.seek(0)  # 回到文件开头

        # 1. 调用 /scc/sp_create_temp_file_upload_sign 获取上传签名
        sign_response = await self._client._async_request(
            "POST",
            "/scc/sp_create_temp_file_upload_sign",
            json={
                "contentType": content_type,
                "originalFilename": filename,
            },
        )

        sign_data = sign_response.json().get("data", {})
        upload_url = sign_data.get("uploadUrl")

        if not upload_url:
            raise ValueError("获取上传签名失败")

        # 2. 使用 PUT 方法上传文件到指定 URL
        file.seek(0)  # 确保从文件开头读取
        upload_response = await self._client._async_client.put(
            upload_url,
            content=file.read(),
            headers={
                "Content-Type": content_type,
                "Content-Length": str(file_size),
            },
        )

        upload_response.raise_for_status()

        # 3. 返回文件对象
        file_obj = File(
            path=sign_data.get("path", ""),
            expire_time=sign_data.get("expireTime"),
            upload_url=upload_url,
            access_url=sign_data.get("accessUrl", ""),
            object_key=sign_data.get("objectKey", ""),
            name=filename,
            content_type=content_type,
            size=file_size,
        )

        return file_obj
