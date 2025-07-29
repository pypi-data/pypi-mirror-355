from mcp.server.fastmcp import FastMCP
mcpserver = FastMCP('gdmec21120421')
@mcpserver.tool()
def sayHello(name):
    """
    问候，打招呼，寒暄
    :params name:对方的名字
    :return:问招呼的回复
    """
    return f'{name}您好,21120421黄日赏,表示很欢迎您！'
def main():
    mcpserver.run(transport='stdio')