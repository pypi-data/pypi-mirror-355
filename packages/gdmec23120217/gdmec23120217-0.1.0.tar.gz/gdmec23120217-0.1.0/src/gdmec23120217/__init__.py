from mcp.server.fastmcp import FastMCP
mcpserver = FastMCP('gdmec23120199')
# 解释代码 | 代码修复 | 生成文档 | 生成测试 | 代码评审 | 关闭

@mcpserver.tool()
# 解释代码 | 代码修复 | 生成文档 | 生成测试 | 代码评审 | 关闭
def sayHello(name):
    """
    打招呼，问候，寒暄
    :param name: 对方的姓名
    :return: 打招呼的回复
    """
    return f'{name}您好，23120217李嘉健很高兴认识您。'

# 解释代码 | 代码修复 | 生成文档 | 生成测试 | 代码评审 | 关闭
def main():
    mcpserver.run(transport='stdio')