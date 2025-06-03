from flask import Blueprint, request, jsonify, current_app, render_template
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename
import uuid
from PIL import Image
import io
import traceback
from flask_wtf.csrf import CSRFProtect

uploads = Blueprint('uploads', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 添加测试上传页面
@uploads.route('/test-upload')
@login_required
def test_upload():
    return render_template('test_upload.html', title='测试上传')

@uploads.route('/upload/image', methods=['POST'])
@login_required
def upload_image():
    try:
        # 打印请求信息用于调试
        print("\n==== 上传请求信息 ====")
        print(f"请求方法: {request.method}")
        print(f"请求表单: {request.form}")
        print(f"请求文件: {list(request.files.keys())}")
        print(f"Content-Type: {request.headers.get('Content-Type')}")
        print("=====================\n")
        
        if 'file' not in request.files:
            print("错误: 请求中没有 'file' 字段")
            print(f"请求文件字段: {list(request.files.keys())}")
            return jsonify({'error': '没有文件部分'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            print("错误: 文件名为空")
            return jsonify({'error': '没有选择文件'}), 400
        
        print(f"接收到文件: {file.filename}, 类型: {file.content_type}")
        
        if file and allowed_file(file.filename):
            # 创建上传目录（如果不存在）
            uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'images')
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir, exist_ok=True)
                print(f"创建目录: {uploads_dir}")
            
            # 生成安全的文件名
            filename = secure_filename(file.filename)
            # 添加随机UUID前缀，防止文件名冲突
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            
            # 处理图片
            try:
                img = Image.open(file)
                print(f"成功打开图片，原始大小: {img.size}, 格式: {img.format}")
                
                # 调整图片大小，最大宽度为1200像素
                max_width = 1200
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_size = (max_width, int(img.height * ratio))
                    img = img.resize(new_size, Image.LANCZOS)
                    print(f"调整图片大小为: {new_size}")
                
                # 保存处理后的图片
                upload_path = os.path.join(uploads_dir, unique_filename)
                print(f"准备保存到: {upload_path}")
                img.save(upload_path, optimize=True, quality=85)
                print(f"图片已保存")
            except Exception as e:
                print(f"图片处理错误: {str(e)}")
                print(traceback.format_exc())
                return jsonify({'error': f'图片处理错误: {str(e)}'}), 500
            
            # 返回成功信息和图片URL
            image_url = f"/static/uploads/images/{unique_filename}"
            print(f"上传成功，URL: {image_url}")
            return jsonify({
                'success': True,
                'file': {
                    'url': image_url
                }
            })
        
        print(f"不允许的文件类型: {file.filename}")
        return jsonify({'error': f'不允许的文件类型: {file.filename}'}), 400
    
    except Exception as e:
        print(f"上传处理异常: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500
