from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
import sqlite3
from datetime import datetime

from db import get_db_connection
from db.tools import sanitize_search_input

bp = Blueprint('personnel', __name__, url_prefix='/personnel')

@bp.route('/')
@login_required
def personnel_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    personnel_list = cursor.execute('''
        SELECT 
            id,
            name,
            contact,
            department,
            position,
            employee_id,
            status,
            emergency_contact,
            emergency_phone,
            notes,
            created_at,
            updated_at
        FROM personnel 
        ORDER BY created_at DESC
    ''').fetchall()

    cursor.close()
    conn.close()
    return render_template('personnel.html', personnel_list=personnel_list)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_personnel():
    if request.method == 'POST':
        # 获取JSON数据
        data = request.get_json()

        # 验证必填字段
        required_fields = ['name', 'contact', 'employee_id', 'position', 'department_id']
        for field in required_fields:
            if not data.get(field):
                return {'success': False, 'message': f'缺少必填字段: {field}'}, 400

        # 获取数据
        name = data['name']
        contact = data['contact']
        department_id = data['department_id']
        position = data['position']
        employee_id = data['employee_id']
        emergency_contact = data.get('emergency_contact', '')
        emergency_phone = data.get('emergency_phone', '')
        notes = data.get('notes', '')

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 先获取部门名称
        department = cursor.execute('SELECT name FROM departments WHERE id = ?', (department_id,)).fetchone()
        if not department:
            return {'success': False, 'message': '部门不存在'}, 400
            
        # 插入人员数据
        cursor.execute('''
            INSERT INTO personnel 
            (name, contact, department, position, employee_id, status, emergency_contact, emergency_phone, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (name, contact, department[0], position, employee_id, emergency_contact, emergency_phone, notes))
        
        personnel_id = cursor.lastrowid
        
        # 更新employee_department表
        cursor.execute('''
            INSERT INTO employee_department (employee_id, department_id, is_primary, position, start_date)
            VALUES (?, ?, 1, ?, CURRENT_DATE)
        ''', (personnel_id, department_id, position))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {'success': True, 'message': '人员添加成功'}
            
    return render_template('add_personnel.html')

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_personnel(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取人员信息和部门ID
    person = cursor.execute('''
        SELECT 
            p.id,
            p.name,
            p.contact,
            p.department,
            p.position,
            p.employee_id,
            p.status,
            p.emergency_contact,
            p.emergency_phone,
            p.notes,
            p.created_at,
            p.updated_at,
            ed.department_id
        FROM personnel p
        LEFT JOIN employee_department ed ON p.id = ed.employee_id AND ed.is_primary = 1
        WHERE p.id = ?
    ''', (id,)).fetchone()
    
    if request.method == 'POST':
        # 获取JSON数据
        data = request.get_json()
        
        # 更新人员基本信息
        cursor.execute('''
            UPDATE personnel 
            SET name = ?, 
                contact = ?, 
                department = ?, 
                position = ?, 
                employee_id = ?, 
                status = ?, 
                emergency_contact = ?, 
                emergency_phone = ?, 
                notes = ?, 
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            data['name'],
            data['contact'],
            data.get('department_name', ''),  # 使用部门名称
            data['position'],
            data['employee_id'],
            data['status'],
            data['emergency_contact'],
            data['emergency_phone'],
            data['notes'],
            id
        ))

        # 更新部门关联
        if data.get('department_id'):
            # 先删除旧的关联
            cursor.execute('DELETE FROM employee_department WHERE employee_id = ?', (id,))
            # 添加新的关联
            cursor.execute('''
                INSERT INTO employee_department (employee_id, department_id, is_primary, start_date, position)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP, ?)
            ''', (id, data['department_id'], data['position']))

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({
            'success': True,
            'message': '人员信息更新成功！'
        })
    
    cursor.close()
    conn.close()
    return render_template('edit_personnel.html', person=person)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_personnel(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 先删除部门关联
    cursor.execute('DELETE FROM employee_department WHERE employee_id = ?', (id,))
    
    # 再删除人员信息
    cursor.execute('DELETE FROM personnel WHERE id = ?', (id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('人员删除成功！', 'success')
    return redirect(url_for('personnel.personnel_list'))

@bp.route('/search', methods=['GET'])
@login_required
def search_personnel():
    name = request.args.get('name', '')
    if not name:
        return {'error': '请提供人员姓名'}, 400
    
    # 清理和验证输入
    name = sanitize_search_input(name)
    if not name:
        return {'error': '无效的搜索内容'}, 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 使用参数化查询进行模糊匹配
    search_pattern = f'%{name}%'
    personnel = cursor.execute('''
        SELECT 
            id,
            name,
            contact,
            department,
            position,
            employee_id,
            status,
            emergency_contact,
            emergency_phone,
            notes,
            created_at,
            updated_at
        FROM personnel 
        WHERE name LIKE ?
        ORDER BY name
        LIMIT 10
    ''', (search_pattern,)).fetchall()
    
    if not personnel:
        return {'error': '未找到相关人员信息'}, 404
        
    # 将查询结果转换为字典列表
    result = []
    for person in personnel:
        person_dict = {
            'id': person[0],
            'name': person[1],
            'contact': person[2],
            'department': person[3],
            'position': person[4],
            'employee_id': person[5],
            'status': person[6],
            'emergency_contact': person[7],
            'emergency_phone': person[8],
            'notes': person[9],
            'created_at': person[10],
            'updated_at': person[11]
        }
        result.append(person_dict)
    
    return {'data': result}, 200

@bp.route('/list/tree/info')
@login_required
def personnel_tree_info():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取所有在职人员的基本信息
    personnel_list = cursor.execute('''
        SELECT 
            p.id,
            p.name,
            ed.department_id
        FROM personnel p
        LEFT JOIN employee_department ed ON p.id = ed.employee_id AND ed.is_primary = 1
    ''').fetchall()
    
    # 转换为JSON格式
    result = [{
        'id': person['id'],
        'name': person['name'],
        'department_id': person['department_id']
    } for person in personnel_list]
    
    cursor.close()
    conn.close()
    
    return jsonify(result)

@bp.route('/<int:id>', methods=['GET'])
@login_required
def get_personnel(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取人员基本信息
    person = cursor.execute('''
        SELECT 
            id,
            name,
            contact,
            department,
            position,
            employee_id,
            status,
            emergency_contact,
            emergency_phone,
            notes,
            created_at,
            updated_at
        FROM personnel 
        WHERE id = ?
        LIMIT 1
    ''', (id,)).fetchone()
    
    cursor.close()
    conn.close()
    
    if person is None:
        return jsonify({
            'success': False,
            'message': '未找到该人员'
        }), 404
        
    return jsonify({
        'success': True,
        'data': {
            'id': person[0],
            'name': person[1],
            'contact': person[2],
            'department': person[3],
            'position': person[4],
            'employee_id': person[5],
            'status': person[6],
            'emergency_contact': person[7],
            'emergency_phone': person[8],
            'notes': person[9],
            'created_at': person[10],
            'updated_at': person[11]
        }
    })

@bp.route('/<int:id>/qualifications', methods=['GET'])
@login_required
def get_personnel_qualifications(id):
    """获取人员资质列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取人员信息
    person = cursor.execute('''
        SELECT id, name FROM personnel WHERE id = ?
    ''', (id,)).fetchone()
    
    if not person:
        return "人员不存在", 404
    
    # 获取资质列表
    qualifications = cursor.execute('''
        SELECT id, qualification_type, source_url, description, created_at, title
        FROM qualification
        WHERE personnel_id = ?
        ORDER BY id DESC
    ''', (id,)).fetchall()
    
    # 将查询结果转换为字典列表
    qualification_list = []
    for qual in qualifications:
        # 处理静态资源路径
        source_url = qual[2]
        if source_url and not source_url.startswith('http'):
            # 确保路径格式正确
            if source_url.startswith('/'):
                source_url = source_url[1:]  # 移除开头的斜杠
            source_url = url_for('static', filename=source_url)
            
        qualification_dict = {
            'id': qual[0],
            'type': int(qual[1]),
            'source_url': source_url,
            'description': qual[3],
            'created_at': qual[4],
            'title': qual[5]
        }
        qualification_list.append(qualification_dict)
    
    cursor.close()
    conn.close()
    
    return render_template('personnel/qualifications.html', 
                         person={'id': person[0], 'name': person[1]},
                         qualifications=qualification_list)

@bp.route('/<int:id>/qualifications', methods=['POST'])
@login_required
def add_personnel_qualification(id):
    """添加人员资质"""
    data = request.get_json()
    
    # 验证必要字段
    if not data or 'type' not in data or 'description' not in data or 'title' not in data:
        return jsonify({
            'success': False,
            'message': '缺少必要参数'
        }), 400
    
    # 验证资质类型
    if data['type'] not in ['1', '2', '3']:
        return jsonify({
            'success': False,
            'message': '无效的资质类型'
        }), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 插入资质数据
        cursor.execute('''
            INSERT INTO qualification (personnel_id, qualification_type, source_url, description, title)
            VALUES (?, ?, ?, ?, ?)
        ''', (id, data['type'], data.get('source_url', ''), data['description'], data['title']))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': '添加成功',
            'data': {
                'id': cursor.lastrowid
            }
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'message': f'添加失败: {str(e)}'
        }), 500
        
    finally:
        cursor.close()
        conn.close()

@bp.route('/qualifications/<int:qual_id>', methods=['DELETE'])
@login_required
def delete_personnel_qualification(qual_id):
    """删除人员资质"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 检查资质是否存在
        qualification = cursor.execute('''
            SELECT personnel_id FROM qualification WHERE id = ?
        ''', (qual_id,)).fetchone()
        
        if not qualification:
            return jsonify({
                'success': False,
                'message': '资质不存在'
            }), 404
        
        # 删除资质
        cursor.execute('DELETE FROM qualification WHERE id = ?', (qual_id,))
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': '删除成功'
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500
        
    finally:
        cursor.close()
        conn.close()