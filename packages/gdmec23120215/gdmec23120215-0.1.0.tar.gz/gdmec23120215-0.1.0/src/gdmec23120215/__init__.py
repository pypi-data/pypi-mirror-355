from mcp.server.fastmcp import FastMCP
mcpserver = FastMCP('gdmec23120215')
@mcpserver.tool()
def sayhello(name):
    """
    打招呼,问候
    :param name:  对方名字
    :return: 问候语
    """
    return f'{name}你好，23120215蓝康表示欢迎你！'
def main():
    mcpserver.run(transport='stdio')

