#!/usr/bin/env python3
"""
MCP OpenAPI Generator for Yii2 Controllers
用于分析Yii2控制器并生成OpenAPI文档的MCP服务
"""

import os
import re
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Union
import httpx
import yaml
from fastmcp import FastMCP
from config_manager import config_manager

# 创建日志配置
def setup_api_logger():
    """设置API请求日志记录器"""
    logger = logging.getLogger('api_requests')
    logger.setLevel(logging.INFO)
    
    # 如果已经有处理器，直接返回
    if logger.handlers:
        return logger
    
    # 创建文件处理器
    log_file = os.path.join(os.path.dirname(__file__), 'api_requests.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    return logger

# 初始化日志记录器
api_logger = setup_api_logger()

def log_api_request(method: str, url: str, headers: dict = None, data: Any = None, params: dict = None):
    """记录API请求信息"""
    try:
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "type": "REQUEST",
            "method": method,
            "url": url,
            "headers": dict(headers) if headers else {},
            "params": params or {},
            "data": data
        }
        
        # 敏感信息处理
        if log_data["headers"].get("X-MCP-KEY"):
            log_data["headers"]["X-MCP-KEY"] = log_data["headers"]["X-MCP-KEY"][:8] + "..."
        
        api_logger.info(f"API_REQUEST: {json.dumps(log_data, ensure_ascii=False, indent=2)}")
    except Exception as e:
        api_logger.error(f"记录请求日志失败: {str(e)}")

def log_api_response(status_code: int, response_text: str, url: str = "", error: str = None):
    """记录API响应信息"""
    try:
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "type": "RESPONSE", 
            "url": url,
            "status_code": status_code,
            "response_text": response_text[:2000] if response_text else "",  # 限制长度避免日志过大
            "error": error
        }
        
        api_logger.info(f"API_RESPONSE: {json.dumps(log_data, ensure_ascii=False, indent=2)}")
    except Exception as e:
        api_logger.error(f"记录响应日志失败: {str(e)}")

# 创建MCP服务器实例
mcp = FastMCP("openapi-generator")

# AI分析提示词模板
ANALYSIS_PROMPT_TEMPLATE = """
# Yii2控制器API接口分析专家

请仔细分析这个Yii2控制器文件，生成完整的OpenAPI 3.0文档。

## 📋 分析范围
控制器: {controller_name}
{specific_action_instruction}

## 🎯 核心要求
1. 所有接口都是POST请求
2. 入参分析要求极其详细
3. 出参分析要包含所有可能的返回情况
4. 每种返回都必须有具体JSON示例

## 📍 接口路径转换规则
1. 控制器名转换：
   - 去掉"Controller"后缀
   - 转换为小写
   - RegisterController → register

2. 方法名转换：
   - 去掉"action"前缀  
   - 驼峰命名转连字符分隔
   - actionCreate → create
   - actionCompleteProfile → complete-profile
   - actionCheckEmail → check-email

3. 最终路径格式：
   - /{控制器名}/{方法名}
   - 例如：/register/create, /register/complete-profile

## 🔍 详细分析步骤

### 入参分析 (requestBody)
- 查看模型验证场景 (如: RegisterModel::SCENARIO_CREATE_ACCOUNT)
- 分析 $this->model->load($this->params, '') 中使用的参数
- 查看 @param 注释说明
- 确定每个参数的：
  * 类型 (string/integer/boolean/array等)
  * 是否必填 (required数组)
  * 长度限制、格式要求
  * 中文描述和用途
  * 默认值 (如果有)

### 出参分析 (responses)
必须包含以下所有情况：
- ✅ 成功返回：$this->back(1, [...]) 的情况
- ❌ 参数错误：$this->errorModel($model) 的情况  
- ❌ 业务错误：$this->error('...') 的情况
- ❌ 异常错误：catch Exception 的情况

### 返回示例要求
每种返回都要提供真实的JSON示例：
```json
// 成功示例 (200)
{
  "ok": 1,
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGci...",
    "uid": 12345,
    "user_info": {
      "nickname": "用户昵称",
      "email": "user@example.com"
    },
    "profile_completed": false
  },
  "msg": "注册成功，请完善个人信息"
}

// 参数错误示例 (400)
{
  "ok": 0,
  "msg": "邮箱格式不正确",
  "errors": {
    "email": ["邮箱格式不正确"],
    "password": ["密码长度不能少于6位"]
  }
}

// 业务错误示例 (400)
{
  "ok": 0,
  "msg": "该邮箱已被注册，请使用其他邮箱或直接登录"
}

// 系统异常示例 (500)
{
  "ok": 0,
  "msg": "系统异常，请稍后重试"
}
```

## 📋 输出格式严格要求
- 接口路径：按照上述转换规则生成
- HTTP方法：全部为POST
- Content-Type：application/json
- 响应状态码：至少包含200、400、500
- 每个响应都要有详细的schema定义和example
- 使用中文描述所有字段和接口用途

## ⚠️ 特别注意
- 分析$this->uid的使用（表示需要认证的接口）
- 分析$this->optional数组（表示无需认证的接口）
- 查看try-catch块中的异常处理逻辑
- 注意业务逻辑中的条件判断（如邮箱已存在检查）
- 每个接口都要有详细的summary和description

## 🚨 OPENAPI文档完整性要求 🚨
生成的OpenAPI文档必须符合以下规范：

1. **完整的文档结构**：
   - 必须包含 `openapi: 3.0.0`
   - 必须包含完整的 `info` 节点
   - 必须包含 `paths` 节点定义所有接口
   - 必须包含 `components` 节点定义可复用组件

2. **Components规范**：
   ```yaml
   components:
     schemas:
       SuccessResponse:
         type: object
         properties:
           ok: 
             type: integer
             example: 1
           data:
             type: object
           msg:
             type: string
       ErrorResponse:
         type: object
         properties:
           ok:
             type: integer
             example: 0
           msg:
             type: string
       ValidationErrorResponse:
         type: object
         properties:
           ok:
             type: integer
             example: 0
           msg:
             type: string
           errors:
             type: object
             additionalProperties:
               type: array
               items:
                 type: string
   ```

3. **引用规范**：
   - 如果使用 `$ref` 引用，必须在 `components.schemas` 中定义对应的schema
   - 不允许存在未定义的引用
   - 建议直接在responses中内联定义schema，避免过度使用引用

4. **文档验证要求**：
   - 生成的YAML必须能通过OpenAPI 3.0语法验证
   - 必须能在Swagger Editor中正常预览
   - 所有字段类型定义必须正确
   - 示例数据必须与schema定义匹配

5. **响应定义规范**：
   - 每个响应都要有完整的schema定义
   - 每个响应都要有具体的example
   - schema中要包含所有必要的properties定义
   - 避免使用过于复杂的嵌套引用

## 📤 输出要求
请直接输出完整的OpenAPI 3.0.0 YAML格式文档，确保：
- 文档结构完整，包含所有必需节点
- 所有引用都有对应定义
- 可以在Swagger Editor中正常预览
- 符合OpenAPI 3.0.0规范
- 不要有任何其他说明文字

## 🚨 关键提醒：完成分析后必须上传！
**⚠️ 重要警告：生成OpenAPI文档只是第一步，必须完成上传才算任务成功！**

**🎯 完整任务流程：**
1. ✅ 分析控制器并生成OpenAPI YAML文档
2. 🚨 **必须执行**：使用 `upload_openapi_doc_tool` 工具上传生成的YAML文档

**💡 上传命令示例：**
```
upload_openapi_doc_tool pid:<项目ID> yaml_content:<生成的YAML内容>
```

**❌ 任务失败的典型情况：**
- 只生成了文档但忘记上传
- 跳过了 upload_openapi_doc_tool 工具的使用
- 认为生成文档就算完成了任务

**✅ 任务成功的标准：**
- 生成了完整的OpenAPI文档 + 成功上传到服务器

## 🎯 建议使用的标准Components模板
为确保文档完整性，建议在生成的OpenAPI文档中包含以下标准组件定义：

```yaml
{standard_components_template}
```

你可以直接使用这些标准组件，或者根据具体需求进行调整。

控制器文件内容：
```php
{file_content}
```
"""

def extract_controller_name(file_content: str) -> str:
    """从文件内容中提取控制器名称"""
    # 匹配 class XXXController
    match = re.search(r'class\s+(\w+Controller)', file_content)
    if match:
        return match.group(1)
    return "UnknownController"

def convert_controller_name(controller_name: str) -> str:
    """将控制器名转换为路径格式"""
    # 去掉Controller后缀，转小写
    name = controller_name.replace('Controller', '').lower()
    return name

def convert_action_name(action_name: str) -> str:
    """将action方法名转换为路径格式"""
    # 去掉action前缀
    name = action_name.replace('action', '')
    # 驼峰转连字符
    result = re.sub(r'([A-Z])', r'-\1', name).lower()
    return result.lstrip('-')

def generate_standard_components() -> str:
    """生成标准的OpenAPI components模板"""
    return """components:
  schemas:
    SuccessResponse:
      type: object
      properties:
        ok:
          type: integer
          example: 1
          description: "成功标识，1表示成功"
        data:
          type: object
          description: "业务数据"
        msg:
          type: string
          description: "响应消息"
    ErrorResponse:
      type: object
      properties:
        ok:
          type: integer
          example: 0
          description: "失败标识，0表示失败"
        msg:
          type: string
          example: "操作失败"
          description: "错误消息"
    ValidationErrorResponse:
      type: object
      properties:
        ok:
          type: integer
          example: 0
          description: "失败标识，0表示失败"
        msg:
          type: string
          example: "参数验证失败"
          description: "错误消息"
        errors:
          type: object
          description: "详细的参数验证错误信息"
          additionalProperties:
            type: array
            items:
              type: string
          example:
            email: ["邮箱格式不正确"]
            password: ["密码长度不能少于6位"]"""

def extract_actions(file_content: str, specific_action: Optional[str] = None) -> list:
    """提取action方法列表"""
    # 匹配 public function actionXxx
    pattern = r'public\s+function\s+(action\w+)\s*\([^)]*\)'
    actions = re.findall(pattern, file_content)
    
    if specific_action:
        # 如果指定了特定action，只返回匹配的
        if specific_action in actions:
            return [specific_action]
        else:
            return []
    
    return actions

def analyze_openapi_document(openapi_data: Dict[str, Any]) -> Dict[str, Any]:
    """分析OpenAPI文档并生成格式化的结果"""
    
    # 提取项目基本信息
    info = openapi_data.get("info", {})
    project_info = {
        "title": info.get("title", "未知项目"),
        "description": info.get("description", ""),
        "version": info.get("version", "1.0.0"),
        "contact": info.get("contact", {})
    }
    
    # 分析API路径
    paths = openapi_data.get("paths", {})
    api_list = []
    
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                api_info = {
                    "path": path,
                    "method": method.upper(),
                    "summary": details.get("summary", ""),
                    "description": details.get("description", ""),
                    "tags": details.get("tags", []),
                    "auth_required": "需要认证" if has_auth_requirement(details) else "无需认证"
                }
                api_list.append(api_info)
    
    # 按标签分组
    api_by_tags = {}
    for api in api_list:
        for tag in api["tags"]:
            if tag not in api_by_tags:
                api_by_tags[tag] = []
            api_by_tags[tag].append(api)
    
    # 生成API摘要
    api_summary = {
        "total_apis": len(api_list),
        "apis_by_tags": api_by_tags,
        "all_apis": api_list
    }
    
    # 生成详细API信息
    detailed_apis = []
    for api in api_list:
        path = api["path"]
        method = api["method"].lower()
        api_details = paths.get(path, {}).get(method, {})
        
        # 分析请求参数
        request_info = analyze_request_body(api_details.get("requestBody", {}))
        
        # 分析响应
        response_info = analyze_responses(api_details.get("responses", {}))
        
        detailed_api = {
            "basic_info": api,
            "request": request_info,
            "responses": response_info
        }
        detailed_apis.append(detailed_api)
    
    # 生成格式化文档
    formatted_doc = generate_formatted_documentation(project_info, api_summary, detailed_apis)
    
    return {
        "project_info": project_info,
        "api_summary": api_summary,
        "detailed_apis": detailed_apis,
        "formatted_doc": formatted_doc
    }

def has_auth_requirement(api_details: Dict[str, Any]) -> bool:
    """检查API是否需要认证"""
    # 检查是否有security要求
    if "security" in api_details:
        return len(api_details["security"]) > 0
    
    # 检查响应中是否有401状态码
    responses = api_details.get("responses", {})
    return "401" in responses

def analyze_request_body(request_body: Dict[str, Any]) -> Dict[str, Any]:
    """分析请求体信息"""
    if not request_body:
        return {"has_body": False}
    
    content = request_body.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema", {})
    
    # 修复：处理 properties 字段可能是数组的情况
    properties = schema.get("properties", {})
    if isinstance(properties, list):
        # 如果 properties 是数组（异常格式），转换为空字典
        properties = {}
        property_names = []
    else:
        # 正常情况，properties 是字典
        property_names = list(properties.keys())
    
    # 修复：处理 example 字段可能是数组的情况
    example = json_content.get("example", {})
    if isinstance(example, list):
        # 如果 example 是数组（异常格式），转换为空字典
        example = {}
    
    return {
        "has_body": True,
        "required": request_body.get("required", False),
        "description": request_body.get("description", ""),
        "schema_type": schema.get("type", ""),
        "properties": property_names,
        "required_fields": schema.get("required", []),
        "example": example
    }

def analyze_responses(responses: Dict[str, Any]) -> Dict[str, Any]:
    """分析响应信息"""
    response_summary = {}
    
    for status_code, response_details in responses.items():
        description = response_details.get("description", "")
        content = response_details.get("content", {})
        json_content = content.get("application/json", {})
        
        # 修复：处理 example 字段可能是数组的情况
        example = json_content.get("example", {})
        if isinstance(example, list):
            # 如果 example 是数组（异常格式），转换为空字典
            example = {}
        
        response_summary[status_code] = {
            "description": description,
            "has_content": bool(json_content),
            "schema": json_content.get("schema", {}),
            "example": example
        }
    
    return response_summary

def generate_formatted_documentation(project_info: Dict[str, Any], api_summary: Dict[str, Any], detailed_apis: list) -> str:
    """生成格式化的文档字符串"""
    
    doc = f"""
## 📖 项目基本信息
- **项目名称**: {project_info['title']}
- **描述**: {project_info['description'] if project_info['description'] else '暂无描述'}
- **版本**: {project_info['version']}

## 📊 API接口概览
- **接口总数**: {api_summary['total_apis']} 个
- **模块分布**:
"""
    
    # 按标签统计
    for tag, apis in api_summary['apis_by_tags'].items():
        auth_count = sum(1 for api in apis if api['auth_required'] == '需要认证')
        doc += f"  - **{tag}**: {len(apis)} 个接口 (认证: {auth_count}个, 公开: {len(apis)-auth_count}个)\n"
    
    doc += "\n## 📝 接口详细列表\n\n"
    
    # 按标签分组显示接口
    for tag, apis in api_summary['apis_by_tags'].items():
        doc += f"### 🔖 {tag} 模块\n\n"
        
        for api in apis:
            # 找到对应的详细信息
            detailed_api = next((d for d in detailed_apis if d['basic_info']['path'] == api['path'] and d['basic_info']['method'] == api['method']), None)
            
            doc += f"#### `{api['method']} {api['path']}`\n"
            doc += f"- **功能**: {api['summary']}\n"
            doc += f"- **认证**: {api['auth_required']}\n"
            
            if api['description']:
                doc += f"- **说明**: {api['description'][:150]}{'...' if len(api['description']) > 150 else ''}\n"
            
            # 添加详细的参数信息
            if detailed_api:
                request_info = detailed_api['request']
                response_info = detailed_api['responses']
                
                # 请求参数分析
                if request_info['has_body']:
                    doc += f"- **请求体**: {request_info['schema_type']}\n"
                    if request_info['required_fields']:
                        doc += f"  - 必填: `{', '.join(request_info['required_fields'])}`\n"
                    if request_info['properties']:
                        optional_fields = [p for p in request_info['properties'] if p not in request_info['required_fields']]
                        if optional_fields:
                            doc += f"  - 可选: `{', '.join(optional_fields)}`\n"
                else:
                    doc += f"- **请求体**: 无需请求体\n"
                
                # 响应状态码
                status_codes = list(response_info.keys())
                doc += f"- **响应码**: {', '.join(f'`{code}`' for code in status_codes)}\n"
            
            doc += "\n"
    
    return doc

def generate_intelligent_analysis(openapi_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> str:
    """生成智能化的开发分析和建议"""
    
    project_info = analysis_result["project_info"]
    api_summary = analysis_result["api_summary"]
    detailed_apis = analysis_result["detailed_apis"]
    
    # 分析API设计模式
    patterns = []
    auth_apis = [api for api in api_summary["all_apis"] if api["auth_required"] == "需要认证"]
    public_apis = [api for api in api_summary["all_apis"] if api["auth_required"] == "无需认证"]
    
    if len(auth_apis) > 0:
        patterns.append(f"🔐 **认证保护**: {len(auth_apis)}个接口需要认证")
    if len(public_apis) > 0:
        patterns.append(f"🌐 **公开访问**: {len(public_apis)}个接口无需认证")
    
    # 分析HTTP方法使用
    method_stats = {}
    for api in api_summary["all_apis"]:
        method = api["method"]
        method_stats[method] = method_stats.get(method, 0) + 1
    
    # 分析参数复杂度
    complex_apis = []
    simple_apis = []
    for detailed_api in detailed_apis:
        request_info = detailed_api["request"]
        if request_info["has_body"] and len(request_info.get("properties", [])) > 3:
            complex_apis.append(detailed_api["basic_info"]["path"])
        elif not request_info["has_body"] or len(request_info.get("properties", [])) <= 1:
            simple_apis.append(detailed_api["basic_info"]["path"])
    
    # 分析错误处理
    error_handling_analysis = []
    has_400_errors = False
    has_500_errors = False
    has_401_errors = False
    
    for detailed_api in detailed_apis:
        responses = detailed_api["responses"]
        if "400" in responses:
            has_400_errors = True
        if "401" in responses:
            has_401_errors = True
        if "500" in responses:
            has_500_errors = True
    
    if has_400_errors:
        error_handling_analysis.append("✅ 参数验证错误处理 (400)")
    if has_401_errors:
        error_handling_analysis.append("✅ 认证失败处理 (401)")
    if has_500_errors:
        error_handling_analysis.append("✅ 服务器错误处理 (500)")
    
    # 生成智能分析报告
    analysis = f"""
## 🤖 AI智能分析

### 📊 设计模式识别
{chr(10).join(patterns)}

### 🎯 API复杂度分析
- **简单接口** ({len(simple_apis)}个): 参数少于2个，易于使用
- **复杂接口** ({len(complex_apis)}个): 参数超过3个，需要重点关注

### 🛡️ 错误处理覆盖
{chr(10).join(error_handling_analysis) if error_handling_analysis else "⚠️ 未发现详细的错误处理模式"}

### 📈 HTTP方法分布
{chr(10).join([f"- **{method}**: {count}个接口" for method, count in method_stats.items()])}

### 💡 开发建议

#### 🔍 重点关注接口
"""
    
    # 推荐需要重点关注的接口
    if complex_apis:
        analysis += f"**复杂接口** (参数较多，需仔细测试):\n"
        for api_path in complex_apis[:3]:  # 最多显示3个
            analysis += f"- `{api_path}`\n"
        if len(complex_apis) > 3:
            analysis += f"- 还有 {len(complex_apis) - 3} 个复杂接口...\n"
        analysis += "\n"
    
    if auth_apis:
        analysis += f"**认证接口** (需要token验证):\n"
        for api in auth_apis[:3]:  # 最多显示3个
            analysis += f"- `{api['method']} {api['path']}`\n"
        if len(auth_apis) > 3:
            analysis += f"- 还有 {len(auth_apis) - 3} 个认证接口...\n"
        analysis += "\n"
    
    # 根据API特点生成具体建议
    analysis += "#### 🚀 实现建议\n"
    
    if "register" in str(api_summary).lower() or "login" in str(api_summary).lower():
        analysis += "- **用户认证流程**: 发现用户相关接口，建议优先实现注册/登录流程\n"
    
    if len(method_stats) == 1 and "POST" in method_stats:
        analysis += "- **统一POST请求**: 所有接口使用POST方法，符合内部规范\n"
    
    if has_400_errors and has_401_errors:
        analysis += "- **完善的错误处理**: 已包含参数验证和认证错误处理\n"
    
    if len(api_summary["apis_by_tags"]) > 1:
        analysis += "- **模块化设计**: 接口按功能模块分组，便于维护\n"
    
    # 代码实现建议
    analysis += """
#### 💻 代码实现要点

1. **参数验证**
   - 使用Model层的rules()方法定义验证规则
   - 实现scenarios()方法支持不同场景
   - 在Controller中使用 $this->errorModel($model) 返回验证错误

2. **统一响应格式**
   - 成功: $this->back(1, $data, $message)
   - 失败: $this->error($message, 0)
   - 认证失败: 返回401状态码

3. **安全实现**
   - JWT token验证机制
   - 敏感接口的认证中间件
   - 参数过滤和SQL注入防护

4. **测试建议**
   - 使用Codeception进行单元测试
   - 测试所有错误状态码场景
   - 验证参数边界条件
"""
    
    return analysis

# 注意：detect_user_working_directory 函数已移除
# 现在由AI使用edit_file工具来决定文件保存位置

async def upload_openapi_doc(openapi_content: str, project_id: int) -> Dict[str, Any]:
    """上传OpenAPI文档到服务器"""
    url = "https://api.267girl.com/api/mcp/upload-doc"
    
    headers = {
        "X-MCP-KEY": config_manager.get_mcp_key(),
        "Content-Type": "application/json"
    }
    
    payload = {
        "project_id": project_id,
        "openapi_content": openapi_content,
        "required": True,
        "content": "application/json"
    }
    
    # 记录请求日志
    log_api_request("POST", url, headers, payload)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            
            # 记录响应日志
            log_api_response(response.status_code, response.text, url)
            
            response.raise_for_status()
            
            response_data = response.json()
            if response_data.get("ok") == 1:
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response": response_data
                }
            else:
                return {
                    "success": False,
                    "error": response_data.get("msg", "上传失败"),
                    "status_code": response.status_code
                }
        except httpx.HTTPError as e:
            error_msg = str(e)
            status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            response_text = getattr(e.response, 'text', '') if hasattr(e, 'response') else ''
            
            # 记录错误响应日志
            log_api_response(status_code or 0, response_text, url, error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "status_code": status_code
            }

@mcp.tool()
async def sapi(
    pid: int,
    file_content: str,
    file_path: str = "",
    specific_action: Optional[str] = None
) -> str:
    """
    分析Yii2控制器并生成OpenAPI文档后上传
    
    Args:
        pid: 项目ID (简化输入参数，对应后端的project_id)
        file_content: 控制器文件内容
        file_path: 文件路径 (可选，用于提取控制器名)
        specific_action: 指定要分析的action方法 (可选，如actionCreate)
    
    Returns:
        分析和上传结果的JSON字符串
    """
    
    try:
        # 检查MCP Key配置
        mcp_key = config_manager.get_mcp_key()
        if not mcp_key:
            return json.dumps({
                "success": False,
                "error": "未配置MCP Key，请使用 'set key <your_key>' 命令设置API密钥"
            }, ensure_ascii=False, indent=2)
        
        # 提取控制器名称
        controller_name = extract_controller_name(file_content)
        if not controller_name or controller_name == "UnknownController":
            return json.dumps({
                "success": False,
                "error": "无法从文件内容中提取控制器名称"
            }, ensure_ascii=False, indent=2)
        
        # 检查是否存在action方法
        actions = extract_actions(file_content, specific_action)
        if not actions:
            action_info = f"指定的action '{specific_action}'" if specific_action else "任何action方法"
            return json.dumps({
                "success": False,
                "error": f"在控制器中未找到{action_info}"
            }, ensure_ascii=False, indent=2)
        
        # 准备AI提示词
        if specific_action:
            specific_action_instruction = f"仅分析以下action方法: {specific_action}"
        else:
            specific_action_instruction = f"分析所有action方法: {', '.join(actions)}"
        
        # 构建简化的提示词（避免复杂字符串格式化）
        prompt_data = {
            "controller_name": controller_name,
            "specific_action_instruction": specific_action_instruction,
            "file_content": file_content,
            "standard_components_template": generate_standard_components()
        }
        
        # 生成路径预览
        converted_controller = convert_controller_name(controller_name)
        path_preview = []
        for action in actions:
            converted_action = convert_action_name(action)
            path = f"/{converted_controller}/{converted_action}"
            path_preview.append(f"{action} -> {path}")
        
        # 构建返回结果
        analysis_result = {
            "success": True,
            
            # 🚨 关键任务提醒
            "🚨 CRITICAL_WORKFLOW": "MUST COMPLETE BOTH STEPS: ANALYZE + UPLOAD",
            "⚠️ 严重警告": "此任务包含两个必须完成的步骤，缺一不可！",
            
            # 📋 强制执行流程
            "📋 必须执行的完整流程": {
                "步骤1": "分析控制器并生成OpenAPI YAML文档",
                "步骤2": "🚨 必须上传！使用upload_openapi_doc_tool工具上传生成的YAML文档",
                "警告": "如果只完成步骤1而忽略步骤2，整个任务就是失败的！"
            },
            
            # 🎯 上传工具提醒
            "🎯 上传工具信息": {
                "工具名": "upload_openapi_doc_tool",
                "参数": f"pid: {pid}, openapi_yaml: <生成的YAML内容>",
                "重要性": "🚨 这是任务的核心环节，绝对不能遗漏！"
            },
            
            "controller_info": {
                "original_name": controller_name,
                "converted_name": converted_controller,
                "actions_to_analyze": actions,
                "path_preview": path_preview
            },
            "prompt_data": prompt_data,
            "analysis_prompt": "请使用以下信息分析Yii2控制器并生成OpenAPI 3.0文档",
            "next_step": "🚨 重要：生成OpenAPI YAML文档后，务必使用upload_openapi_doc_tool工具上传！这是完整流程的必要步骤！",
            "quality_assurance": {
                "validation_enabled": True,
                "description": "上传前将进行严格的OpenAPI文档验证，包括：",
                "validation_checks": [
                    "YAML语法正确性",
                    "OpenAPI 3.0.0结构完整性",
                    "必需节点存在性（openapi, info, paths）",
                    "$ref引用完整性检查",
                    "响应schema定义完整性",
                    "示例数据一致性"
                ],
                "standards": "确保生成的文档可在Swagger Editor中正常预览"
            },
            
            # 🔄 成功标准
            "🔄 任务成功标准": {
                "必须完成": [
                    "✅ 生成完整的OpenAPI 3.0 YAML文档",
                    "🚨 上传文档到服务器（使用upload_openapi_doc_tool）"
                ],
                "失败情况": [
                    "❌ 只生成文档但没有上传",
                    "❌ 跳过upload_openapi_doc_tool工具的调用"
                ]
            }
        }
        
        return json.dumps(analysis_result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"处理过程中发生异常: {str(e)}"
        }, ensure_ascii=False, indent=2)

def validate_openapi_document(openapi_data: Dict[str, Any]) -> Dict[str, Any]:
    """验证OpenAPI文档完整性"""
    errors = []
    warnings = []
    
    # 验证基本结构
    if "openapi" not in openapi_data:
        errors.append("缺少 'openapi' 版本声明")
    elif openapi_data["openapi"] != "3.0.0":
        warnings.append(f"OpenAPI版本为 {openapi_data['openapi']}，建议使用 3.0.0")
    
    if "info" not in openapi_data:
        errors.append("缺少 'info' 节点")
    else:
        info = openapi_data["info"]
        if "title" not in info:
            errors.append("info节点缺少 'title' 字段")
        if "version" not in info:
            errors.append("info节点缺少 'version' 字段")
    
    if "paths" not in openapi_data:
        errors.append("缺少 'paths' 节点")
    elif not openapi_data["paths"]:
        warnings.append("paths节点为空，没有定义任何接口")
    
    # 验证引用完整性
    used_refs = set()
    defined_schemas = set()
    
    # 收集所有使用的$ref
    def collect_refs(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "$ref" and isinstance(value, str):
                    if value.startswith("#/components/schemas/"):
                        schema_name = value.replace("#/components/schemas/", "")
                        used_refs.add(schema_name)
                elif isinstance(value, (dict, list)):
                    collect_refs(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, (dict, list)):
                    collect_refs(item, f"{path}[{i}]")
    
    collect_refs(openapi_data)
    
    # 收集所有定义的schemas
    if "components" in openapi_data and "schemas" in openapi_data["components"]:
        defined_schemas = set(openapi_data["components"]["schemas"].keys())
    
    # 检查未定义的引用
    undefined_refs = used_refs - defined_schemas
    if undefined_refs:
        errors.extend([f"引用了未定义的schema: {ref}" for ref in undefined_refs])
    
    # 检查未使用的定义
    unused_schemas = defined_schemas - used_refs
    if unused_schemas:
        warnings.extend([f"定义了但未使用的schema: {schema}" for schema in unused_schemas])
    
    # 验证响应结构
    if "paths" in openapi_data:
        for path, methods in openapi_data["paths"].items():
            for method, details in methods.items():
                if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                    if "responses" not in details:
                        errors.append(f"{method.upper()} {path} 缺少responses定义")
                    else:
                        responses = details["responses"]
                        if "200" not in responses:
                            warnings.append(f"{method.upper()} {path} 缺少200成功响应")
                        
                        for status_code, response_def in responses.items():
                            if "content" in response_def:
                                content = response_def["content"]
                                if "application/json" in content:
                                    json_content = content["application/json"]
                                    if "schema" not in json_content:
                                        warnings.append(f"{method.upper()} {path} 响应{status_code}缺少schema定义")
                                    if "example" not in json_content and "examples" not in json_content:
                                        warnings.append(f"{method.upper()} {path} 响应{status_code}缺少示例数据")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

@mcp.tool()
async def upload_openapi_doc_tool(
    pid: int,
    openapi_yaml: str
) -> str:
    """
    上传OpenAPI文档到服务器
    
    Args:
        pid: 项目ID (简化输入参数，对应后端的project_id)
        openapi_yaml: OpenAPI YAML格式文档内容
    
    Returns:
        上传结果的JSON字符串
    """
    
    try:
        # 验证YAML格式
        try:
            openapi_data = yaml.safe_load(openapi_yaml)
        except yaml.YAMLError as e:
            return json.dumps({
                "success": False,
                "error": f"OpenAPI YAML格式错误: {str(e)}",
                "validation_stage": "yaml_parsing"
            }, ensure_ascii=False, indent=2)
        
        # 验证OpenAPI文档完整性
        validation_result = validate_openapi_document(openapi_data)
        
        if not validation_result["valid"]:
            return json.dumps({
                "success": False,
                "error": "OpenAPI文档验证失败",
                "validation_stage": "openapi_validation",
                "validation_errors": validation_result["errors"],
                "validation_warnings": validation_result["warnings"],
                "suggestion": "请检查文档结构，确保包含所有必需的节点和正确的引用定义"
            }, ensure_ascii=False, indent=2)
        
        # 如果有警告，在结果中包含但不阻止上传 (转换参数名，保持后端API兼容性)
        upload_result = await upload_openapi_doc(openapi_yaml, pid)
        
        # 在成功结果中包含验证警告
        if validation_result["warnings"]:
            if isinstance(upload_result, dict) and upload_result.get("success"):
                upload_result["validation_warnings"] = validation_result["warnings"]
        
        return json.dumps(upload_result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"上传过程中发生异常: {str(e)}",
            "validation_stage": "exception"
        }, ensure_ascii=False, indent=2)

async def download_openapi_doc(project_id: Optional[int] = None, endpoint_id: Optional[int] = None) -> Dict[str, Any]:
    """下载OpenAPI文档"""
    url = "https://api.267girl.com/api/mcp/download-doc"
    
    headers = {
        "X-MCP-KEY": config_manager.get_mcp_key(),
        "Content-Type": "application/json"
    }
    
    # 构建请求参数
    payload = {}
    if project_id is not None:
        payload["project_id"] = project_id
    elif endpoint_id is not None:
        payload["endpoint_id"] = endpoint_id
    else:
        return {
            "success": False,
            "error": "必须提供project_id或endpoint_id参数"
        }
    
    # 记录请求日志
    log_api_request("POST", url, headers, payload)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            
            # 记录响应日志
            log_api_response(response.status_code, response.text, url)
            
            response.raise_for_status()
            
            response_data = response.json()
            if response_data.get("ok") == 1:
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "content": response_data.get("data", {}).get("content", ""),
                    "response": response_data
                }
            else:
                return {
                    "success": False,
                    "error": response_data.get("msg", "下载失败"),
                    "status_code": response.status_code
                }
        except httpx.HTTPError as e:
            error_msg = str(e)
            status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            response_text = getattr(e.response, 'text', '') if hasattr(e, 'response') else ''
            
            # 记录错误响应日志
            log_api_response(status_code or 0, response_text, url, error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "status_code": status_code
            }

@mcp.tool()
async def dapi(
    pid: int = 0,
    eid: int = 0
) -> str:
    """
    下载OpenAPI接口文档
    
    Args:
        pid: 项目ID - 下载整个项目的接口文档 (简化输入参数，对应后端的project_id)
        eid: 接口ID - 下载特定接口的文档 (简化输入参数，对应后端的endpoint_id)
    
    Returns:
        下载和解析结果的详细分析报告
    """
    
    try:
        # 检查MCP Key配置
        mcp_key = config_manager.get_mcp_key()
        if not mcp_key:
            return "❌ **错误**: 未配置MCP Key，请使用 'set key <your_key>' 命令设置API密钥"
        
        # 检查参数
        if pid == 0 and eid == 0:
            return "❌ **错误**: 请提供pid或eid参数\n\n**使用方法**:\n- `dapi pid:5` (下载项目文档)\n- `dapi eid:19` (下载特定接口文档)"
        
        if pid > 0 and eid > 0:
            return "❌ **错误**: 不能同时提供pid和eid参数，请选择其中一个"
        
        # 确定下载类型和ID
        download_type = "项目" if pid > 0 else "接口"
        file_id = pid if pid > 0 else eid
        
        # 下载文档 (转换参数名，保持后端API兼容性)
        final_project_id = pid if pid > 0 else None
        final_endpoint_id = eid if eid > 0 else None
        download_result = await download_openapi_doc(project_id=final_project_id, endpoint_id=final_endpoint_id)
        
        if not download_result["success"]:
            return f"❌ **下载失败**: {download_result['error']}\n状态码: {download_result.get('status_code', 'Unknown')}"
        
        # 获取下载的内容
        content = download_result["content"]
        
        if not content:
            return "❌ **错误**: 下载的文档内容为空"
        
        # 解析OpenAPI文档内容
        try:
            openapi_data = json.loads(content)
        except json.JSONDecodeError:
            return "❌ **错误**: 下载的内容不是有效的JSON格式"
        
        # 分析OpenAPI文档并生成易读格式
        analysis_result = analyze_openapi_document(openapi_data)
        
        # 构建详细的人性化分析报告
        report = f"""
# 🎯 OpenAPI 文档分析报告

## 📥 下载信息
- **类型**: {download_type}文档
- **ID**: {file_id}
- **文档大小**: {len(content):,} 字符
- **下载状态**: ✅ 成功

{analysis_result['formatted_doc']}

## 🔍 详细技术分析

### 🏗️ 架构特点
- **API设计风格**: RESTful API
- **认证方式**: {"需要认证" if any(api["auth_required"] == "需要认证" for api in analysis_result["api_summary"]["all_apis"]) else "无需认证"}
- **数据格式**: JSON
- **HTTP方法**: {", ".join(set(api["method"] for api in analysis_result["api_summary"]["all_apis"]))}

### 📋 接口详细分析

"""
        
        # 为每个接口生成详细分析
        for detailed_api in analysis_result["detailed_apis"]:  # 显示所有接口的详细分析
            api_info = detailed_api["basic_info"]
            request_info = detailed_api["request"]
            response_info = detailed_api["responses"]
            
            report += f"""
#### 🔗 `{api_info['method']} {api_info['path']}`

**功能描述**: {api_info['summary']}
{f"**详细说明**: {api_info['description'][:200]}{'...' if len(api_info['description']) > 200 else ''}" if api_info['description'] else ""}

**请求分析**:
"""
            
            if request_info["has_body"]:
                report += f"- 请求体类型: {request_info['schema_type']}\n"
                report += f"- 必填参数: {', '.join(request_info['required_fields']) if request_info['required_fields'] else '无'}\n"
                report += f"- 可选参数: {', '.join([p for p in request_info['properties'] if p not in request_info['required_fields']]) if request_info['properties'] else '无'}\n"
            else:
                report += "- 无请求体\n"
            
            report += "\n**响应分析**:\n"
            for status_code, response_detail in response_info.items():
                report += f"- `{status_code}`: {response_detail['description']}\n"
            
            report += "\n---\n"
        
        # 显示接口总数统计
        report += f"\n📈 **完整分析**: 已展示全部 {len(analysis_result['detailed_apis'])} 个接口的详细信息\n"
        
        # 添加使用建议
        report += f"""

## 💡 开发建议

### 🚀 后续开发方向
基于当前API文档分析，建议关注以下开发要点：

1. **参数验证**: 确保所有必填参数都有适当的验证逻辑
2. **错误处理**: 完善各种HTTP状态码的错误响应处理
3. **认证机制**: {"已实现认证保护，注意token有效性管理" if any(api["auth_required"] == "需要认证" for api in analysis_result["api_summary"]["all_apis"]) else "当前接口无认证要求，如有敏感操作请考虑添加认证"}
4. **数据一致性**: 注意接口间的数据格式保持一致

### 🔧 可能的改进点
- 添加更详细的接口文档描述
- 完善请求参数的验证规则
- 优化错误信息的返回格式
- 考虑添加接口版本管理

---

📝 **提示**: 这份分析基于下载的OpenAPI文档生成。如需进一步讨论特定接口的实现细节或开发方案，请直接提出！
"""
        
        # 添加智能分析
        report += generate_intelligent_analysis(openapi_data, analysis_result)
        
        return report
        
    except Exception as e:
        return f"❌ **处理异常**: {str(e)}"

@mcp.tool()
async def show_config(random_string: str = "dummy") -> str:
    """
    显示当前MCP配置信息
    从环境变量读取配置，符合标准MCP配置方式
    
    Returns:
        配置信息的详细报告
    """
    
    try:
        config = config_manager.get_all_config()
        is_configured = config_manager.is_configured()
        debug_info = config_manager.debug_key_info()
        
        report = f"""
# 🔧 MCP 配置状态报告

## 📊 配置概览
- **配置状态**: {'✅ 已配置' if is_configured else '❌ 未配置'}
- **配置方式**: 环境变量 (标准MCP配置)
- **当前Key**: {'已设置' if is_configured else '未设置'}

## 🌍 环境变量状态

### 🔑 API Key 环境变量
"""
        
        for var_name, status in debug_info["environment_variables"].items():
            status_icon = "✅" if status == "SET" else "❌"
            report += f"- **{var_name}**: {status_icon} {status}\n"
        
        report += f"""
### 📝 其他MCP环境变量
"""
        
        other_vars = ["MCP_SERVER_NAME", "MCP_SERVER_URL", "MCP_DEBUG", "OPENAPI_BASE_URL"]
        for var_name in other_vars:
            value = config.get(var_name)
            if value:
                report += f"- **{var_name}**: ✅ {value}\n"
            else:
                report += f"- **{var_name}**: ❌ 未设置\n"
        
        report += f"""
## 🚀 配置方法

### 标准MCP配置 (推荐)
在Cursor的 `mcp.json` 文件中配置：

```json
{{
  "mcpServers": {{
    "openapi-generator": {{
      "command": "/path/to/start_mcp_server.sh",
      "args": [],
      "env": {{
        "MCP_API_KEY": "your_api_key_here"
      }}
    }}
  }}
}}
```

### 环境变量优先级
1. **MCP_API_KEY** (推荐，标准MCP配置)
2. **OPENAPI_MCP_KEY** (项目特定配置)
3. **MCP_KEY** (简化配置)

## 💡 使用建议
"""
        
        if is_configured:
            report += """
✅ **配置完成**: 你的MCP服务已正确配置，可以使用所有功能！

### 可用命令
- `sapi pid:5 @Controller.php` - 分析上传控制器
- `dapi pid:5` - 下载项目文档
- `dapi eid:19` - 下载特定接口文档
"""
        else:
            report += """
❌ **需要配置**: 请在Cursor的mcp.json中设置MCP_API_KEY环境变量

### 配置步骤
1. 打开Cursor设置中的mcp.json文件
2. 在对应的服务配置中添加env字段
3. 设置MCP_API_KEY为你的API密钥
4. 重启Cursor让配置生效
"""
        
        return report
        
    except Exception as e:
        return f"❌ **配置检查异常**: {str(e)}"

@mcp.tool()
async def view_api_logs(lines: int = 50) -> str:
    """
    查看API请求日志
    
    Args:
        lines: 显示最后几行日志 (默认50行)
    
    Returns:
        日志内容的JSON字符串
    """
    
    try:
        log_file = os.path.join(os.path.dirname(__file__), 'api_requests.log')
        
        if not os.path.exists(log_file):
            return json.dumps({
                "success": True,
                "message": "日志文件不存在，可能还没有API请求记录",
                "logs": []
            }, ensure_ascii=False, indent=2)
        
        # 读取日志文件的最后几行
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        
        # 获取最后的指定行数
        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        # 统计信息
        total_lines = len(all_lines)
        request_count = sum(1 for line in all_lines if 'API_REQUEST:' in line)
        response_count = sum(1 for line in all_lines if 'API_RESPONSE:' in line)
        
        return json.dumps({
            "success": True,
            "log_info": {
                "total_lines": total_lines,
                "request_count": request_count,
                "response_count": response_count,
                "showing_lines": len(recent_lines),
                "log_file_path": log_file
            },
            "recent_logs": ''.join(recent_lines).strip()
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"读取日志文件时发生异常: {str(e)}"
        }, ensure_ascii=False, indent=2)

@mcp.tool()
async def clear_api_logs() -> str:
    """
    清空API请求日志文件
    
    Returns:
        清空结果的JSON字符串
    """
    
    try:
        log_file = os.path.join(os.path.dirname(__file__), 'api_requests.log')
        
        if os.path.exists(log_file):
            # 备份当前日志（如果需要的话）
            backup_file = log_file + '.backup'
            if os.path.exists(backup_file):
                os.remove(backup_file)
            os.rename(log_file, backup_file)
            
            return json.dumps({
                "success": True,
                "message": "API日志已清空",
                "backup_file": backup_file,
                "note": "原日志文件已备份为 .backup 文件"
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "success": True,
                "message": "日志文件不存在，无需清空"
            }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"清空日志文件时发生异常: {str(e)}"
        }, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    mcp.run() 