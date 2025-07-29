from mcp.server.fastmcp import FastMCP 
mcpserver = FastMCP('gdmec23120233')
@mcpserver.tool()
def sayHello(name):
    """
    问候，打招呼，寒暄
    :params name:对方的姓名
    :return:打招呼的回复
    """
    return f'{name}您好,gdmec23120233蒙雪梅，表示十分的欢迎您！'
def main():
    mcpserver.run(transport='stdio')

if __name__ == '__main__':  
    main()