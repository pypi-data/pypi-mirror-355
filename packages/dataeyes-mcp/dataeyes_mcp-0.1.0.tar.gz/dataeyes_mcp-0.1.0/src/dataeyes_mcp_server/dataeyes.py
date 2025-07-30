from mcp.server.fastmcp import FastMCP
import os
from mcp.types import Tool, TextContent
import httpx

# 创建MCP服务器实例
mcp = FastMCP(
    name="mcp-server-dataeyes",
    version="0.1.0",
    instructions="This is a MCP server for Dataeyes."
)


"""

获取环境变量中的 API 密钥, 用于调用数眼智能 API
环境变量名为: DATAEYES_API_KEY
获取方式请参考: 

"""

api_key = os.getenv('DATAEYES_API_KEY')
api_url = "https://api.shuyanai.com"



async def reader(url: str, timeout: int) -> TextContent:
    
    """
    网页阅读器, 用于阅读网页内容。
    """
    try:
        reader_url = f"{api_url}/v1/reader"

        # 参数设置
        params = {
            "url": url,
            "timeout": timeout,
        }

        # 请求头设置
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(reader_url, params=params, headers=headers)
            response.raise_for_status()
            result = response.json()

        if result.get("status") != 0 :
            error_msg = result.get("message", "unknown error")
            raise Exception(f"API response error: {error_msg}")

        return TextContent(type="text", text=response.text)
    
    except httpx.HTTPError as e:
        raise Exception(f"HTTP request failed: {str(e)}") from e
    

async def list_tools() -> list[Tool]:
    """
    列出所有可用的工具。

    Args:
        None.

    Returns:
        list (Tool): 包含了所有可用的工具, 每个工具都包含了名称、描述、输入 schema 三个属性.
    """
    return [
        Tool(
            name="reader",
            description="读取网页内容并返回大模型友好的 Markdown 格式",
            inputSchema={
                "type": "object",
                "required": ["url"],
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "要读取的网页链接",
                    },
                    "timeout": {
                        "type": "number",
                        "description": "页面加载超时时间，单位为秒（1-60）",

                    }
                }
            }
        )

    ]

async def dispatch(name: str, arguments: dict) -> TextContent | None:
    """
    根据名称调度对应的工具函数, 并返回处理结果.

    Args:
        name (str): 工具函数的名称, 可选值为: "reader".
        arguments (dict): 传递给工具函数的参数字典, 包括必要和可选参数.

    Returns:
        types.TextContent: 返回包含网页内容的 Markdown 格式.

    Raises:
        ValueError: 如果提供了未知的工具名称.
    """
    match name:
        case "reader":
            return await reader(arguments.get("url"), arguments.get("timeout", 30))
        case _:
            raise ValueError(f"Unknown tool: {name}")

mcp._mcp_server.list_tools()(list_tools)
mcp._mcp_server.call_tool()(dispatch)

if __name__ == "__main__":
    mcp.run()