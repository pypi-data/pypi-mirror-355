from mcp.server.fastmcp import fastMCP 
mcpserver = FastMCP('gdmec23120351')
@mcpserver.tool
def sayHello(name):
    """
    打招呼，问候，寒暄
    :param name:对方的名字
    :return:打招呼的回复
    """
    return f'{name}您好，23120351张仕增和高兴认识您'

def main():
    mcpserver.run(transport ='stfio')
