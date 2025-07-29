# server.py
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Demo")


# Add an addition tool
# 注意凡是@tool修饰的, 说明llm调用它可能会改变输入的值
# 可以理解它不仅会获取内容, 还会修改内容
# 任何可能修改的内容都用@tool修饰
# mcp中的任何函数都要求使用注释它什么功能、参数类型、返回值类型, 这些是为了给llm看的
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Add a dynamic greeting resource
# 注意凡是@tresource修饰的, 说明llm调用它只会获取某种资源
# 可简单理解为是const变量, 它只会读取内容, 不会修改内容
# 任何只读取资源的使用@resource修饰
# mcp中的任何函数都要求使用注释它什么功能、参数类型、返回值类型, 这些是为了给llm看的
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


 # pypi-AgEIcHlwaS5vcmcCJDUyYWZlNTdhLTFhOGUtNDU4MS05OWNjLTk5MjNmMzgwNGEwMQACKlszLCI0ZDViN2IwOS01OGM2LTQ1MTItYjI0MC0wZGYxYWE5MTcxMjYiXQAABiCnqF05CwcEF4l7o-2-k7_5HUOOao5rgWYNJAsHPnCBqQ
def main() -> None:
    mcp.run(transport='stdio')    # 使用stdio协议, 因为用户是需要下载到本地使用的, 所以使用stdio协议
