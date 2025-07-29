from mcp.server.fastmcp import FastMCP
mcpserver = FastMCP('gdmec23120125')
@mcpserver.tool()
def sayHello(name):
    """
    打招呼，问候，寒暄
    :param name:对方的姓名
    :return:打招呼的回复
    """
    return f'{name}您好,23120125李思日表示很欢迎您!'