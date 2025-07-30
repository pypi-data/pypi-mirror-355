## 计算器 MCP
基于 Model Context Protocol (MCP) 的小红书笔记获取器，提供了笔记获取功能。


# Tools
```
{
  "tools": [
    {
      "name": "generate_xiaohongshu_notes",
      "description": "获取小红书笔记",
      "inputSchema": {
        "type": "object",
        "properties": {
            "text":"美妆"
          }
        }
```

## MCP 服务器配置
```
[
  {
    "mcpServers": {
        "calculator": {
        "command": "uvx",
        "args": [
            "mcp-calculator-kel@latest"
            ]
        }
    }
  }
]
```