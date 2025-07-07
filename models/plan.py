from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
import sqlite3
from datetime import datetime

from db import get_db_connection
from db.tools import sanitize_search_input

bp = Blueprint('plan', __name__, url_prefix='/plan')

@bp.route('/plans')
@login_required
def plan_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.id, p.name, p.description, p.last_editor, p.created_at, p.updated_at,
               per.name as editor_name
        FROM plans p
        LEFT JOIN personnel per ON p.last_editor = per.id
        ORDER BY p.updated_at DESC
    ''')
    plans = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('plan_list.html', plans=plans)

@bp.route('/plans/add', methods=['GET', 'POST'])
@login_required
def add_plan():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        last_editor = request.form['last_editor']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO plans (name, description, last_editor)
                VALUES (?, ?, ?)
            ''', (name, description, last_editor))
            conn.commit()
            flash('预案创建成功！', 'success')
            return redirect(url_for('plan.plan_list'))
        except sqlite3.Error as e:
            flash('创建预案失败！', 'danger')
        finally:
            cursor.close()
    
    return render_template('add_plan.html')

@bp.route('/plans/<int:plan_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_plan(plan_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        last_editor = request.form['last_editor']
        
        try:
            cursor.execute('''
                UPDATE plans 
                SET name = ?, description = ?, last_editor = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (name, description, last_editor, plan_id))
            conn.commit()
            flash('预案更新成功！', 'success')
            return redirect(url_for('plan.plan_list'))
        except sqlite3.Error as e:
            flash('更新预案失败！', 'danger')
        finally:
            cursor.close()
    
    cursor.execute('''
        SELECT p.*, per.name as editor_name
        FROM plans p
        LEFT JOIN personnel per ON p.last_editor = per.id
        WHERE p.id = ?
    ''', (plan_id,))
    plan = cursor.fetchone()
    cursor.close()
    
    return render_template('edit_plan.html', plan=plan)

@bp.route('/plans/<int:plan_id>/delete', methods=['POST'])
@login_required
def delete_plan(plan_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM plans WHERE id = ?', (plan_id,))
        conn.commit()
        flash('预案已删除！', 'success')
    except sqlite3.Error as e:
        flash('删除预案失败！', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('plan.plan_list'))

@bp.route('/search')
@login_required
def search_plan():
    name = request.args.get('name', '')
    if not name:
        return jsonify({'error': '请输入预案名称'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 清理和验证输入
    name = sanitize_search_input(name)
    # 使用参数化查询防止 SQL 注入
    search_term = f'%{name}%'
    plans = cursor.execute('''
        SELECT id, name, description
        FROM plans
        WHERE name LIKE ? OR description LIKE ?
        ORDER BY 
            CASE 
                WHEN name LIKE ? THEN 1  -- 完全匹配名称的排在前面
                WHEN name LIKE ? THEN 2  -- 以搜索词开头的排在其次
                ELSE 3                  -- 其他匹配排在最后
            END,
            name
        LIMIT 10
    ''', (search_term, search_term, name, f'{name}%')).fetchall()
    cursor.close()
    
    if not plans:
        return jsonify({'error': '未找到相关预案'})
    
    return jsonify({
        'data': [
            {
                'id': plan[0],
                'name': plan[1],
                'description': plan[2]
            }
            for plan in plans
        ]
    })

@bp.route('/<int:id>/qualifications', methods=['GET'])
@login_required
def get_plan_qualifications(id):
    """获取预案资质列表页面"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 查询预案资质
        cursor.execute('''
            SELECT 
                pq.id,
                pq.plan_id,
                pq.title,
                pq.created_at,
                pq.updated_at
            FROM plan_qualification pq
            WHERE pq.plan_id = ?
        ''', (id,))
        
        qualifications = cursor.fetchall()
        
        # 将查询结果转换为JSON格式
        result = []
        for qual in qualifications:
            result.append({
                'id': qual['id'],
                'plan_id': qual['plan_id'],
                'title': qual['title'],
                'created_at': qual['created_at'],
                'updated_at': qual['updated_at']
            })
        
        return render_template('plan/list.html', 
                             qualifications=result,
                             plan_id=id)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取资质列表失败: {str(e)}'
        }), 500
        
    finally:
        cursor.close()
        conn.close()

@bp.route('/<int:id>/qualifications', methods=['POST'])
@login_required
def add_plan_qualification(id):
    """添加预案资质"""
    data = request.get_json()
    
    # 验证必要字段
    if not data or 'title' not in data:
        return jsonify({
            'success': False,
            'message': '缺少必要参数'
        }), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 检查预案是否存在
        cursor.execute('SELECT id FROM plans WHERE id = ?', (id,))
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'message': '预案不存在'
            }), 404
        
        # 插入预案资质
        cursor.execute('''
            INSERT INTO plan_qualification (plan_id, title)
            VALUES (?, ?)
        ''', (id, data['title']))
        
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

@bp.route('/<int:plan_id>/qualifications/<int:qualification_id>', methods=['DELETE'])
@login_required
def delete_plan_qualification(plan_id, qualification_id):
    """删除预案资质"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 检查预案资质是否存在
        cursor.execute('''
            SELECT id FROM plan_qualification 
            WHERE plan_id = ? AND id = ?
        ''', (plan_id, qualification_id))
        
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'message': '预案资质不存在'
            }), 404
        
        # 删除预案资质
        cursor.execute('''
            DELETE FROM plan_qualification 
            WHERE plan_id = ? AND id = ?
        ''', (plan_id, qualification_id))
        
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