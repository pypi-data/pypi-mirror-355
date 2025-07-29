# DAPI 文档下载功能使用指南

## 🎯 功能概述

DAPI 是 MCP OpenAPI Generator 的文档下载功能，支持从服务器下载已生成的接口文档。

## 📖 命令格式

### 下载项目文档
```bash
dapi pid:项目ID
```

### 下载特定接口文档
```bash  
dapi eid:接口ID
```

## 💡 使用示例

### 示例1: 下载项目5的所有接口文档
```bash
dapi pid:5
```

**返回结果示例**:
```json
{
  "success": true,
  "download_info": {
    "type": "project",
    "id": 5,
    "content_length": 2048
  },
  "downloaded_content": "...", 
  "ai_analysis_prompt": "请分析以下OpenAPI文档内容，并生成格式化的接口文档说明",
  "next_step": "请使用AI分析downloaded_content中的OpenAPI文档，生成易读的接口文档"
}
```

### 示例2: 下载接口19的文档
```bash
dapi eid:19
```

**返回结果示例**:
```json
{
  "success": true,
  "download_info": {
    "type": "endpoint", 
    "id": 19,
    "content_length": 1024
  },
  "downloaded_content": "...",
  "ai_analysis_prompt": "请分析以下OpenAPI文档内容，并生成格式化的接口文档说明",
  "next_step": "请使用AI分析downloaded_content中的OpenAPI文档，生成易读的接口文档"
}
```

## 🔧 使用流程

### 第1步: 下载文档
在Cursor中执行下载命令:
```bash
dapi pid:5
# 或
dapi eid:19
```

### 第2步: AI分析文档
系统会返回下载的文档内容，然后请AI分析：

**提示AI的话**:
> 请分析以下OpenAPI文档内容，生成易读的接口文档说明：
> 
> [将downloaded_content内容粘贴给AI]

### 第3步: 格式化显示
AI会将OpenAPI格式的JSON文档转换为易读的格式，包括：
- 接口基本信息
- 请求参数说明  
- 响应格式说明
- 使用示例
- 错误代码说明

## 📊 返回数据结构

### 成功返回
```json
{
  "success": true,
  "download_info": {
    "type": "project|endpoint",    // 下载类型
    "id": 5,                       // 对应的ID
    "content_length": 1234         // 内容长度
  },
  "downloaded_content": "...",     // 下载的OpenAPI文档内容
  "ai_analysis_prompt": "...",     // AI分析提示
  "next_step": "..."              // 下一步操作说明
}
```

### 失败返回
```json
{
  "success": false,
  "error": "错误描述",
  "status_code": 404
}
```

## ⚠️ 注意事项

1. **API密钥配置**: 确保在MCP配置中正确设置了 `MCP_API_KEY`
2. **参数限制**: `pid` 和 `eid` 不能同时使用
3. **ID存在性**: 确保要下载的项目ID或接口ID在服务器上存在
4. **网络连接**: 确保能够访问下载服务器
5. **内容解析**: 下载的内容需要AI进一步分析才能生成易读文档

## 🔍 错误排除

### 常见错误及解决方案

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| 未配置MCP_API_KEY环境变量 | API密钥未设置 | 在MCP配置中添加环境变量 |
| 请提供pid或eid参数 | 参数缺失 | 确保提供了pid或eid其中一个 |
| 不能同时提供pid和eid参数 | 参数冲突 | 只使用pid或eid其中一个 |
| 下载失败: 项目不存在 | 项目ID错误 | 检查项目ID是否正确 |
| 下载失败: 接口不存在 | 接口ID错误 | 检查接口ID是否正确 |
| 网络连接错误 | 网络问题 | 检查网络连接和服务器状态 |

## 🚀 完整工作流示例

### 场景: 查看项目5的接口文档

1. **下载文档**
   ```bash
   dapi pid:5
   ```

2. **复制返回的内容**
   从返回结果中复制 `downloaded_content` 的内容

3. **请求AI分析**
   ```
   请分析以下OpenAPI文档内容，生成易读的接口文档说明：
   
   [粘贴downloaded_content内容]
   ```

4. **获得格式化文档**
   AI会生成包含以下内容的文档：
   - 接口列表及描述
   - 每个接口的参数说明
   - 响应格式和示例
   - 错误代码说明

这样就完成了从下载到格式化显示的完整流程！

---

**提示**: 如果你是第一次使用，建议先用 `dapi eid:19` 下载单个接口文档进行测试。 