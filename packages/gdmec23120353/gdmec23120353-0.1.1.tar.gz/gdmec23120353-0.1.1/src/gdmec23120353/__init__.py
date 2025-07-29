from mcp.server.fastmcp import FastMCP
mcpserver = FastMCP("gdmec23120353")
@mcpserver.tool()
def sayHello(name):
    """
    问候，打招呼，寒暄
    :params name: 对方的姓名
    :return: 问候语
    """
    return f'{name}您好，23120353郑世昱,表示很高兴认识您!'

def main():
    mcpserver.run(transport = 'stdio')
