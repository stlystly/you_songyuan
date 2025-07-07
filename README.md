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
├── app.py              # 主应用程序文件
├── requirements.txt    # 项目依赖
├── README.md          # 项目说明
└── templates/         # HTML 模板目录
    └── index.html    # 主页模板
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