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

### templates/ 目录详细说明
- **base.html**：所有页面的基础模板，定义了页面的整体布局和公共部分（如导航栏、页脚）。
- **index.html**：系统首页模板，通常为欢迎页或仪表盘。
- **drill_list.html**：演练计划列表页面模板。
- **add_drill.html**：添加演练计划的表单页面模板。
- **edit_drill.html**：编辑演练计划的表单页面模板。
- **plan_list.html**：预案列表页面模板。
- **add_plan.html**：添加预案的表单页面模板。
- **edit_plan.html**：编辑预案的表单页面模板。
- **personnel.html**：人员管理主页面模板。
- **add_personnel.html**：添加人员的表单页面模板。
- **edit_personnel.html**：编辑人员的表单页面模板。
- **department.html**：部门管理页面模板。
- **add_team.html**：添加团队的表单页面模板。
- **edit_team.html**：编辑团队的表单页面模板。
- **team_list.html**：团队列表页面模板。

#### templates/plan/
- **list.html**：预案的详细列表页面模板。

#### templates/personnel/
- **qualifications.html**：人员资质管理页面模板。

#### templates/components/
- **personnel_selector.html**：人员选择器组件模板，供其他页面弹窗选择人员时复用。
- **department_tree.html**：部门树形结构组件模板。
- **department_select.html**：部门下拉选择组件模板。
- **team_selector.html**：团队选择器组件模板。
- **plan_selector.html**：预案选择器组件模板。
- **select_options.html**：下拉选项渲染组件模板。
- **role_display.html**：角色显示组件模板。

#### templates/auth/
- **login.html**：用户登录页面模板。

---

### models/ 目录详细说明
- **__init__.py**：models 包初始化文件。
- **auth.py**：用户认证相关蓝图和逻辑（如登录、登出、注册等）。
- **user.py**：用户模型及相关操作。
- **department.py**：部门模型及部门相关业务逻辑。
- **personnel.py**：人员模型及人员相关业务逻辑。
- **team.py**：团队模型及团队相关业务逻辑。
- **plan.py**：预案模型及预案相关业务逻辑。
- **drill.py**：演练计划模型及演练相关业务逻辑。
- **upload.py**：文件上传相关蓝图和逻辑。
- **__pycache__/**：Python 自动生成的字节码缓存目录，无需关心。

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