# kxj-openapi-mcp 快速安装指南

## 🚀 1. 安装
```bash
uv add kxj-openapi-mcp
uv add pyyaml httpx fastmcp
```

## ⚙️ 2. 配置Cursor
将以下内容添加到Cursor的MCP设置：
```json
{
  "mcpServers": {
    "kxj-openapi-mcp": {
      "command": "/path/to/your/.venv/bin/openapi-mcp",
      "args": [],
      "env": {
        "MCP_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## 🎯 3. 开始使用
在Cursor中：
```
请使用show_config工具显示当前MCP服务配置状态
```

## 📚 详细文档
查看 `kxj-openapi-mcp-使用指南.md` 获取完整使用说明。 