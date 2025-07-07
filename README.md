# Flask Demo

这是一个简单的 Flask 演示项目。

## 功能特点

- 基本的 Flask 路由设置
- 简单的 API 端点
- 响应式前端界面
- 交互式问候功能

## 安装和运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行应用：
```bash
python app.py
```

3. 在浏览器中访问：
```
http://localhost:5000
```

## 项目结构

```
.
├── app.py                # 主应用程序入口，Flask 启动文件，注册蓝图和初始化核心组件
├── requirements.txt      # Python 依赖包列表，项目环境依赖
├── README.md             # 项目说明文档
├── build.py              # 用于 PyInstaller 打包的自动化脚本
├── init_db.py            # 数据库初始化和建表脚本，包含表结构定义和测试数据插入
├── app.db                # SQLite 数据库文件，存储业务数据
├── 预案管理系统.spec      # PyInstaller 打包配置文件
├── .gitignore            # Git 忽略文件配置
├── .cursor               # Cursor 编辑器相关配置文件
├── auth.log              # 认证相关日志文件
├── static/               # 静态资源目录（JS、CSS、图片、字体等）
├── templates/            # 前端 HTML 模板目录（Jinja2 模板）
├── models/               # 业务模型与蓝图目录，包含各功能模块（如用户、部门、演练等）
├── scripts/              # 辅助脚本目录（如数据迁移、批量处理等）
├── logs/                 # 项目运行日志目录
├── db/                   # 其他数据库相关文件目录
└── __pycache__/          # Python 编译缓存目录（自动生成，可忽略）
```

TODO List
    测试
    对各种比例窗口适配测试
    数据库监控 连接数
    0 分页
    0.1 各种搜索框分页
    0.2 部门结构缺乏对万人级别的性能支持
    1 日志
    2 实时数据接口
list
    电话通知?
    网络版视频需要cdn
部署
    记得校验上传功能