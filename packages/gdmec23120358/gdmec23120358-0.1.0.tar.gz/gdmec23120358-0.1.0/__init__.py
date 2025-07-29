from fastmcp.client import Client
mcpserver = FastMCP('gdmec23120358')
@mcpserver.tool()
def sayHello(name):
    """
    问候，打招呼，寒暄
    :params name:对方的姓名
    :return:问候语
    """
    return f'{name}您好！23120358朱梓桐很高兴您！'

def main():
    mcpserver.run(transport='stdio')