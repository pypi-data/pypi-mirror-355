from mcp.server.fastmcp import FastMCP  
mcpserver=FastMCP('gdmec23120346')

@mcpserver.tool()

def sayHello(name):
    """
    问候，打招呼，寒暄
    :params name:对方的名字 
    :return:打招呼的回复
    """
    return f'{name}你好，23120346余杨很高兴认识您！'

def main():
    mcpserver.run(transport='stdio')
    
