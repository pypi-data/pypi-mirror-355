from mcp.server.fastmcp import FastMCP
mcpserver = FastMCP('gdmec23120224')
@mcpserver.tool()
def sayHello(name):
    """
    打招呼，问候，寒暄
    :param name:对方的名字
    :return:打招呼回复
    """
    return f'{name}您好,23120224刘承通很高兴认识你。'
def main():
    mcpserver.run(transport='stdio')

    
