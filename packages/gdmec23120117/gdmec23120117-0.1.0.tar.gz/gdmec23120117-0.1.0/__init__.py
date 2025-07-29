from mcp.server.fastmcp import FastMCP
mcpserver = FastMCP('gdmec23120117')
@mcpserver.tool()
def sayHello(name):
    """
    问候,打招呼，寒暄
    :params name:对方的姓名
    :return:问候语
    """
    return f'{name}你好,23120117黄明洛,表示很欢迎你。'

def main():
    mcpserver.run(transport='stdio')