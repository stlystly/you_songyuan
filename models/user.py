from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection

class User(UserMixin):
    def __init__(self, id, username, password_hash, full_name=None, role=1, active=True, last_login=None):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.full_name = full_name
        self.role = role
        self.active = active
        self.last_login = last_login

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self):
        return self.role >= 3
    
    @property
    def is_superadmin(self):
        return self.role == 4
    
    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, password_hash, full_name, role, active, last_login 
            FROM users 
            WHERE id = ?
        ''', (user_id,))
        user = cursor.fetchone()
        cursor.close()
        if user:
            return User(
                id=user['id'],
                username=user['username'],
                password_hash=user['password_hash'],
                full_name=user['full_name'],
                role=user['role'],
                active=user['active'],
                last_login=user['last_login']
            )
        return None

    @staticmethod
    def get_by_username(username):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, password_hash, full_name, role, active, last_login 
            FROM users 
            WHERE username = ?
        ''', (username,))
        user = cursor.fetchone()
        cursor.close()
        if user:
            return User(
                id=user['id'],
                username=user['username'],
                password_hash=user['password_hash'],
                full_name=user['full_name'],
                role=user['role'],
                active=user['active'],
                last_login=user['last_login']
            )
        return None

    def __repr__(self):
        return f'<User {self.username}>'

    @staticmethod
    def create(username, password, full_name=None, role=1):
        conn = get_db_connection()
        cursor = conn.cursor()
        password_hash = generate_password_hash(password)
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, role, active) 
                VALUES (?, ?, ?, ?, 1)
            ''', (username, password_hash, full_name, role))
            conn.commit()
            user_id = cursor.lastrowid
            cursor.close()
            return User(
                id=user_id,
                username=username,
                password_hash=password_hash,
                full_name=full_name,
                role=role,
                active=True
            )
        except Exception as e:
            conn.rollback()
            cursor.close()
            raise e 