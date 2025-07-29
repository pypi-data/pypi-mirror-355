# MCP OpenAPI Generator for Yii2

这是一个专为Yii2框架设计的MCP服务，能够智能分析Yii2控制器文件并生成标准的OpenAPI 3.0文档。支持自动上传、智能下载分析，并自动保存到用户项目目录。

## 🎯 核心功能

- **🔍 智能分析**: 利用AI深度分析Yii2控制器代码结构
- **📄 完整文档**: 生成包含详细入参出参的OpenAPI 3.0文档
- **📁 智能保存**: 自动保存到用户当前项目根目录
- **🔄 双向操作**: 支持上传分析结果和下载已有文档
- **🎯 灵活控制**: 支持分析整个控制器或指定单个action
- **📊 格式化输出**: 自动生成易读的Markdown文档
- **🛡️ 质量保证**: 严格的文档验证机制确保生成文档可正常预览

## 📦 安装配置

### 1. 环境要求
- Python 3.7+
- FastMCP框架

### 2. 配置Cursor MCP

在Cursor的设置中，找到MCP配置文件（通常在 `~/.cursor/mcp.json`），添加以下配置：

```json
{
  "mcpServers": {
    "openapi-generator": {
      "command": "/Users/yfy/Desktop/project/mcp-api/openapi-mcp/start_mcp_server.sh",
      "args": [],
      "env": {
        "MCP_API_KEY": "your-actual-api-key-here"
      }
    }
  }
}
```

**重要**: 请将路径和 `MCP_API_KEY` 替换为你的实际值。

## 🛠️ 可用工具命令

### 1. 📤 SAPI - 分析上传工具

**语法**: `sapi pid:<ID> @<控制器文件> [action方法名]`

```bash
# 分析整个控制器的所有接口
sapi pid:5 @RegisterController

# 分析指定的单个action  
sapi pid:5 @RegisterController actionCreate

# 使用简化语法
sapi pid:5 @HealthController
```

**功能**：
- 智能解析Yii2控制器代码
- 自动生成OpenAPI 3.0文档
- 上传到指定项目

### 2. 📥 DAPI - 智能下载工具

**语法**: `dapi pid:<ID>` 或 `dapi eid:<ID>`

```bash
# 下载整个项目的API文档
dapi pid:5

# 下载特定接口的文档
dapi eid:24
```

**功能**：
- 下载原始OpenAPI文档
- 智能分析和格式化
- 自动保存3个文件到用户项目目录：
  - `downloaded_<type>_<id>_openapi.json` - 原始OpenAPI文档
  - `analyzed_<type>_<id>_documentation.md` - 格式化Markdown文档
  - `analysis_<type>_<id>_result.json` - 完整分析结果

### 3. 📤 上传文档工具

**语法**: `upload_openapi_doc_tool pid:<ID> openapi_yaml:<YAML内容>`

```bash
# 直接上传OpenAPI YAML文档
upload_openapi_doc_tool pid:5 openapi_yaml:"..."
```

**质量保证**：
- 🔍 **YAML语法验证** - 确保文档格式正确
- 📋 **结构完整性检查** - 验证包含所有必需节点
- 🔗 **引用完整性验证** - 检查所有$ref引用都有对应定义
- ✅ **预览兼容性** - 确保可在Swagger Editor中正常显示
- ⚠️ **警告提示** - 对不影响功能的问题给出建议

### 4. ⚙️ 配置管理

#### 标准MCP配置 (推荐)

在Cursor的 `mcp.json` 文件中配置环境变量：

```json
{
  "mcpServers": {
    "openapi-generator": {
      "command": "/path/to/openapi-mcp/start_mcp_server.sh",
      "args": [],
      "env": {
        "MCP_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

#### 环境变量优先级

服务会按以下优先级读取API密钥：
1. `MCP_API_KEY` (推荐，标准MCP配置)
2. `OPENAPI_MCP_KEY` (项目特定配置)
3. `MCP_KEY` (简化配置)

#### 配置检查

```bash
# 显示当前配置状态
show_config
```

## 🎯 智能目录检测

DAPI工具会智能检测用户的工作目录，按以下优先级保存文件：

1. **项目根目录** - 自动识别包含以下文件的目录：
   - `.git` (Git仓库)
   - `package.json` (Node.js项目)
   - `composer.json` (PHP项目)
   - `requirements.txt` (Python项目)
   - 其他项目标识文件

2. **环境变量目录** - 检查以下环境变量：
   - `PWD` - 当前工作目录
   - `CURSOR_CWD` - Cursor工作目录
   - `PROJECT_ROOT` - 项目根目录

3. **降级目录** - 如果以上都不可用：
   - 用户桌面目录 (`~/Desktop`)
   - 用户下载目录 (`~/Downloads`)
   - 用户家目录 (`~`)

## 📋 路径转换规则

MCP会自动将Yii2的命名规则转换为RESTful API路径：

| 控制器 | Action方法 | 生成路径 |
|-------|-----------|----------|
| RegisterController | actionCreate | `/register/create` |
| RegisterController | actionCompleteProfile | `/register/complete-profile` |
| HealthController | actionCheck | `/health/check` |
| UserController | actionGetProfile | `/user/get-profile` |

## 💡 使用场景

### 场景1：API开发阶段
```bash
# 开发完控制器后，快速生成文档
sapi pid:5 @UserController

# 增量更新单个接口
sapi pid:5 @UserController actionUpdate
```

### 场景2：文档查看和分析
```bash
# 下载项目所有API文档并生成易读版本
dapi pid:5

# 下载特定接口文档进行分析
dapi eid:24
```

### 场景3：多项目协作
- 在项目A中调用 → 文件保存到项目A根目录
- 在项目B中调用 → 文件保存到项目B根目录
- 自动识别项目边界，避免文件混乱

## 📊 生成的文件说明

### 1. 原始文档 (JSON)
包含完整的OpenAPI 3.0规范文档，可用于：
- 导入Postman、Swagger Editor
- 生成客户端SDK
- 技术集成

### 2. 格式化文档 (Markdown)
易读的API文档，包含：
- 项目信息概览
- 接口分类统计
- 详细的接口说明
- 认证需求标识

### 3. 分析结果 (JSON)
结构化的分析数据，包含：
- 项目基本信息
- API摘要统计
- 详细接口分析
- 下载信息

## 🛡️ 质量保证机制

为确保生成的OpenAPI文档质量，我们实施了多层验证机制：

### 📋 AI生成阶段
- **完整性要求**: AI必须生成包含 `openapi`、`info`、`paths`、`components` 的完整文档
- **标准模板**: 提供标准的响应组件模板，确保一致性
- **引用规范**: 明确要求所有引用都要有对应定义
- **示例完整**: 每个响应都要包含完整的schema和example

### 🔍 上传验证阶段
- **YAML语法检查**: 验证文档是否为有效的YAML格式
- **OpenAPI结构验证**: 检查是否符合OpenAPI 3.0.0规范
- **必需节点检查**: 确保包含所有必需的节点
- **引用完整性**: 验证所有 `$ref` 引用都有对应的定义
- **响应结构验证**: 检查每个接口的响应定义完整性

### ⚠️ 验证结果处理
- **错误阻断**: 严重错误会阻止文档上传，确保质量
- **警告提示**: 非致命问题会以警告形式提示，不影响上传
- **详细反馈**: 提供具体的错误位置和修复建议

### 📊 验证覆盖范围
```yaml
验证项目:
  ✅ YAML语法正确性
  ✅ OpenAPI 3.0.0结构完整性  
  ✅ 必需节点存在性（openapi, info, paths）
  ✅ $ref引用完整性检查
  ✅ 响应schema定义完整性
  ✅ 示例数据一致性
  ✅ Swagger Editor预览兼容性
```

## 🛠 开发调试

### 查看服务状态
```bash
# 检查配置
show_config

# 查看Cursor MCP日志
tail -f ~/.cursor/logs/mcp.log
```

### 测试连接
```bash
curl -X POST https://api.267girl.com/api/mcp/upload-doc \
  -H "X-MCP-KEY: your-key" \
  -H "Content-Type: application/json" \
  -d '{"project_id": 5, "openapi_content": "test"}'
```

## ❓ 常见问题

### Q: 提示 "未配置MCP Key"
A: 在Cursor的 `mcp.json` 文件中配置 `MCP_API_KEY` 环境变量，然后重启Cursor。

### Q: 找不到action方法
A: 确保控制器中存在以 `action` 开头的public方法，如 `public function actionCreate()`。

### Q: 文件保存位置不对
A: 检查当前项目是否有项目标识文件（如.git、package.json等），或使用 `pwd` 确认当前目录。

### Q: 工具无法加载
A: 重启Cursor中的MCP服务：设置 → MCP Tools → 关闭再重开 openapi-generator。

## 🔄 更新日志

### v1.2.0 (最新)
- ✨ 新增智能目录检测，自动保存到用户项目根目录
- ✨ DAPI工具支持自动分析和格式化
- ✨ 生成3种格式的文档文件
- 🐛 修复Python版本兼容性问题

### v1.1.0
- ✨ 新增DAPI下载工具
- ✨ 新增配置管理工具
- 🐛 优化错误处理

### v1.0.0
- 🎉 基础SAPI分析上传功能
- 🎉 支持Yii2控制器分析
- 🎉 自动路径转换

## 🔗 相关资源

- [FastMCP 文档](https://github.com/pydantic/fastmcp)
- [OpenAPI 3.0 规范](https://swagger.io/specification/)
- [Yii2 框架文档](https://www.yiiframework.com/doc/guide/2.0/zh-cn)

## �� 许可证

MIT License 