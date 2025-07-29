from mcp.server.fastmcp import FastMCP
mcpserver = FastMCP('gdmec23120316')
@mcpserver.tool()
def sayHello(name):
    """
    问候，打招呼，寒暄
    :param name:对方的名字
    :return:打招呼的回复
    """
    return f'{name}您好，gdmec23120316黄子恒很高兴认识您'

def main():
    mcpserver.run(transport='stdio')
