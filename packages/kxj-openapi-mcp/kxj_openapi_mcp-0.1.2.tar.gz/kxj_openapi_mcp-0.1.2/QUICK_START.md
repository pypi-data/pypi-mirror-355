# 🚀 MCP OpenAPI Generator 快速开始

## 步骤1: 安装配置

### 安装依赖
```bash
cd openapi-mcp
pip install -r requirements.txt
```

### 配置MCP
编辑 `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "openapi-generator": {
      "command": "python3",
      "args": ["/Users/yfy/Desktop/project/mcp-api/openapi-mcp/server.py"],
      "env": {
        "MCP_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## 步骤2: 测试连接

重启Cursor，然后尝试：
```bash
test_connection
```

## 步骤3: 分析控制器（SAPI功能）

### 分析整个控制器
```bash
sapi pid:5 @ExampleController.php
```

### 分析特定方法
```bash
sapi pid:5 @ExampleController.php actionDetail
```

## 步骤4: 下载文档（DAPI功能）

### 下载项目文档
```bash
dapi pid:5
```

### 下载特定接口文档
```bash
dapi eid:19
```

## 完整示例工作流

### 场景: 分析和下载接口文档

1. **分析控制器生成文档**
   ```bash
   sapi pid:5 @RegisterController.php actionCreate
   ```
   
2. **上传成功后，下载查看**
   ```bash
   dapi pid:5
   ```
   
3. **让AI分析下载的内容**
   复制返回结果中的 `downloaded_content`，请AI分析：
   ```
   请分析以下OpenAPI文档内容，生成易读的接口文档说明：
   [粘贴内容]
   ```

## 快速测试

运行测试脚本验证功能：
```bash
cd openapi-mcp
python3 test_mcp.py      # 测试SAPI功能
python3 test_dapi.py     # 测试DAPI功能  
python3 diagnose_mcp.py  # 诊断连接问题
```

## 常见问题

### Q: MCP连接失败？
A: 
1. 检查路径是否正确
2. 确保Python环境正常
3. 运行 `python3 diagnose_mcp.py`

### Q: API密钥错误？
A: 
1. 检查MCP配置中的 `MCP_API_KEY`
2. 确认密钥有效性
3. 联系管理员获取正确密钥

### Q: 文件找不到？  
A:
1. 使用相对路径或完整路径
2. 确保文件存在且可访问
3. 检查文件格式是否正确

---

🎉 现在你可以开始使用 MCP OpenAPI Generator 了！ 