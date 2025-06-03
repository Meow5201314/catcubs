from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def check_banned(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            # 检查邮箱验证
            if not current_user.email_verified:
                flash('请先验证您的邮箱地址', 'warning')
                return redirect(url_for('auth.resend_verification'))
            
            # 检查封禁状态
            if current_user.is_currently_banned():
                flash('您的账号已被封禁，无法执行此操作', 'danger')
                return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def email_verified_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.email_verified:
            flash('请先验证您的邮箱地址', 'warning')
            return redirect(url_for('auth.resend_verification'))
        
        return f(*args, **kwargs)
    return decorated_function
