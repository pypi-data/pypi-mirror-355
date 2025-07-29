# MCP OpenAPI Generator 配置指南

## 📋 概述

MCP OpenAPI Generator 采用标准的 MCP 配置方式，通过环境变量管理 API Key，符合 Model Context Protocol 的最佳实践。

## 🔧 标准MCP配置

### 在 Cursor 的 mcp.json 中配置

编辑 Cursor 设置中的 `mcp.json` 文件：

```json
{
  "mcpServers": {
    "openapi-generator": {
      "command": "/Users/yfy/Desktop/project/mcp-api/openapi-mcp/start_mcp_server.sh",
      "args": [],
      "env": {
        "MCP_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### 环境变量优先级

系统会按以下优先级查找 API Key：

1. **MCP_API_KEY** (推荐)
   - 标准 MCP 配置变量
   - 在 mcp.json 的 env 字段中设置

2. **OPENAPI_MCP_KEY** (项目特定)
   - 项目特定的配置变量
   - 可用于多项目环境

3. **MCP_KEY** (简化)
   - 简化版本的配置变量
   - 便于快速配置

## 🚀 配置步骤

### 1. 获取 API Key
联系 API 提供方获取您的专用 API Key。

### 2. 配置环境变量

**方法一：通过 Cursor mcp.json (推荐)**
```json
{
  "mcpServers": {
    "openapi-generator": {
      "command": "/path/to/start_mcp_server.sh",
      "args": [],
      "env": {
        "MCP_API_KEY": "8448f6108eea94832f952797a2a09693d842985b84a7ededb09fa06905"
      }
    }
  }
}
```

**方法二：系统环境变量**
```bash
# macOS/Linux
export MCP_API_KEY="your_api_key_here"

# Windows
set MCP_API_KEY=your_api_key_here
```

### 3. 重启 Cursor
配置完成后，重启 Cursor 使配置生效。

### 4. 验证配置

```bash
# 检查配置状态
show config
```

成功配置后应显示：
```
✅ 配置状态: 已配置
🔑 当前Key: 已设置
🌍 配置方式: 环境变量 (标准MCP配置)
```

## 🔍 配置检查命令

### 查看配置状态
```bash
show config
```

**功能**：
- 显示环境变量配置状态
- 检查 API Key 是否正确设置
- 提供配置指导和故障排除信息

## 🛡️ 安全最佳实践

### 1. 保护 API Key
- ❌ 不要在代码中硬编码 API Key
- ❌ 不要提交包含 Key 的配置文件到版本控制
- ✅ 使用环境变量管理敏感信息
- ✅ 定期轮换 API Key

### 2. 配置管理
- 在 mcp.json 中设置环境变量
- 使用 Key 预览功能检查配置
- 保持配置文件的备份

## 🌍 多环境配置

### 开发环境
```json
{
  "env": {
    "MCP_API_KEY": "dev_api_key_here",
    "MCP_DEBUG": "true"
  }
}
```

### 生产环境
```json
{
  "env": {
    "MCP_API_KEY": "prod_api_key_here",
    "OPENAPI_BASE_URL": "https://api.production.com"
  }
}
```

## ❗ 故障排除

### Q: 提示 "未配置 MCP Key"
**解决方案**：
1. 检查 mcp.json 中的 env 配置
2. 确认 API Key 拼写正确
3. 重启 Cursor
4. 使用 `show config` 检查状态

### Q: 配置后仍然无法工作
**检查清单**：
- [ ] 环境变量名称正确 (MCP_API_KEY)
- [ ] API Key 有效且未过期
- [ ] mcp.json 语法正确
- [ ] 已重启 Cursor
- [ ] 服务器路径正确

### Q: 如何知道配置是否生效？
**验证方法**：
```bash
# 1. 检查配置状态
show config

# 2. 尝试使用功能
sapi pid:1 @TestController.php

# 3. 检查 MCP 连接日志
# 在 Cursor 设置中查看 MCP 日志
```

## 🎯 配置优势

✅ **标准兼容**: 符合 MCP 官方规范  
✅ **安全性高**: 环境变量隔离，不会泄露到代码中  
✅ **易于管理**: 集中在 mcp.json 中配置  
✅ **多环境支持**: 可为不同环境设置不同配置  
✅ **调试友好**: 提供详细的配置状态信息

## 🔗 相关资源

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [Cursor MCP 配置指南](https://cursor.com/docs/mcp)
- [环境变量最佳实践](https://12factor.net/config) 