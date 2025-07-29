from mcp.server.fastmcp import FastMCP
mcpserver = FastMCP('gdmec23120124')
@mcpserver.tool()
def sayHello(name):
    """
    问候，打招呼，寒暄
    :params name:对方的姓名
    :return:打招呼的回复
    """

    return f'{name}您好，23120124李明勋很高兴认识你.'

def main():
    mcpserver.run(transport='stdio')
    
