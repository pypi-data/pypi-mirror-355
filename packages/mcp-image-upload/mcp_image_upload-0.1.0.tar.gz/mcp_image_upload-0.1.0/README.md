# MCP 图床上传服务器

这是一个基于MCP（Model Context Protocol）的图床上传服务器，支持将本地图片上传到图床并返回完整的图片链接。

## 功能特性

- 🖼️ 支持多种图片格式：PNG, JPG, JPEG, GIF, BMP, WEBP
- 🔗 自动生成完整的图片链接
- 🛡️ 文件存在性和格式验证
- 📝 详细的错误信息反馈
- 🔧 可配置的认证码

## 安装

```bash
# 克隆项目
git clone <repository-url>
cd mcp-image-upload

# 安装依赖
uv sync
```

## 使用方法

### 启动MCP服务器

```bash
python -m mcp_image_upload
```

### 可用工具

#### 1. upload_image
上传本地图片到图床

**参数：**
- `file_path` (str): 本地图片文件路径
- `auth_code` (str, 可选): 认证码，默认为"luoshui"

**返回：**
完整的图片链接URL

**示例：**
```python
# 上传图片
result = upload_image("/path/to/your/image.png")
# 返回: https://imgbed.deepseeking.app/file/1749965438804_image.png
```

#### 2. get_supported_formats
获取支持的图片格式列表

**返回：**
支持的图片格式字符串

## 错误处理

服务器会处理以下错误情况：
- 文件不存在
- 不支持的文件格式
- 网络请求失败
- 上传服务器错误
- 其他异常情况

## 技术栈

- Python 3.13+
- MCP (Model Context Protocol)
- requests
- FastMCP

## 开发

```bash
# 安装开发依赖
uv sync --dev

# 运行服务器
python -m mcp_image_upload
```
