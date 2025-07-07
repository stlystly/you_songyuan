import sqlite3
from flask import g
from dbutils.pooled_db import PooledDB

def create_connection():
    """创建数据库连接并设置 row_factory"""
    conn = sqlite3.connect('app.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# 创建数据库连接池
pool = PooledDB(
    creator=create_connection,  # 使用自定义的创建函数
    maxconnections=6,  # 连接池最大连接数
    blocking=True,    # 连接池满时是否阻塞等待
    maxusage=None,    # 一个连接最多被重复使用的次数，None表示无限制
    setsession=[],    # 开始会话前执行的命令列表
    ping=1,           # ping MySQL服务端，检查是否服务可用
)

def get_db_connection():
    # if 'db' not in g:
    #     g.db = pool.connection()
    # return g.db
    conn = sqlite3.connect('app.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def close_db(e=None):

    # 空闲连接数
    idle = len(pool._idle_cache)
    # 最大连接数
    maxconn = pool._maxconnections
    # 已创建的连接数（有些实现可能没有 _connections 属性）
    created = getattr(pool, '_connections', '未知')

    """清理数据库连接
    
    在请求结束时被调用，确保：
    1. 连接被正确关闭并归还到连接池
    2. 从 g 对象中移除连接引用
    """
    if 'db' in g:
        g.db.close()  # 归还连接到连接池
        g.pop('db')   # 从 g 对象中移除连接引用

def init_db(app):
    app.teardown_appcontext(close_db) 