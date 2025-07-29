from mcp.server.fastmcp import FastMCP
mcpserver = FastMCP('gdmec23120445')

@mcpserver.tool()
def sayHello(name):
    """
    问候，打招呼，寒暄
    :param name: 对方的姓名
    :return: 打招呼的回复
    """
    return f'{name}hi,23120445吴晓扬 is glad to meet you!'

def main():
    mcpserver.run(transport='stdio')