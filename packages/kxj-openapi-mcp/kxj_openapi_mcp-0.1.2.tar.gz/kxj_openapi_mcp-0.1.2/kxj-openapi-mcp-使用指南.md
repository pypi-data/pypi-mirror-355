# 📚 kxj-openapi-mcp 使用指南

> 🚀 专业的Yii2控制器OpenAPI文档生成工具，支持智能分析、完整文档生成和远程同步功能

## 📖 目录
- [1. 项目简介](#1-项目简介)
- [2. 快速开始](#2-快速开始)
- [3. 配置说明](#3-配置说明)
- [4. 功能详解](#4-功能详解)
- [5. 使用示例](#5-使用示例)
- [6. 故障排除](#6-故障排除)
- [7. 常见问题](#7-常见问题)

---

## 1. 项目简介

### 🎯 主要功能
- **智能分析Yii2控制器**：自动识别控制器结构、方法和参数
- **生成OpenAPI 3.0文档**：包含完整的请求/响应示例
- **中文文档支持**：支持中文API描述和错误信息
- **远程文档管理**：支持上传下载OpenAPI文档到远程服务器
- **详细日志记录**：记录所有API调用便于调试

### 🏗️ 技术架构
- **MCP协议**：基于Model Context Protocol构建
- **FastMCP框架**：高性能异步处理
- **Python 3.13+**：支持最新Python特性

---

## 2. 快速开始

### 📦 Step 1: 安装包

```bash
# 创建新环境
mkdir my-openapi-mcp && cd my-openapi-mcp
uv init . --python 3.13

# 安装主包
uv add kxj-openapi-mcp

# 安装依赖（临时需要，下个版本会自动包含）
uv add pyyaml httpx fastmcp
```

### ⚙️ Step 2: 配置Cursor

在Cursor设置中添加MCP服务器配置：

```json
{
  "mcpServers": {
    "kxj-openapi-mcp": {
      "command": "/path/to/your/env/.venv/bin/openapi-mcp",
      "args": [],
      "env": {
        "MCP_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### 🔄 Step 3: 重启Cursor
重启Cursor让配置生效

### ✅ Step 4: 验证安装
在Cursor中运行：
```
请使用show_config工具显示当前MCP服务配置状态
```

---

## 3. 配置说明

### 🔑 API Key配置

#### 为什么需要API Key？
某些功能需要访问远程服务器：
- `upload_openapi_doc_tool` - 上传OpenAPI文档
- `dapi` - 下载OpenAPI文档

#### 支持的环境变量（按优先级）：
1. **`MCP_API_KEY`** ⭐ 推荐，标准MCP配置
2. **`OPENAPI_MCP_KEY`** - 项目特定配置  
3. **`MCP_KEY`** - 简化配置

#### 配置方式：

**方式1：在Cursor MCP配置中设置**（推荐）
```json
{
  "mcpServers": {
    "kxj-openapi-mcp": {
      "command": "/path/to/.venv/bin/openapi-mcp",
      "args": [],
      "env": {
        "MCP_API_KEY": "sk-your-actual-api-key-here"
      }
    }
  }
}
```

**方式2：系统环境变量**
```bash
# 在 ~/.zshrc 或 ~/.bash_profile 中添加
export MCP_API_KEY="sk-your-actual-api-key-here"
```

---

## 4. 功能详解

### 🔓 无需API Key的功能

| 工具 | 功能描述 | 主要用途 |
|------|----------|----------|
| `sapi` | 分析Yii2控制器生成OpenAPI文档 | 核心功能，本地分析 |
| `show_config` | 显示配置状态和调试信息 | 检查配置是否正确 |
| `view_api_logs` | 查看API请求日志 | 调试和监控 |
| `clear_api_logs` | 清空所有API日志 | 日志管理 |

### 🔑 需要API Key的功能

| 工具 | 功能描述 | 主要用途 |
|------|----------|----------|
| `upload_openapi_doc_tool` | 上传OpenAPI文档到远程服务器 | 文档同步和共享 |
| `dapi` | 从远程服务器下载OpenAPI文档 | 获取已存储的文档 |

### 📝 详细功能说明

#### `sapi` - Yii2控制器分析工具
```
参数：
- pid (int): 项目ID
- file_content (str): Yii2控制器文件内容
- file_path (str, 可选): 文件路径
- specific_action (str, 可选): 指定分析特定方法

输出：
- 完整的OpenAPI 3.0 YAML文档
- 包含所有接口的详细定义
- 中文描述和错误示例
```

#### `upload_openapi_doc_tool` - 文档上传工具
```
参数：
- pid (int): 项目ID  
- openapi_yaml (str): OpenAPI YAML内容

输出：
- 上传状态和结果信息
- 远程服务器响应详情
```

#### `dapi` - 文档下载工具
```
参数：
- pid (int, 默认0): 项目ID
- eid (int, 默认0): 端点ID

输出：
- 下载的OpenAPI文档内容
- 服务器响应信息
```

---

## 5. 使用示例

### 🎯 示例1：检查配置状态（推荐首次使用）

```
请使用show_config工具显示当前MCP服务配置状态
```

**预期输出**：
- ✅ API Key配置状态
- 🔧 环境变量详情
- 📊 服务运行状态

---

### 🎯 示例2：分析Yii2控制器

```
请使用sapi工具分析这个Yii2控制器，生成OpenAPI文档：

<?php
namespace app\controllers;

use Yii;
use yii\web\Controller;
use app\models\User;

class UserController extends Controller
{
    public function actionCreate()
    {
        $model = new User();
        if ($model->load(Yii::$app->request->post(), '') && $model->validate()) {
            if ($model->save()) {
                return $this->back(1, [
                    'user_id' => $model->id,
                    'username' => $model->username
                ], '用户创建成功');
            }
        }
        return $this->errorModel($model);
    }
}

项目ID使用: 1
```

**预期输出**：
- 完整的OpenAPI YAML文档
- 包含POST /user/create接口定义
- 详细的请求参数和响应示例

---

### 🎯 示例3：上传生成的文档

```
请使用upload_openapi_doc_tool工具上传刚才生成的OpenAPI文档：

项目ID: 1  
YAML内容: [将上一步生成的完整YAML内容粘贴在这里]
```

**预期输出**：
- 上传成功确认
- 远程服务器存储信息

---

### 🎯 示例4：下载已存储的文档

```
请使用dapi工具下载项目文档：

项目ID: 1
端点ID: 0
```

**预期输出**：
- 完整的OpenAPI文档内容
- 服务器响应状态

---

## 6. 故障排除

### ❌ 常见错误及解决方案

#### 错误1：API Key未配置
```
错误信息：❌ 需要配置: 请在Cursor的mcp.json中设置MCP_API_KEY环境变量
```
**解决方案**：
1. 在Cursor MCP配置中添加 `MCP_API_KEY`
2. 重启Cursor
3. 使用 `show_config` 工具验证配置

#### 错误2：模块导入失败
```
错误信息：ModuleNotFoundError: No module named 'xxx'
```
**解决方案**：
```bash
# 安装缺失的依赖
uv add pyyaml httpx fastmcp
```

#### 错误3：命令找不到
```
错误信息：command not found: openapi-mcp
```
**解决方案**：
1. 检查虚拟环境路径
2. 确认包已正确安装
3. 使用完整路径：`/path/to/.venv/bin/openapi-mcp`

### 🔧 调试步骤

1. **检查安装**：
   ```bash
   which openapi-mcp
   ```

2. **验证包版本**：
   ```bash
   uv list | grep kxj-openapi-mcp
   ```

3. **测试MCP服务**：
   ```bash
   source .venv/bin/activate
   openapi-mcp  # 按Ctrl+C退出
   ```

4. **检查配置**：
   在Cursor中使用 `show_config` 工具

---

## 7. 常见问题

### Q1: 我可以不配置API Key吗？
**A**: 可以！本地分析功能（`sapi`）无需API Key，可以正常生成OpenAPI文档。只有上传下载功能需要API Key。

### Q2: 支持哪些Yii2版本？
**A**: 支持Yii2.0及以上版本，主要分析控制器结构和注释，对版本依赖较小。

### Q3: 生成的文档包含哪些内容？
**A**: 
- 完整的OpenAPI 3.0格式文档
- 所有接口的请求参数定义
- 详细的响应示例（成功、错误、异常）
- 中文描述和说明

### Q4: 如何获取API Key？
**A**: API Key由你的服务提供商提供，具体获取方式请咨询相关服务商。

### Q5: 能分析多个控制器文件吗？
**A**: 目前一次只能分析一个控制器文件，如需分析多个文件，请分别调用 `sapi` 工具。

### Q6: 生成的文档如何使用？
**A**: 
- 可以导入到Postman、Swagger UI等工具
- 用于API文档网站生成
- 团队协作和接口规范制定

---

## 🎉 结语

恭喜！你现在已经掌握了 kxj-openapi-mcp 的完整使用方法。这个工具将大大提升你的Yii2项目API文档生成效率。

### 🚀 开始你的OpenAPI文档生成之旅吧！

**建议使用流程**：
1. 先用 `show_config` 检查配置 ✅
2. 使用 `sapi` 分析控制器生成文档 📝  
3. 可选：使用 `upload_openapi_doc_tool` 上传文档 📤
4. 使用 `view_api_logs` 查看调用日志 📋

---

*最后更新：2025年1月 | 版本：v0.1.1* 