from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime
from flask_login import login_required

from db import get_db_connection

bp = Blueprint('drill', __name__, url_prefix='/drill')


@bp.route('/list')
@login_required
def drill_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    drills = cursor.execute(
        '''
        SELECT
            d.id,
            d.name,
            d.start_date,
            d.end_date,
            d.frequency,
            d.status,
            d.created_at,
            d.updated_at,
            d.description,
            p1.name as executor_name,
            p2.name as creator_name,
            d.executor as executor_id,
            d.creator as creator_id,
            t.group_name as team_name,
            d.team_id,
            pl.name as plan_name,
            d.plan_id
        FROM drills d
        LEFT JOIN personnel p1 ON d.executor = p1.id
        LEFT JOIN personnel p2 ON d.creator = p2.id
        LEFT JOIN teams t ON d.team_id = t.id
        LEFT JOIN plans pl ON d.plan_id = pl.id
        ORDER BY d.created_at DESC
        '''
    ).fetchall()
    cursor.close()
    conn.close()
    return render_template('drill_list.html', drills=drills)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_drill():
    if request.method == 'POST':
        name = request.form['name']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        frequency = request.form['frequency']
        executor_id = request.form['executor_id']
        team_id = request.form['team_id']
        plan_id = request.form['plan_id']
        status = request.form['status']
        creator_id = request.form['creator_id']
        description = request.form.get('description', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO drills (name, start_date, end_date, frequency, executor, team_id, plan_id, status, creator, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (name, start_date, end_date, frequency, executor_id, team_id, plan_id, status, creator_id, description))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('演练计划添加成功！', 'success')
        return redirect(url_for('drill.drill_list'))
    
    return render_template('add_drill.html')

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_drill(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    drill = cursor.execute('''
        SELECT
            d.id,
            d.name,
            d.start_date,
            d.end_date,
            d.frequency,
            d.status,
            d.created_at,
            d.updated_at,
            d.description,
            p1.name as executor_name,
            p2.name as creator_name,
            d.executor as executor_id,
            d.creator as creator_id,
            t.group_name as team_name,
            d.team_id,
            pl.name as plan_name,
            d.plan_id
        FROM drills d
        LEFT JOIN personnel p1 ON d.executor = p1.id
        LEFT JOIN personnel p2 ON d.creator = p2.id
        LEFT JOIN teams t ON d.team_id = t.id
        LEFT JOIN plans pl ON d.plan_id = pl.id
        WHERE d.id = ?
    ''', (id,)).fetchone()
    
    if request.method == 'POST':
        name = request.form['name']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        frequency = request.form['frequency']
        executor_id = request.form['executor_id']
        team_id = request.form['team_id']
        plan_id = request.form['plan_id']
        status = request.form['status']
        creator_id = request.form['creator_id']
        description = request.form.get('description', '')
        
        cursor.execute('''
            UPDATE drills 
            SET name = ?, start_date = ?, end_date = ?, frequency = ?, 
                executor = ?, team_id = ?, plan_id = ?, status = ?, creator = ?, description = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (name, start_date, end_date, frequency, executor_id, team_id, plan_id, status, creator_id, description, id))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('演练计划更新成功！', 'success')
        return redirect(url_for('drill.drill_list'))
    
    cursor.close()
    conn.close()
    return render_template('edit_drill.html', drill=drill)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_drill(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM drills WHERE id = ?', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('演练计划已删除！', 'success')
    return redirect(url_for('drill.drill_list'))

@bp.route('/<int:id>/qualification_match')
@login_required
def get_qualification_match(id):
    """获取演练计划的资质匹配情况"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. 获取演练计划信息
        drill = cursor.execute('''
            SELECT d.team_id, d.plan_id
            FROM drills d
            WHERE d.id = ?
        ''', (id,)).fetchone()
        
        if not drill:
            return jsonify({
                'success': False,
                'message': '演练计划不存在'
            }), 404
            
        team_id = drill['team_id']
        plan_id = drill['plan_id']
        
        # 2. 获取预案的所有资质
        qualifications = cursor.execute('''
            SELECT id, title
            FROM plan_qualification
            WHERE plan_id = ?
        ''', (plan_id,)).fetchall()
        
        # 3. 获取团队的所有成员
        team_members = cursor.execute('''
            SELECT p.id, p.name, tr.role
            FROM teams_relation tr
            JOIN personnel p ON tr.member_id = p.id
            WHERE tr.group_id = ?
        ''', (team_id,)).fetchall()
        
        # 4. 一次性获取所有团队成员的资质
        member_qualifications = {}
        for member in team_members:
            member_qualifications[member['id']] = set()
            
        # 获取所有团队成员的资质
        member_quals = cursor.execute('''
            SELECT q.personnel_id, q.title
            FROM qualification q
            WHERE q.personnel_id IN ({})
        '''.format(','.join('?' * len(team_members))), 
        [member['id'] for member in team_members]).fetchall()
        
        # 构建成员资质映射
        for qual in member_quals:
            member_qualifications[qual['personnel_id']].add(qual['title'])
        
        # 5. 构建结果
        result = []
        for qual in qualifications:
            qual_info = {
                'id': qual['id'],
                'title': qual['title'],
                'matched_members': [],
                'unmatched_members': []
            }
            
            for member in team_members:
                member_info = {
                    'id': member['id'],
                    'name': member['name'],
                    'role': member['role']
                }
                
                if qual['title'] in member_qualifications[member['id']]:
                    qual_info['matched_members'].append(member_info)
                else:
                    qual_info['unmatched_members'].append(member_info)
            
            result.append(qual_info)
        
        return jsonify({
            'success': True,
            'data': {
                'drill_id': id,
                'team_id': team_id,
                'plan_id': plan_id,
                'qualifications': result
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取资质匹配情况失败: {str(e)}'
        }), 500
        
    finally:
        cursor.close()
        conn.close() 