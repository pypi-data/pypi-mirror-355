# server.py
import requests
import os
from typing import Optional
from mcp.server.fastmcp import FastMCP

# 创建MCP服务器
mcp = FastMCP("ImageUpload")


@mcp.tool()
def upload_image(file_path: str, auth_code: str = "luoshui") -> str:
    """
    上传本地图片到图床
    
    Args:
        file_path: 本地图片文件路径
        auth_code: 认证码，默认为"luoshui"
    
    Returns:
        完整的图片链接URL
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return f"错误：文件不存在 - {file_path}"
    
    # 检查文件是否为图片格式
    valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
    file_extension = os.path.splitext(file_path)[1].lower()
    if file_extension not in valid_extensions:
        return f"错误：不支持的文件格式 - {file_extension}"
    
    try:
        # 构建上传URL
        url = f"https://imgbed.deepseeking.app/upload?authCode={auth_code}"
        
        # 获取文件名
        filename = os.path.basename(file_path)
        
        # 根据文件扩展名确定MIME类型
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(file_extension, 'image/png')
        
        # 准备文件上传
        with open(file_path, 'rb') as file:
            files = [
                ('file', (filename, file, mime_type))
            ]
            payload = {}
            headers = {}
            
            # 发送POST请求
            response = requests.post(url, headers=headers, data=payload, files=files)
            
            # 检查响应状态
            if response.status_code == 200:
                # 解析响应JSON
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    # 获取相对路径
                    relative_path = result[0].get('src', '')
                    if relative_path:
                        # 拼接完整URL
                        full_url = f"https://imgbed.deepseeking.app{relative_path}"
                        return full_url
                    else:
                        return "错误：响应中未找到图片路径"
                else:
                    return f"错误：响应格式异常 - {result}"
            else:
                return f"错误：上传失败，状态码 {response.status_code} - {response.text}"
                
    except requests.exceptions.RequestException as e:
        return f"错误：网络请求失败 - {str(e)}"
    except FileNotFoundError:
        return f"错误：文件未找到 - {file_path}"
    except Exception as e:
        return f"错误：上传过程中发生异常 - {str(e)}"


@mcp.tool()
def get_supported_formats() -> str:
    """
    获取支持的图片格式列表
    
    Returns:
        支持的图片格式字符串
    """
    formats = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
    return f"支持的图片格式：{', '.join(formats)}"


def main() -> None:
    """启动MCP服务器"""
    mcp.run(transport="stdio")
