import argparse
from .server import mcp

def main():
    """MCP 小红书"""
    parser = argparse.ArgumentParser(
        description="""MCP 小红书
        一个基于小红书的 MCP 插件，支持小红书账号登录，自动获取账号下的文章，支持自定义文章筛选条件，支持自定义 Markdown 模板，支持自定义输出目录。
        """
    )
    parser.parse_args()
    mcp.run()

if __name__ == "__main__":
    main()
