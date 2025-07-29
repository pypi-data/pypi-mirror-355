from mcp.server.fastmcp import FastMCP
mcpserver = FastMCP('gdmec23120455')
@mcpserver.tool()
def sayHello(name):
    """
    问候，打招呼，寒暄
    :params name: 对方的名字
    :return: 打招呼的回复   
    """
    return f'{name}你好，23120455余政煜很高兴认识你！'

def main():
    mcpserver.run(transport='stdio')


