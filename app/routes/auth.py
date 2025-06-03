from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db
from urllib.parse import urlparse as url_parse
from datetime import datetime, timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from flask_wtf.file import FileField, FileAllowed
from flask_wtf.recaptcha import RecaptchaField
from werkzeug.utils import secure_filename
import os
import uuid
from PIL import Image
from flask import current_app
from app.utils import get_beijing_time
from app.email import send_verification_email

auth = Blueprint('auth', __name__)

# 注册表单
class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    avatar = FileField('头像', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], '只允许图片文件！')])
    submit = SubmitField('注册')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('该用户名已被注册')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('该邮箱已被注册')

# 带 reCAPTCHA 的注册表单
class RegistrationFormWithCaptcha(RegistrationForm):
    recaptcha = RecaptchaField()

# 登录表单
class LoginForm(FlaskForm):
    username = StringField('用户名或邮箱', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    # 根据配置选择表单
    if current_app.config.get('RECAPTCHA_ENABLED', False):
        form = RegistrationFormWithCaptcha()
    else:
        form = RegistrationForm()

    form = RegistrationForm()
    if form.validate_on_submit():
        # 处理头像上传
        avatar_filename = 'default_avatar.jpg'
        if form.avatar.data:
            try:
                # 生成唯一文件名
                picture_fn = secure_filename(form.avatar.data.filename)
                unique_filename = f"{uuid.uuid4().hex}_{picture_fn}"

                # 读取和处理图像
                img = Image.open(form.avatar.data)

                # 裁剪成正方形
                width, height = img.size
                size = min(width, height)
                left = (width - size) // 2
                top = (height - size) // 2
                right = left + size
                bottom = top + size
                img = img.crop((left, top, right, bottom))

                # 调整大小为 128x128
                img = img.resize((128, 128), Image.LANCZOS)

                # 保存图像
                avatar_path = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars', unique_filename)
                img.save(avatar_path)

                avatar_filename = unique_filename
            except Exception as e:
                flash(f'头像处理出错: {str(e)}', 'danger')

        # 创建用户
        user = User(
            username=form.username.data,
            email=form.email.data,
            avatar=avatar_filename
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        # 发送验证邮件
        try:
            send_verification_email(user)
            flash('注册成功！请检查您的邮箱并验证邮箱地址。', 'success')
        except Exception as e:
            current_app.logger.error(f'发送验证邮件失败: {str(e)}')
            flash('注册成功，但验证邮件发送失败。请稍后重试发送验证邮件。', 'warning')

        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', title='注册', form=form)

# 邮箱验证路由
@auth.route('/verify-email/<token>')
def verify_email(token):
    user = User.query.filter_by(email_verification_token=token).first()

    if not user:
        flash('无效的验证链接', 'danger')
        return redirect(url_for('main.index'))

    # 检查令牌是否过期（24小时）
    if user.email_verification_sent_at:
        # 确保两个时间都有时区信息
        now = get_beijing_time()
        sent_at = user.email_verification_sent_at
        
        # 如果 sent_at 没有时区信息，添加北京时区
        if sent_at.tzinfo is None:
            import pytz
            beijing_tz = pytz.timezone('Asia/Shanghai')
            sent_at = beijing_tz.localize(sent_at)
        
        time_diff = now - sent_at
        if time_diff > timedelta(hours=24):
            flash('验证链接已过期，请重新发送', 'danger')
            return redirect(url_for('auth.resend_verification'))

    user.email_verified = True
    user.email_verification_token = None
    db.session.commit()

    flash('邮箱验证成功！', 'success')
    return redirect(url_for('main.index'))

# 重新发送验证邮件
@auth.route('/resend-verification', methods=['GET', 'POST'])
@login_required
def resend_verification():
    if current_user.email_verified:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        # 检查是否在1分钟内已发送过
        if current_user.email_verification_sent_at:
            now = get_beijing_time()
            sent_at = current_user.email_verification_sent_at
            
            # 如果 sent_at 没有时区信息，添加北京时区
            if sent_at.tzinfo is None:
                import pytz
                beijing_tz = pytz.timezone('Asia/Shanghai')
                sent_at = beijing_tz.localize(sent_at)
            
            time_diff = now - sent_at
            if time_diff < timedelta(minutes=1):
                flash('请稍后再试', 'warning')
                return redirect(url_for('auth.resend_verification'))

        try:
            send_verification_email(current_user)
            db.session.commit()
            flash('验证邮件已发送，请查收', 'success')
        except Exception as e:
            current_app.logger.error(f'发送验证邮件失败: {str(e)}')
            flash('验证邮件发送失败，请稍后重试', 'danger')

        return redirect(url_for('auth.resend_verification'))

    return render_template('auth/resend_verification.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # 通过用户名或邮箱查找用户
        user = User.query.filter((User.username == form.username.data) | 
                               (User.email == form.username.data)).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('用户名或密码不正确', 'danger')
            return render_template('auth/login.html', title='登录', form=form)
        
        # 登录用户
        login_user(user, remember=form.remember_me.data)
        user.last_login = get_beijing_time()
        db.session.commit()
        
        # 如果邮箱未验证，跳转到验证页面
        if not user.email_verified:
            flash('请先验证您的邮箱地址', 'warning')
            return redirect(url_for('auth.resend_verification'))
        
        # 重定向到next页面或首页
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        
        return redirect(next_page)
    
    return render_template('auth/login.html', title='登录', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    # 清除已浏览帖子的会话数据
    if 'viewed_posts' in session:
        session.pop('viewed_posts')
    flash('您已成功登出', 'info')
    return redirect(url_for('main.index'))
