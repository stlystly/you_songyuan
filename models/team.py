from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from flask_login import login_required

from db import get_db_connection
from db.tools import sanitize_search_input

bp = Blueprint('team', __name__, url_prefix='/team')

@bp.route('/teams')
@login_required
def team_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取所有团队信息
    cursor.execute('''
        SELECT t.id, t.group_name, t.notes, t.created_at, t.updated_at,
               COUNT(tr.id) as member_count,
               GROUP_CONCAT(DISTINCT CASE WHEN tr.role != 'LEADER' THEN p.name END) as member_names,
               GROUP_CONCAT(DISTINCT CASE WHEN tr.role = 'LEADER' THEN p.name END) as leader_name
        FROM teams t
        LEFT JOIN teams_relation tr ON t.id = tr.group_id
        LEFT JOIN personnel p ON tr.member_id = p.id
        LEFT JOIN teams_relation tr_leader ON t.id = tr_leader.group_id AND tr_leader.role = 'LEADER'
        LEFT JOIN personnel leader ON tr_leader.member_id = leader.id
        GROUP BY t.id, t.group_name, t.notes, t.created_at, t.updated_at
    ''')
    teams = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('team_list.html', teams=teams)

@bp.route('/teams/add', methods=['GET', 'POST'])
@login_required
def add_team():
    if request.method == 'POST':
        group_name = request.form['group_name']
        notes = request.form['notes']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO teams (group_name, notes)
            VALUES (?, ?)
        ''', (group_name, notes))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('团队创建成功！', 'success')
        return redirect(url_for('team.team_list'))
    
    return render_template('add_team.html')

@bp.route('/teams/<int:team_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_team(team_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        group_name = request.form['group_name']
        notes = request.form['notes']
        
        cursor.execute('''
            UPDATE teams 
            SET group_name = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (group_name, notes, team_id))
        conn.commit()
        
        flash('团队信息更新成功！', 'success')
        return redirect(url_for('team.team_list'))
    
    # 获取团队信息
    cursor.execute('''
        SELECT id, group_name, notes, created_at, updated_at 
        FROM teams 
        WHERE id = ?
    ''', (team_id,))
    team = cursor.fetchone()
    
    # 获取团队成员
    cursor.execute('''
        SELECT p.id, p.name, p.position, p.department, tr.role
        FROM teams_relation tr
        JOIN personnel p ON tr.member_id = p.id
        WHERE tr.group_id = ?
    ''', (team_id,))
    members = cursor.fetchall()
    
    # 获取所有可选人员
    cursor.execute('''
        SELECT id, name, position, department, employee_id 
        FROM personnel 
        WHERE status = "ACTIVE"
    ''')
    all_personnel = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('edit_team.html', team=team, members=members, all_personnel=all_personnel)

@bp.route('/teams/<int:team_id>/delete', methods=['POST'])
@login_required
def delete_team(team_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 首先删除团队成员关系
    cursor.execute('DELETE FROM teams_relation WHERE group_id = ?', (team_id,))
    # 然后删除团队
    cursor.execute('DELETE FROM teams WHERE id = ?', (team_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('团队已删除！', 'success')
    return redirect(url_for('team.team_list'))

@bp.route('/teams/<int:team_id>/members/add', methods=['POST'])
@login_required
def add_team_member(team_id):
    member_id = request.form['member_id']
    role = request.form['role']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO teams_relation (group_id, member_id, role)
            VALUES (?, ?, ?)
        ''', (team_id, member_id, role))
        conn.commit()
        flash('成员添加成功！', 'success')
    except sqlite3.IntegrityError:
        flash('该成员已在团队中！', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('team.edit_team', team_id=team_id))

@bp.route('/teams/<int:team_id>/members/<int:member_id>/delete', methods=['POST'])
@login_required
def delete_team_member(team_id, member_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM teams_relation 
        WHERE group_id = ? AND member_id = ?
    ''', (team_id, member_id))
    
    conn.commit()
    cursor.close()
    
    flash('成员已移除！', 'success')
    return redirect(url_for('team.edit_team', team_id=team_id))

@bp.route('/teams/<int:team_id>/members/<int:member_id>/edit', methods=['POST'])
@login_required
def edit_team_member(team_id, member_id):
    role = request.form['role']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE teams_relation 
            SET role = ?, updated_at = CURRENT_TIMESTAMP
            WHERE group_id = ? AND member_id = ?
        ''', (role, team_id, member_id))
        conn.commit()
        flash('成员角色更新成功！', 'success')
    except sqlite3.Error as e:
        flash('更新成员角色失败！', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('team.edit_team', team_id=team_id))

@bp.route('/search')
@login_required
def search_team():
    name = request.args.get('name', '')
    if not name:
        return jsonify({'error': '请输入团队名称'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 清理和验证输入
    name = sanitize_search_input(name)
    # 使用参数化查询防止 SQL 注入
    search_term = f'%{name}%'
    teams = cursor.execute('''
        SELECT id, group_name, notes
        FROM teams
        WHERE group_name LIKE ? OR notes LIKE ?
        ORDER BY 
            CASE 
                WHEN group_name LIKE ? THEN 1  -- 完全匹配名称的排在前面
                WHEN group_name LIKE ? THEN 2  -- 以搜索词开头的排在其次
                ELSE 3                        -- 其他匹配排在最后
            END,
            group_name
        LIMIT 10
    ''', (search_term, search_term, name, f'{name}%')).fetchall()
    cursor.close()
    
    if not teams:
        return jsonify({'error': '未找到相关团队'})
    
    return jsonify({
        'data': [
            {
                'id': team[0],
                'group_name': team[1],
                'notes': team[2]
            }
            for team in teams
        ]
    }) 