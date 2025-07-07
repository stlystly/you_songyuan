from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from db import get_db_connection

bp = Blueprint('department', __name__, url_prefix='/department')

@bp.route('/')
def department_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    departments = cursor.execute('''
        SELECT id, name, code, parent_id, description, status
        FROM departments
        ORDER BY departments.level, departments.parent_id, departments.id
    ''').fetchall()
    cursor.close()
    conn.close()
    return render_template('department.html', departments=departments)

@bp.route('/tree')
@login_required
def department_tree():
    conn = get_db_connection()
    cursor = conn.cursor()
    departments = cursor.execute('''
        SELECT id, name, code, parent_id, description, status
        FROM departments
        ORDER BY level, parent_id, id
    ''').fetchall()
    cursor.close()
    conn.close()
    
    # 将查询结果转换为字典列表
    departments_list = []
    for dept in departments:
        departments_list.append({
            'id': dept['id'],
            'name': dept['name'],
            'code': dept['code'],
            'parent_id': dept['parent_id'],
            'description': dept['description'],
            'status': dept['status']
        })
    return jsonify(departments_list)

@bp.route('/add', methods=['GET'])
@login_required
def add_department():
    return render_template('add_department.html')

@bp.route('/add', methods=['POST'])
@login_required
def add_department_post():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    if data['parent_id'] == None or data['parent_id'] == '':
        data['parent_id'] = -1
    
    # 检查部门代码是否重复
    existing_dept = cursor.execute('SELECT id FROM departments WHERE code = ?', (data['code'],)).fetchone()
    if existing_dept and data['code'] != '':
        return jsonify({'success': False, 'message': '部门代码已存在'})
    
    # 获取父部门层级
    parent_level = -1
    if data['parent_id'] != None:
        parent = cursor.execute('SELECT level FROM departments WHERE id = ?', (data['parent_id'],)).fetchone()
        if parent:
            parent_level = parent['level']
    
    cursor.execute('''
        INSERT INTO departments (name, code, parent_id, level, description, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data['name'],
        data['code'],
        data['parent_id'],
        parent_level + 1 if data['parent_id'] != '0' else 0,
        data.get('description', ''),
        data.get('status', 1)
    ))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'message': '添加成功'})

@bp.route('/update', methods=['POST'])
@login_required
def update_department():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()

    # 检查部门是否存在
    dept = cursor.execute('SELECT id FROM departments WHERE id = ?', (data['id'],)).fetchone()
    if not dept:
        return jsonify({'success': False, 'message': '部门不存在'})
    
    # 获取父部门层级
    parent_level = -1
    if data['parent_id'] != '0' and data['parent_id'] != None:
        parent = cursor.execute('SELECT level FROM departments WHERE id = ?', (data['parent_id'],)).fetchone()
        if parent:
            parent_level = parent['level']
    
    
    # 更新部门信息
    cursor.execute('''
        UPDATE departments 
        SET name = ?, 
            code = ?, 
            parent_id = ?, 
            level = ?,
            description = ?, 
            status = ?
        WHERE id = ?
    ''', (
        data['name'],
        data['code'],
        data['parent_id'],
        parent_level + 1 if data['parent_id'] != '-1' else 0,
        data.get('description', ''),
        data.get('status', 1),
        data['id']
    ))
            
    # 递归更新所有子部门的层级
    update_children_level(data['id'], parent_level + 1 if data['parent_id'] != '-1' else 0, cursor)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'message': '更新成功'})
   
@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_department(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查部门是否存在
    dept = cursor.execute('SELECT id FROM departments WHERE id = ?', (id,)).fetchone()
    if not dept:
        return jsonify({'success': False, 'message': '部门不存在'})
    
    # 检查是否有子部门
    has_children = cursor.execute('SELECT id FROM departments WHERE parent_id = ?', (id,)).fetchone()
    if has_children:
        return jsonify({'success': False, 'message': '该部门下有子部门，无法删除'})
    
    cursor.execute('DELETE FROM departments WHERE id = ?', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'message': '删除成功'}) 

# 更新子部门的层级
def update_children_level(parent_id, parent_level, cursor):
    children = cursor.execute('SELECT id FROM departments WHERE parent_id = ?', (parent_id,)).fetchall()
    for child in children:
        cursor.execute('''
            UPDATE departments 
            SET level = ?
            WHERE id = ?
        ''', (parent_level + 1, child['id']))
        update_children_level(child['id'], parent_level + 1, cursor)
