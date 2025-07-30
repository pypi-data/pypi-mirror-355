# SpeedPix Python SDK

智作工坊 SpeedPix Python SDK，提供简洁易用的 API 接口，专注于 AI 图像生成和处理工作流。

## 📚 关于智作工坊

智作工坊（AIGC Service Lab）是阿里云教育推出的 AIGC 生成服务，主要为泛教育、设计业务企业提供高效的 AIGC（人工智能生成内容）PAAS 服务。

### 🎯 核心功能
- **文生图**：根据文本描述生成高质量图像
- **图生图**：基于输入图像进行风格转换或内容变换
- **文转视频**：将文本描述转换为动态视频内容
- **图转视频**：将静态图像转换为动态视频

### 🔧 技术支持
- 支持**通义万相**以及开源的 **Stable Diffusion** 模型
- 提供 **WEB UI** 和 **ComfyUI** 两种模式
- 集成阿里云严格的**内容安全检测服务**
- 支持自定义界面部署和权限管理

### 📖 详细文档
- [智作工坊产品文档](https://help.aliyun.com/document_detail/2804197.html)
- [产品概述](https://help.aliyun.com/document_detail/2804199.html)
- [智作工坊控制台](https://eduplatform-sp.console.aliyun.com/)

---

## 特性

- 🚀 **简洁易用** - 直观的 API 设计，开箱即用
- 🔄 **异步支持** - 完整的同步和异步操作支持
- 📁 **智能文件处理** - 自动检测、上传和转换文件输入
- 🛡️ **类型安全** - 完整的类型注解支持，更好的开发体验
- ⚡ **高性能** - 基于 httpx 的现代 HTTP 客户端
- 🔧 **代码规范** - 遵循 Python 最佳编码实践
- 🎯 **一键运行** - `run()` 方法直接获取结果
- 📎 **多文件格式** - 支持路径、Path 对象、文件流等多种输入
- 🔐 **灵活编码** - base64 和 URL 两种文件编码策略
- 🌐 **智能输出** - URL 自动转换为可操作的 FileOutput 对象

## 安装

使用 pip 安装：

```bash
pip install speedpix
```

或使用 uv（推荐）：

```bash
uv add speedpix
```

## 目录

- [5 分钟快速上手](#5-分钟快速上手)
- [详细使用方法](#详细使用方法)
- [文件处理](#文件处理)
- [异步支持](#异步支持)
- [错误处理](#错误处理)
- [环境变量](#环境变量)
- [常见问题 FAQ](#常见问题-faq)
- [API 参考](#api-参考)
- [示例](#示例)

## 5 分钟快速上手

### 最简单的开始方式

```python
import os
from speedpix import Client

from speedpix import Client

# 方法 1：最简方式（推荐）- 仅需提供必需参数
client = Client(
    app_key="your-app-key",
    app_secret="your-app-secret"
    # endpoint 可选，默认为 https://openai.edu-aliyun.com
)

# 方法 2：从环境变量读取（传统方式）
client = Client(
    endpoint=os.getenv("SPEEDPIX_ENDPOINT"),  # 可选
    app_key=os.getenv("SPEEDPIX_APP_KEY"),
    app_secret=os.getenv("SPEEDPIX_APP_SECRET")
)

# 方法 3：混合方式
client = Client(
    app_key="your-app-key",  # 直接提供
    app_secret=os.getenv("SPEEDPIX_APP_SECRET"),  # 从环境变量读取
    endpoint="https://custom-endpoint.com"  # 自定义endpoint
)

# 2. 运行 AI 工作流
try:
    output = client.run(
        workflow_id="your-workflow-id",
        input={"prompt": "一幅美丽的山水画"}
        # alias_id 默认为 "main"，可选指定其他别名
    )

    # 3. 保存结果
    output['images']['url'].save("result.png")
    print("图片已保存为 result.png")
except Exception as e:
    print(f"处理失败: {e}")
```

就这么简单！🎉

## 详细使用方法

### 客户端创建方式

SpeedPix Python SDK 提供灵活的客户端创建方式：

```python
# 方式 1：最简单（推荐）
client = Client("your-app-key", "your-app-secret")

# 方式 2：指定所有参数
client = Client(
    endpoint="https://custom-endpoint.com",  # 可选，默认为 https://openai.edu-aliyun.com
    app_key="your-app-key",
    app_secret="your-app-secret",
    timeout=60.0  # 可选，默认30秒
)

# 方式 3：混合环境变量和直接参数
client = Client(
    app_key=os.getenv("SPEEDPIX_APP_KEY"),
    app_secret="your-app-secret"  # 可以混合使用
)
```

### 方法 1：直接运行（推荐新手）

最简单直接的使用方式：

```python
import os
from speedpix import Client

# 初始化客户端（推荐：最简方式）
client = Client("your-app-key", "your-app-secret")

# 直接运行并获取结果
output = client.run(
    workflow_id="your-workflow-id",
    input={"prompt": "A beautiful landscape painting"}
    # alias_id 默认为 "main"，可选指定其他别名
)

# 处理输出
if 'images' in output and hasattr(output['images'], 'save'):
    output['images'].save("result.png")
    print("图片已保存为 result.png")

print(f"Complete result: {output}")
```

### 方法 2：全局函数（更简洁）

```python
import speedpix

# 使用自定义客户端
client = speedpix.Client()  # 自动从环境变量读取配置

# 全局 run 函数
output = speedpix.run(
    workflow_id="your-workflow-id",
    input={"prompt": "A magical forest"},
    client=client
)

# 或者直接使用（需要设置环境变量）
output = speedpix.run(
    workflow_id="your-workflow-id",
    input={"prompt": "A magical forest"}
)
```

### 方法 3：后台处理

不等待完成，先启动任务：

```python
import os
from speedpix import Client

client = Client()  # 自动从环境变量读取配置

try:
    # 启动任务但不等待
    prediction = client.run(
        workflow_id="your-workflow-id",
        input={"prompt": "A cyberpunk cityscape"},
        wait=False  # 不等待完成
    )

    print(f"Task started: {prediction.id}")

    # 做其他事情...

    # 稍后检查并等待完成
    prediction = prediction.wait()
    prediction.output['images']['url'].save("result.png")
except Exception as e:
    print(f"后台处理失败: {e}")
```

### 方法 4：传统预测接口

```python
from speedpix import Client

client = Client()  # 自动从环境变量读取配置

# 创建预测任务
try:
    prediction = client.predictions.create(
        workflow_id="your-workflow-id",
        input={"prompt": "A beautiful sunset"}
        # alias_id 默认为 "main"，可选指定其他别名
    )

    # 等待完成
    prediction = prediction.wait()

    # 检查结果
    if prediction.error:
        print(f"Error: {prediction.error}")
    else:
        print("Success!")
        prediction.output['images']['url'].save("result.png")
except Exception as e:
    print(f"预测处理失败: {e}")
```

## 文件处理

SpeedPix SDK 提供强大的文件处理功能，支持自动上传和智能输入处理：

### 自动文件上传

SDK 会自动检测输入中的文件对象并上传：

```python
from pathlib import Path
import speedpix

client = speedpix.Client()  # 自动从环境变量读取配置

# 支持多种文件输入类型
output = client.run(
    workflow_id="your-workflow-id",
    input={
        "image": "path/to/image.jpg",           # 文件路径字符串
        "reference": Path("reference.png"),     # pathlib.Path 对象
        "mask": open("mask.jpg", "rb"),         # 文件对象
        "prompt": "编辑这张图片"
    }
)
```

### 文件编码策略

支持两种文件编码策略：

```python
client = Client()  # 自动从环境变量读取配置

# URL 策略（默认）- 上传文件到服务器
output = client.run(
    workflow_id="your-workflow-id",
    input={"image": "large_image.jpg"},
    file_encoding_strategy="url"  # 适合大文件
)

# Base64 策略 - 直接编码到请求中
output = client.run(
    workflow_id="your-workflow-id",
    input={"thumbnail": "small_icon.png"},
    file_encoding_strategy="base64"  # 适合小文件(<1MB)
)
```

### 手动文件上传

也可以手动上传文件：

```python
client = Client()  # 自动从环境变量读取配置

# 上传文件
file_obj = client.files.create("path/to/image.jpg")
print(f"文件已上传: {file_obj.access_url}")

# 在推理中使用
output = client.run(
    workflow_id="your-workflow-id",
    input={
        "image": file_obj.access_url,
        "prompt": "处理这张图片"
    }
)
```

## 异步支持

所有方法都有对应的异步版本：

```python
import asyncio
from speedpix import Client

async def main():
    client = Client()  # 自动从环境变量读取配置

    try:
        # 异步 run
        output = await client.async_run(
            workflow_id="your-workflow-id",
            input={"prompt": "An async generated image"}
        )

        # 保存结果
        await output['images']['url'].async_save("async_result.png")

        # 并发运行多个任务
        tasks = [
            client.async_run(
                workflow_id="your-workflow-id",
                input={"prompt": f"Image {i}"}
            )
            for i in range(3)
        ]

        results = await asyncio.gather(*tasks)

        # 并发保存结果
        save_tasks = [
            result['images']['url'].async_save(f"async_result_{i}.png")
            for i, result in enumerate(results)
        ]
        await asyncio.gather(*save_tasks)
    except Exception as e:
        print(f"异步处理失败: {e}")

# 运行异步函数
asyncio.run(main())
```

## 错误处理

```python
from speedpix import Client, PredictionError

client = Client()  # 自动从环境变量读取配置

try:
    output = client.run(
        workflow_id="your-workflow-id",
        input={"prompt": "Test image"}
    )

except PredictionError as e:
    print(f"Model execution failed: {e}")
    if e.prediction:
        print(f"Prediction ID: {e.prediction.id}")
        print(f"Error details: {e.prediction.error}")

except Exception as e:
    print(f"Other error: {e}")
```

## 环境变量

**重要：请务必通过环境变量设置API凭据，不要在代码中硬编码！**

设置以下环境变量：

```bash
# Linux/macOS
export SPEEDPIX_ENDPOINT="your-endpoint.com"  # 可选，默认为 https://openai.edu-aliyun.com
export SPEEDPIX_APP_KEY="your-app-key"        # 必需
export SPEEDPIX_APP_SECRET="your-app-secret"  # 必需

# Windows
set SPEEDPIX_ENDPOINT=your-endpoint.com  # 可选，默认为 https://openai.edu-aliyun.com
set SPEEDPIX_APP_KEY=your-app-key        # 必需
set SPEEDPIX_APP_SECRET=your-app-secret  # 必需
```

或者创建 `.env` 文件：

```env
SPEEDPIX_ENDPOINT=your-endpoint.com  # 可选，默认为 https://openai.edu-aliyun.com
SPEEDPIX_APP_KEY=your-app-key        # 必需
SPEEDPIX_APP_SECRET=your-app-secret  # 必需
```

然后使用 `python-dotenv` 加载：

```python
from dotenv import load_dotenv
from speedpix import Client

load_dotenv()  # 加载 .env 文件

client = Client()  # 自动从环境变量读取配置
```

设置后可以直接创建客户端：

```python
from speedpix import Client

# 自动从环境变量读取配置
client = Client()
```

## 常见问题 FAQ

### Q: 如何获取 SpeedPix 的 API 凭据？
A: 请联系智作工坊获取您的 `endpoint`、`app_key` 和 `app_secret`。

### Q: 支持哪些文件格式？
A: 支持常见的图片格式（jpg、png、webp 等）和其他文件类型。SDK 会自动检测文件类型。

### Q: 文件大小有限制吗？
A:
- 使用 `base64` 编码策略时，文件大小限制为 1MB
- 使用 `url` 编码策略时（默认），没有大小限制

### Q: 如何处理长时间运行的任务？
A: 使用 `wait=False` 参数启动后台任务，然后用 `prediction.wait()` 等待完成：

```python
# 启动后台任务
prediction = client.run(workflow_id="...", input={...}, wait=False)

# 稍后等待完成
result = prediction.wait()
```

### Q: 如何同时运行多个任务？
A: 使用异步 API 可以轻松并发运行：

```python
import asyncio

async def run_multiple():
    tasks = [
        client.async_run(workflow_id="...", input={"prompt": f"Image {i}"})
        for i in range(5)
    ]
    results = await asyncio.gather(*tasks)
    return results
```

## 示例

查看 [examples/](examples/) 目录中的完整示例：

- [`examples/basic_usage.py`](examples/basic_usage.py) - 基础使用示例
- [`examples/api_usage_demo.py`](examples/api_usage_demo.py) - API 使用演示
- [`examples/file_upload_demo.py`](examples/file_upload_demo.py) - 文件上传示例
- [`examples/advanced_input_handling.py`](examples/advanced_input_handling.py) - 高级输入处理示例
- [`examples/error_handling_demo.py`](examples/error_handling_demo.py) - 错误处理示例
- [`examples/async_save_demo.py`](examples/async_save_demo.py) - 异步保存功能示例

## API 参考

### Client

主要客户端类，提供所有 API 访问功能。

#### 构造函数

```python
Client(
    endpoint: str = None,
    app_key: str = None,
    app_secret: str = None,
    timeout: float = 30.0,
    user_agent: str = None
)
```

#### 方法

- `run(workflow_id, input, **kwargs)` - 直接运行模型（推荐）
- `async_run(workflow_id, input, **kwargs)` - 异步运行模型
- `predictions.create(workflow_id, input, **kwargs)` - 创建预测任务
- `predictions.get(prediction_id)` - 获取预测状态
- `files.create(file)` - 上传文件
- `files.async_create(file)` - 异步上传文件

### FileOutput

文件输出处理类，提供方便的文件操作。

#### 属性

- `url` - 文件访问 URL

#### 方法

- `read()` - 读取文件内容（bytes）
- `save(path)` - 保存文件到本地路径
- `async_read()` - 异步读取文件内容（bytes）
- `async_save(path)` - 异步保存文件到本地路径

### File

文件上传对象，表示已上传的文件。

#### 属性

- `access_url` - 文件访问 URL
- `name` - 文件名
- `content_type` - 文件 MIME 类型
- `size` - 文件大小（字节）

### 主要函数

- `speedpix.run(workflow_id, input, client=None, **kwargs)` - 全局运行函数
- `speedpix.async_run(workflow_id, input, client=None, **kwargs)` - 全局异步运行函数

## 开发

```bash
# 克隆仓库
git clone <repository-url>
cd speed-pix-python

# 安装依赖
uv sync

# 运行测试
uv run python -m pytest test_basic.py -v

# 快速功能验证
uv run python -c "
import speedpix
from speedpix import Client, run
client = Client(endpoint='test', app_key='test', app_secret='test')
print('✓ 所有功能正常')
"

# 代码格式化
uv run ruff format

# 代码检查
uv run ruff check speedpix/
```

## 获取帮助

如果您在使用过程中遇到问题：

1. **查看示例** - 先查看 [examples/](examples/) 目录中的示例代码
2. **查看文档** - 阅读 [docs/](docs/) 目录中的详细文档
3. **检查类型提示** - SDK 提供完整的类型注解，IDE 会给出很好的提示
4. **联系支持** - 如需技术支持，请联系智作工坊团队

## 测试状态

✅ **核心功能**
- 客户端初始化和配置
- HTTP 请求处理和错误处理
- 预测状态管理和轮询

✅ **简洁 API**
- `client.run()` 和 `client.async_run()` 方法
- `speedpix.run()` 和 `speedpix.async_run()` 全局函数
- `wait=False` 支持后台处理

✅ **异常处理**
- PredictionError 用于模型执行失败
- SpeedPixException 用于 API 错误
- 完整的错误传播链

✅ **文件处理**
- FileOutput 类支持 `.save()` 和 `.read()` 方法
- 自动内容缓存和懒加载
- 多种输出格式支持

✅ **代码质量**
- 完整的类型注解覆盖
- Ruff 格式标准合规
- Python 最佳实践遵循

## 许可证

MIT License
