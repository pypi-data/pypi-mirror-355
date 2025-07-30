# _init_.py
from mcp.server.fastmcp import FastMCP
# 创建一个MCP服务器
server = FastMCP("demo_mcp_server")

@server.tool()
def add(a:int,b:int)->int:
    #add two numbers
    return a+b
@server.tool()
def mul(a:int,b:int)->int:
    #multiply two numbers
    return a*b

@server.tool()
def sub(a:int,b:int)->int:
    #subtract two numbers
    return a-b

