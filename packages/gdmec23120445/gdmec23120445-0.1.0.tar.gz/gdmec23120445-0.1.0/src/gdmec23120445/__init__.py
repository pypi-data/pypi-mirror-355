from mcp.server.fastmcp import FastMCP
mcpserver = FastMCP('gdmec23120445')

@mcpserver.tool()
def sayHello(name):
    """
    问候，打招呼，寒暄
    :param name: 对方的姓名
    :return: 打招呼的回复
    """
    return f'{name}您好,23120445吴晓扬很高兴认识您!'

def main():
    mcpserver.run(transport='stdio')