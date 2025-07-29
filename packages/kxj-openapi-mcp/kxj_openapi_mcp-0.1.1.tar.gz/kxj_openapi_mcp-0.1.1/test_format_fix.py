#!/usr/bin/env python3
"""
测试异常格式修复
"""

import sys
import os
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from server import analyze_openapi_document

def test_abnormal_format():
    """测试异常格式的处理"""
    
    # 模拟你发现的异常返回格式
    abnormal_openapi_data = {
        "openapi": "3.0.0",
        "info": {
            "title": "测试",
            "description": "",
            "version": "1.0.0"
        },
        "paths": {
            "/health/check": {
                "post": {
                    "summary": "健康状态检查",
                    "description": "检查应用程序的健康状态，用于监控和负载均衡器健康检查",
                    "tags": ["Health"],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": []  # 异常：应该是对象，但这里是数组
                                },
                                "example": []  # 异常：应该是对象，但这里是数组
                            }
                        },
                        "required": False
                    },
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["ok"],
                                        "properties": {
                                            "ok": {
                                                "type": "integer",
                                                "example": 1,
                                                "description": "健康状态标识，1表示正常"
                                            }
                                        }
                                    },
                                    "example": {
                                        "ok": 1
                                    }
                                }
                            },
                            "description": "应用程序健康状态正常"
                        },
                        "500": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "ok": {
                                                "type": "integer",
                                                "example": 0,
                                                "description": "失败标识，0表示失败"
                                            },
                                            "msg": {
                                                "type": "string", 
                                                "example": "系统异常，请稍后重试",
                                                "description": "错误消息"
                                            }
                                        }
                                    },
                                    "example": {
                                        "ok": 0,
                                        "msg": "系统异常，请稍后重试"
                                    }
                                }
                            },
                            "description": "系统异常"
                        }
                    }
                }
            }
        }
    }
    
    try:
        print("🔧 测试异常格式处理...")
        
        # 测试分析函数
        result = analyze_openapi_document(abnormal_openapi_data)
        
        print("✅ 成功处理异常格式！")
        print(f"📊 项目信息: {result['project_info']}")
        print(f"📋 API摘要: 共 {result['api_summary']['total_apis']} 个接口")
        
        # 检查详细API信息
        for api in result['detailed_apis']:
            print(f"🔍 接口: {api['basic_info']['method']} {api['basic_info']['path']}")
            print(f"   请求体信息: {api['request']}")
            print(f"   响应信息: {list(api['responses'].keys())}")
        
        print("\n✅ 异常格式修复测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_abnormal_format()
    if success:
        print("\n🎉 所有测试通过！异常格式已成功修复。")
    else:
        print("\n💥 测试失败，需要进一步调试。")
        exit(1) 