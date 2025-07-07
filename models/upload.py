import os
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from .auth import login_required

bp = Blueprint('upload', __name__, url_prefix='/upload')

# 允许的文件类型
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif'},
    'video': {'mp4'}
}

def allowed_file(filename, file_type):
    """检查文件类型是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS.get(file_type, set())

def get_file_path(file_type):
    """获取文件保存路径"""
    # 根据文件类型确定基础目录
    if file_type == 'image':
        base_dir = 'source/pic'
    elif file_type == 'video':
        base_dir = 'source/video'
    else:
        raise ValueError('不支持的文件类型')
    
    # 构建完整路径
    save_dir = os.path.join(current_app.static_folder, base_dir)
    
    # 确保目录存在
    os.makedirs(save_dir, exist_ok=True)
    
    return save_dir

@bp.route('/<file_type>', methods=['POST'])
@login_required
def upload_file(file_type):
    """处理文件上传
    
    Args:
        file_type: 文件类型，'image' 或 'video'
    """
    if file_type not in ['image', 'video']:
        return jsonify({
            'success': False,
            'message': '不支持的文件类型'
        }), 400
    
    # 检查是否有文件
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': '没有文件'
        }), 400
    
    file = request.files['file']
    
    # 检查文件名
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': '没有选择文件'
        }), 400
    
    # 检查文件类型
    if not allowed_file(file.filename, file_type):
        return jsonify({
            'success': False,
            'message': f'不支持的文件类型，允许的类型：{", ".join(ALLOWED_EXTENSIONS[file_type])}'
        }), 400
    
    try:
        # 获取保存路径
        save_dir = get_file_path(file_type)
        
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        # 添加时间戳避免重名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        # 保存文件
        file_path = os.path.join(save_dir, filename)
        file.save(file_path)
        
        # 生成访问URL
        relative_path = os.path.relpath(file_path, current_app.static_folder)
        url = f"/{relative_path}"
        
        return jsonify({
            'success': True,
            'message': '上传成功',
            'data': {
                'url': url,
                'filename': filename
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'上传失败: {str(e)}'
        }), 500 