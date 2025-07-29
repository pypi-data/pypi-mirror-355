from mcp.server.fastmcp import FastMCP
mcpserver = FastMCP('gdmec23120143')

@mcpserver.tool()
def sayHello(name):
    """
    打招呼，温厚，寒暄
    :param name: 对方的名字
    :return: 问候语
    """
    return f'{name}您好，23120143王沛权，表示欢迎您！'
def main():
    mcpserver.run(transport='stdio')