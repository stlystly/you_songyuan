from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager
from models.drill import bp as drill_bp
from models.personnel import bp as personnel_bp
from models.team import bp as team_bp
from models.plan import bp as plan_bp
from models.auth import bp as auth_bp
from models.department import bp as department_bp
from models.user import User
from db import init_db
from models import upload

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # 用于flash消息

# 初始化数据库
init_db(app)

# 初始化 Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # 设置登录视图
login_manager.login_message = '请先登录'  # 设置提示消息
login_manager.login_message_category = 'info'  # 设置消息类型
login_manager.session_protection = 'strong'  # 设置会话保护级别

@login_manager.user_loader
def load_user(user_id):
    return User.get(int(user_id))

# 注册蓝图
app.register_blueprint(auth_bp)
app.register_blueprint(drill_bp)
app.register_blueprint(personnel_bp)
app.register_blueprint(team_bp)
app.register_blueprint(plan_bp)
app.register_blueprint(department_bp)
app.register_blueprint(upload.bp)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 