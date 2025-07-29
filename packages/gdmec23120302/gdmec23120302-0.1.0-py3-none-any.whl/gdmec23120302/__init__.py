from mcp.server.fastmcp import FastMCP
mcpserver = FastMCP('gdmec23120302')
@mcpserver.tool()
def sayHello(name):
    """
    问候，打招呼，寒暄
    :param name:对方的姓名
    :return: 打招呼回复
    """
    return f'{name}你好，23120302蔡雯玉,表示很欢迎您!'
def main():
    mcpserver.run(transport='stdio')
