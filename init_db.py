#!/usr/bin/env python3
import os
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

# 数据库文件路径
DB_FILE = "app.db"

def get_existing_tables(cursor):
    """获取已存在的表"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return {row[0] for row in cursor.fetchall()}

def init_database():
    print("连接数据库...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 获取已存在的表
    existing_tables = get_existing_tables(cursor)
    created_tables = set()
    skipped_tables = set()

    # 定义需要创建的表
    tables = {
        'users': '''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,           -- 用户名
            password_hash TEXT NOT NULL,             -- 密码哈希
            full_name TEXT,                          -- 全名 (用于系统内显示)
            role INTEGER NOT NULL DEFAULT 1,         -- 角色(superadmin:超级管理员4, admin:管理员3, operator:操作员2, user:普通用户1)
            active BOOLEAN NOT NULL DEFAULT 1,    -- 账号是否激活 (1:激活, 0:禁用)
            last_login TIMESTAMP,                    -- 最后登录时间
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- 最后修改时间
        )
        ''',
        'drills': '''
        CREATE TABLE drills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,                    -- 演练名称
            start_date DATE NOT NULL,              -- 开始日期
            end_date DATE NOT NULL,                -- 结束日期
            frequency TEXT NOT NULL,               -- 频率(如: 每周, 每月, 每季度等)
            executor INTEGER NOT NULL,             -- 执行人 (personnel表的id)
            team_id INTEGER NOT NULL,              -- 负责团队 (teams表的id)
            plan_id INTEGER NOT NULL,              -- 采用预案 (plans表的id)
            status TEXT NOT NULL DEFAULT 'pending', -- 状态(pending待执行, in_progress进行中, completed已完成, cancelled已取消)
            creator INTEGER NOT NULL,              -- 创建人 (personnel表的id)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 最后修改时间
            description TEXT                       -- 详细描述
        )
        ''',
        'personnel': '''
        CREATE TABLE personnel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,                    -- 人员姓名
            contact TEXT NOT NULL,                 -- 联系方式
            department TEXT,                       -- 所属部门
            department_id INTEGER,                 -- 所属部门id
            position TEXT,                         -- 职位
            employee_id TEXT UNIQUE,               -- 工号
            status TEXT DEFAULT 'ACTIVE',          -- 状态(ACTIVE:在职, INACTIVE:离职, LEAVE:休假)
            emergency_contact TEXT,                -- 紧急联系人
            emergency_phone TEXT,                  -- 紧急联系电话
            notes TEXT,                            -- 备注信息
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- 最后修改时间
        )
        ''',
        "department_id_index":"""
        CREATE INDEX IF NOT EXISTS idx_personnel_department_id ON personnel(department_id)
        """
        ,
        'teams': '''
        CREATE TABLE teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 组ID
            group_name TEXT NOT NULL,              -- 组名称
            notes TEXT,                            -- 备注信息
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 最后修改时间
        )
        ''',
        'teams_relation': '''
        CREATE TABLE teams_relation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- id
            group_id INTEGER NOT NULL,             -- 组ID
            member_id INTEGER NOT NULL,            -- 组员ID
            role TEXT NOT NULL,                    -- 队员身份(LEADER:组长, MEMBER:组员)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 最后修改时间
            UNIQUE(group_id, member_id)            -- 确保组员在组中唯一
        )
        ''',
        'plans': '''
        CREATE TABLE plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,                    -- 预案名称
            description TEXT,                      -- 详细描述
            last_editor INTEGER NOT NULL,             -- 最后编辑人id
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- 最后修改时间
        )
        ''',
        'departments': '''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,                    -- 部门名称
            code TEXT,                             -- 部门编码
            parent_id INTEGER DEFAULT -1,          -- 上级部门ID
            level INTEGER DEFAULT 0,               -- 部门层级
            description TEXT,                      -- 部门描述
            status INTEGER DEFAULT 1,              -- 状态(1:启用, 0:禁用)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- 最后修改时间
        )
        ''',
        'departments_level_index': '''
        CREATE INDEX IF NOT EXISTS idx_departments_level ON departments(level)
        ''',
        'departments_code_index': '''
        CREATE INDEX IF NOT EXISTS idx_departments_code ON departments(code)
        ''',
        'departments_parent_index': '''
        CREATE INDEX IF NOT EXISTS idx_departments_parent_id ON departments(parent_id)
        ''',
        'departments_level_parent_index': '''
        CREATE INDEX IF NOT EXISTS idx_departments_level_parent ON departments(level, parent_id, id)
        ''',
        'employee_department': '''
        CREATE TABLE IF NOT EXISTS employee_department (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,          -- 员工ID
            department_id INTEGER NOT NULL,        -- 部门ID
            is_primary BOOLEAN DEFAULT 0,          -- 是否主部门(1:是, 0:否)
            position TEXT,                         -- 职位
            start_date DATE NOT NULL,              -- 开始日期
            end_date DATE,                         -- 结束日期(为空表示当前在职)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 最后修改时间
            UNIQUE(employee_id, department_id)  -- 确保同一员工在同一部门的同一开始日期不重复
        )
        ''',
        'employee_department_employee_index': '''
        CREATE INDEX IF NOT EXISTS idx_employee_department_employee_id ON employee_department(employee_id)
        ''',
        'employee_department_department_index': '''
        CREATE INDEX IF NOT EXISTS idx_employee_department_department_id ON employee_department(department_id)
        ''',
        'video_info': '''
        CREATE TABLE IF NOT EXISTS video_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 视频id
            file_path TEXT,                        -- 视频文件路径
            video_name TEXT,                       -- 视频描述
            video_type TEXT,                       -- 视频类型
            video_size TEXT,                       -- 视频大小(字节)
            video_duration TEXT,                   -- 视频时长
            video_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 创建时间
        )
        ''',
        'qualification': '''
        CREATE TABLE IF NOT EXISTS qualification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,               -- 资质id
            title TEXT,                                         -- 资质标题
            personnel_id INTEGER NOT NULL,                      -- 人员id
            qualification_type INTEGER NOT NULL DEFAULT 3,      -- 资质类型 (1:视频, 2:图片, 3:仅描述)
            source_url TEXT,                                    -- 资源链接
            description TEXT,                                   -- 描述
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP      -- 创建时间
        )
        ''',
        'qualification_personnel_index': '''
        CREATE INDEX IF NOT EXISTS idx_qualification_personnel_id ON qualification(personnel_id)
        ''',
        "plan_qualification":'''
        CREATE TABLE IF NOT EXISTS plan_qualification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,                   -- 预案id
            title TEXT,                                 -- 资质标题
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- 最后修改时间
        )''',
        'plan_qualification_plan_index': '''
        CREATE INDEX IF NOT EXISTS idx_plan_qualification_plan_id ON plan_qualification(plan_id)
        '''
    }

    # 创建不存在的表
    for table_name, create_sql in tables.items():
        if table_name not in existing_tables:
            print(f"创建表 {table_name}...")
            cursor.execute(create_sql)
            created_tables.add(table_name)
        else:
            print(f"表 {table_name} 已存在, 跳过创建")
            skipped_tables.add(table_name)

    # 插入测试数据
    print("\n插入测试数据...")
    
    # 插入部门数据
    departments_data = [
        # 一级部门
        ('总公司', 'HQ', -1, 0, '公司总部', 1),
        # 二级部门
        ('研发中心', 'RD', 1, 1, '负责公司产品研发', 1),
        ('市场中心', 'MK', 1, 1, '负责市场营销和品牌推广', 1),
        ('运营中心', 'OP', 1, 1, '负责公司日常运营', 1),
        ('行政中心', 'AD', 1, 1, '负责公司行政事务', 1),
        # 三级部门
        ('前端开发部', 'FE', 2, 2, '负责前端开发', 1),
        ('后端开发部', 'BE', 2, 2, '负责后端开发', 1),
        ('测试部', 'QA', 2, 2, '负责质量保证', 1),
        ('产品部', 'PM', 2, 2, '负责产品设计', 1),
        ('市场推广部', 'MP', 3, 2, '负责市场推广', 1),
        ('品牌部', 'BR', 3, 2, '负责品牌建设', 1),
        ('销售部', 'SL', 3, 2, '负责产品销售', 1),
        ('客户服务部', 'CS', 4, 2, '负责客户服务', 1),
        ('技术支持部', 'TS', 4, 2, '负责技术支持', 1),
        ('人力资源部', 'HR', 5, 2, '负责人力资源管理', 1),
        ('财务部', 'FN', 5, 2, '负责财务管理', 1),
        ('法务部', 'LG', 5, 2, '负责法律事务', 1),
        # 四级部门
        ('Web前端组', 'WF', 6, 3, '负责Web前端开发', 1),
        ('移动端组', 'MF', 6, 3, '负责移动端开发', 1),
        ('Java开发组', 'JD', 7, 3, '负责Java后端开发', 1),
        ('Python开发组', 'PD', 7, 3, '负责Python后端开发', 1),
        ('自动化测试组', 'AT', 8, 3, '负责自动化测试', 1),
        ('性能测试组', 'PT', 8, 3, '负责性能测试', 1),
        ('UI设计组', 'UI', 9, 3, '负责UI设计', 1),
        ('产品规划组', 'PP', 9, 3, '负责产品规划', 1)
    ]
    
    cursor.executemany('''
        INSERT INTO departments (name, code, parent_id, level, description, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', departments_data)
    
    # 插入用户数据
    users_data = [
        ('admin', generate_password_hash('admin123'), '系统管理员', 3, 1)  # 用户名, 密码哈希, 全名, 角色(admin=3), 是否激活
    ]
    cursor.executemany('''
        INSERT INTO users (username, password_hash, full_name, role, active)
        VALUES (?, ?, ?, ?, ?)
    ''', users_data)
    
    # 插入演练数据
    drills_data = [
        ('2024年第一季度应急演练', '2024-01-01', '2024-03-31', '每季度', '1', '1', '1', 'pending', '1', '第一季度应急演练计划'),
        ('2024年第二季度应急演练', '2024-04-01', '2024-06-30', '每季度', '2', '2', '2', 'pending', '2', '第二季度应急演练计划'),
        ('2024年1月月度演练', '2024-01-01', '2024-01-31', '每月', '3', '1', '3', 'in_progress', '3', '1月月度演练计划')
    ]
    cursor.executemany('''
        INSERT INTO drills (name, start_date, end_date, frequency, executor, team_id, plan_id, status, creator, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', drills_data)

    # 插入人员数据
    personnel_data = [
        ('张三', '13800138001', '技术部', 6, '高级工程师', 'EMP001', 'ACTIVE', '张父', '13900139001', '技术骨干'),
        ('李四', '13800138002', '运维部', 7, '运维经理', 'EMP002', 'ACTIVE', '李父', '13900139002', '部门负责人'),
        ('王五', '13800138003', '安全部', 8, '安全工程师', 'EMP003', 'ACTIVE', '王父', '13900139003', '安全专家'),
        ('赵六', '13800138004', '技术部', 6, '工程师', 'EMP004', 'LEAVE', '赵父', '13900139004', '休假中')
    ]
    cursor.executemany('''
        INSERT INTO personnel (name, contact, department, department_id, position, employee_id, status, emergency_contact, emergency_phone, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', personnel_data)

    # 插入团队数据
    teams_data = [
        ('应急响应一组', '主要负责火灾和地震应急响应'),
        ('应急响应二组', '主要负责网络安全事件响应')
    ]
    cursor.executemany('''
        INSERT INTO teams (group_name, notes)
        VALUES (?, ?)
    ''', teams_data)

    # 插入团队成员关系数据
    teams_relation_data = [
        (1, 1, 'LEADER'),    # 张三是一组组长
        (1, 2, 'MEMBER'),    # 李四是一组成员
        (2, 3, 'LEADER'),    # 王五是二组组长
        (2, 4, 'MEMBER')     # 赵六是二组成员
    ]
    cursor.executemany('''
        INSERT INTO teams_relation (group_id, member_id, role)
        VALUES (?, ?, ?)
    ''', teams_relation_data)

    # 插入预案数据
    plans_data = [
        ('火灾应急预案', '发生火灾时的应急处理流程和注意事项', 1),
        ('地震应急预案', '发生地震时的应急处理流程和注意事项', 2),
        ('网络安全应急预案', '发生网络安全事件时的应急处理流程和注意事项', 3)
    ]
    cursor.executemany('''
        INSERT INTO plans (name, description, last_editor)
        VALUES (?, ?, ?)
    ''', plans_data)

    # 插入员工部门关系数据
    employee_department_data = [
        # 张三的任职记录
        (1, 6, 1, '高级工程师', '2020-01-01', None),  # 前端开发部，主部门
        # 李四的任职记录
        (2, 7, 1, '运维经理', '2019-06-01', None),  # 后端开发部，主部门
        # 王五的任职记录
        (3, 8, 1, '安全工程师', '2021-03-01', None),  # 测试部，主部门
        # 赵六的任职记录
        (4, 6, 1, '工程师', '2022-01-01', '2023-12-31')  # 前端开发部，已离职
    ]
    cursor.executemany('''
        INSERT INTO employee_department (
            employee_id, department_id, is_primary, position, 
            start_date, end_date
        )
        VALUES (?, ?, ?, ?, ?, ?)
    ''', employee_department_data)

    # 插入资质数据
    qualification_data = [
        ("资质1", 1, '1', 'source/video/gc2048.com-圣杯.mp4', '视频资质'),
        ("资质2",1, '2', 'source/pic/Gluo-NWWkAAQ-Cm.jpeg', '图片资质'),
        ("资质3",1, '3', 'https://example.com/certificate.pdf', '文档资质')
    ]
    
    for data in qualification_data:
        cursor.execute('''
            INSERT INTO qualification (title, personnel_id, qualification_type, source_url, description)
            VALUES (?, ?, ?, ?, ?)
        ''', data)

    # 提交事务
    conn.commit()

    # 显示表结构
    print("\n数据库表结构:")
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
    for table in cursor.fetchall():
        print(table[0])

    # 显示插入的数据
    print("\n插入的测试数据:")
    for table in ['users', 'drills', 'personnel', 'teams', 'plans']:
        print(f"\n{table} 表数据:")
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        for row in rows:
            print(row)

    # 关闭连接
    cursor.close()
    conn.close()

    # 总结表创建状态
    print("\n=== 数据库初始化总结 ===")
    print(f"数据库文件位置: {os.path.abspath(DB_FILE)}")
    print("\n表创建状态:")
    if created_tables:
        print(f"✅ 新创建的表: {', '.join(created_tables)}")
    if skipped_tables:
        print(f"⏭️ 已存在跳过的表: {', '.join(skipped_tables)}")
    print("\n数据库初始化完成!")

if __name__ == "__main__":
    try:
        init_database()
    except Exception as e:
        print(f"数据库初始化失败: {str(e)}")
        exit(1) 