# -*- coding: utf-8 -*-
"""
应用入口文件
用于启动Flask开发服务器
"""

import os
import dotenv

# 加载环境变量
dotenv.load_dotenv()

import app as app_module

# 创建应用实例
app = app_module.create_app()

if __name__ == '__main__':
    # 开发模式下运行
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', '1') == '1'
    )
