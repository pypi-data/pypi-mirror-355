from mcp.server.fastmcp import FastMCP
mcpserver = FastMCP('gdmec23120146')
@mcpserver.tool()
def sayHello(name):
    """
    打招呼，问候，寒暄
    :params name:对方的姓名
    :return:打招呼的回复
    """
    return f'{name}您好,23120146伍川很高兴认识您。'
def main():
    mcpserver.run(transport='stdio')