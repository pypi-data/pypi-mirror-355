from mcp.server.fastmcp import FastMCP
mcpserver = FastMCP('gdmec23120139')
@mcpserver.tool()
def sayHello(name):
    """  
    打招呼，问候，寒暄
    :param name: 对方的姓名
    :return: 问候语
    """
    return f'{name},你好,23120139潘宗榮欢迎你。'   
def main():
    mcpserver.run(transport= 'stdio')