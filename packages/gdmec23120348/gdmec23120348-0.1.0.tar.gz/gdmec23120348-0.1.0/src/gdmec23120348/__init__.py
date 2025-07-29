from mcp.server.fastmcp import FastMCP
mcpserver = FastMCP('gdmec23120348')
@mcpserver.tool()
def syaHello(name):
    """
    打招呼，问候，寒暄
    :param name: 对方名字
    :return: 打招呼的回复
    """
    return f'{name}您好，23120348詹丹虹很高兴认识您。'
def main():
    mcpserver.run(transport='stdio')

