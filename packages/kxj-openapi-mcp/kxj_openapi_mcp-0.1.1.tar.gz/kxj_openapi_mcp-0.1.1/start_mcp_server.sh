#!/bin/bash

# MCP OpenAPI Generator启动脚本
# 用于启动Yii2控制器分析和OpenAPI文档生成服务

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 切换到脚本目录
cd "$SCRIPT_DIR"

# 检查Python和pip (静默)
if ! command -v python3 &> /dev/null; then
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    exit 1
fi

# 静默安装依赖
pip3 install -r requirements.txt &> /dev/null

# 启动服务 (只输出JSON数据)
python3 server.py 