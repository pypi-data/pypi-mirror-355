#!/usr/bin/env python3
"""
调试 dapi 错误
"""

import sys
import os
import json
import asyncio
import traceback

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from server import download_openapi_doc, analyze_openapi_document
from config_manager import ConfigManager

async def debug_dapi():
    """调试 dapi 错误"""
    
    try:
        print("🔧 开始调试 dapi 命令...")
        
        # 测试下载
        print("📥 测试下载文档...")
        download_result = await download_openapi_doc(project_id=7)
        
        if not download_result["success"]:
            print(f"❌ 下载失败: {download_result}")
            return False
        
        print("✅ 下载成功")
        content = download_result["content"]
        print(f"📄 内容长度: {len(content)}")
        
        # 解析JSON
        print("🔍 解析JSON...")
        try:
            openapi_data = json.loads(content)
            print("✅ JSON解析成功")
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            return False
        
        # 打印数据结构预览
        print("📋 数据结构预览:")
        print(f"  - openapi: {openapi_data.get('openapi')}")
        print(f"  - info.title: {openapi_data.get('info', {}).get('title')}")
        print(f"  - paths count: {len(openapi_data.get('paths', {}))}")
        
        # 检查是否有异常的 properties 或 example 字段
        print("\n🔍 检查异常字段...")
        check_abnormal_fields(openapi_data, "root")
        
        # 测试分析
        print("\n📊 测试分析文档...")
        try:
            analysis_result = analyze_openapi_document(openapi_data)
            print("✅ 分析成功")
            print(f"📋 项目: {analysis_result['project_info']['title']}")
            print(f"📊 API总数: {analysis_result['api_summary']['total_apis']}")
        except Exception as e:
            print(f"❌ 分析失败: {str(e)}")
            print("🔍 详细错误信息:")
            traceback.print_exc()
            return False
        
        print("\n✅ 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 调试过程中发生异常: {str(e)}")
        traceback.print_exc()
        return False

def check_abnormal_fields(obj, path):
    """检查异常字段"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}"
            
            # 检查 properties 字段
            if key == "properties":
                if isinstance(value, list):
                    print(f"⚠️  发现异常字段: {current_path} = {value} (应该是对象，但是数组)")
                elif isinstance(value, dict):
                    print(f"✅ 正常字段: {current_path} (对象)")
            
            # 检查 example 字段
            elif key == "example":
                if isinstance(value, list):
                    print(f"⚠️  发现异常字段: {current_path} = {value} (应该是对象，但是数组)")
                elif isinstance(value, dict):
                    print(f"✅ 正常字段: {current_path} (对象)")
                else:
                    print(f"ℹ️  字段: {current_path} = {value} (原始类型)")
            
            # 递归检查
            if isinstance(value, (dict, list)):
                check_abnormal_fields(value, current_path)
    
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            current_path = f"{path}[{i}]"
            if isinstance(item, (dict, list)):
                check_abnormal_fields(item, current_path)

if __name__ == "__main__":
    success = asyncio.run(debug_dapi())
    if success:
        print("\n🎉 调试完成，dapi 应该可以正常工作了。")
    else:
        print("\n💥 调试发现问题，需要进一步修复。")
        exit(1) 