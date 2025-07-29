from mcp.server.fastmcp import FastMCP
mcpserver = FastMCP('gdmec23120145')
@mcpserver.tool()
def sayHello(name):
    """
    问候，打招呼，寒暄
    :params name:对方的姓名
    :return:问候语
    """
    return f'{name}您好，23120145文政灏很高兴欢迎您！'
def main():
    mcpserver.run(transport='stdio')
