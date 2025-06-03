import os
import uuid
from datetime import datetime, timedelta
from flask import current_app
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import current_user
from sqlalchemy import func, desc
from app import db
from PIL import Image
from werkzeug.utils import secure_filename
from app.utils import get_beijing_time
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Email, ValidationError
from flask_wtf.file import FileField, FileAllowed
from app.models import Post, User, Announcement, Notification, Message, Comment  # 添加 Comment 导入
from app.check_permissions import check_banned

main = Blueprint('main', __name__)

class EditProfileForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('电子邮箱', validators=[DataRequired(), Email()], render_kw={'readonly': True})
    title = StringField('个人头衔', validators=[Length(max=50)])
    avatar = FileField('更换头像', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], '只允许图片文件！')])
    submit = SubmitField('保存修改')
    
    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
    
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('该用户名已被使用')

class MessageForm(FlaskForm):
    content = TextAreaField('消息内容', validators=[DataRequired(), Length(max=1000)])
    recipient_id = HiddenField()
    submit = SubmitField('发送')

@main.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    # 获取所有用户的帖子（包括您和其他用户的）
    posts_pagination = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    # 获取每个帖子的评论数（只计算未删除的评论）
    for post in posts_pagination.items:
        try:
            post.comment_count = Comment.query.filter_by(
                post_id=post.id, 
                is_deleted=False
            ).count()
        except:
            post.comment_count = Comment.query.filter_by(
                post_id=post.id
            ).count()
    
    # 获取喵崽Ya用户的帖子（用于统计和展示最新文章）
    owner_user = User.query.filter_by(username='喵崽Ya').first()
    owner_posts = None
    owner_posts_count = 0
    
    if owner_user:
        # 获取喵崽Ya的最新帖子（用于"最新文章"区域展示）
        owner_posts = Post.query.filter_by(user_id=owner_user.id).order_by(Post.created_at.desc()).paginate(
            page=1, per_page=6, error_out=False)  # 只取6篇最新的
        # 统计喵崽Ya的帖子总数（用于统计卡片）
        owner_posts_count = Post.query.filter_by(user_id=owner_user.id).count()
        
        # 获取每个帖子的评论数
        for post in owner_posts.items:
            try:
                post.comment_count = Comment.query.filter_by(
                    post_id=post.id, 
                    is_deleted=False
                ).count()
            except:
                post.comment_count = Comment.query.filter_by(
                    post_id=post.id
                ).count()
    
    announcements = Announcement.query.filter_by(is_active=True).order_by(
        Announcement.created_at.desc()
    ).limit(3).all()
    
    return render_template('index.html', 
                         posts=posts_pagination,  # 所有用户的帖子
                         owner_posts=owner_posts,  # 喵崽Ya的帖子（用于最新文章展示）
                         owner_posts_count=owner_posts_count,  # 喵崽Ya的帖子数量（用于统计）
                         announcements=announcements)

@main.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).paginate(
        page=page, per_page=5, error_out=False)
    
    # 获取每个帖子的评论数（只计算未删除的评论）
    for post in posts.items:
        post.comment_count = Comment.query.filter_by(
            post_id=post.id, 
            is_deleted=False
        ).count()
    
    return render_template('profile.html', title=f'{username}的个人资料', user=user, posts=posts)

@main.route('/notifications')
@login_required
def notifications():
    # 获取用户的通知
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()

    return render_template('notifications.html', title='我的通知', notifications=notifications)

@main.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        abort(403)
    
    notification.is_read = True
    db.session.commit()
    
    return redirect(request.referrer or url_for('main.notifications'))

@main.route('/notifications/mark_all_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).all()
    
    for notification in notifications:
        notification.is_read = True
    
    db.session.commit()
    flash('所有通知已标为已读', 'success')
    
    return redirect(url_for('main.notifications'))

@main.route('/notifications/clear', methods=['POST'])
@login_required
def clear_notifications():
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('所有通知已清空', 'success')
    
    return redirect(url_for('main.notifications'))

@main.route('/messages')
@login_required
def messages():
    # 获取用户的对话列表（包括发送和接收的消息）
    conversations_query = db.session.query(
        db.case(
            (Message.sender_id == current_user.id, Message.recipient_id),
            else_=Message.sender_id
        ).label('other_user_id'),
        func.max(Message.created_at).label('last_message_time')
    ).filter(
        db.or_(
            Message.sender_id == current_user.id,
            Message.recipient_id == current_user.id
        )
    ).group_by(
        db.case(
            (Message.sender_id == current_user.id, Message.recipient_id),
            else_=Message.sender_id
        )
    ).order_by(
        func.max(Message.created_at).desc()
    ).all()

    # 获取对话用户的详细信息
    conversations = []
    for other_user_id, last_message_time in conversations_query:
        user = User.query.get(other_user_id)
        if user:
            # 获取与该用户的最后一条消息
            last_message = Message.query.filter(
                db.or_(
                    db.and_(Message.sender_id == current_user.id, Message.recipient_id == other_user_id),
                    db.and_(Message.sender_id == other_user_id, Message.recipient_id == current_user.id)
                )
            ).order_by(Message.created_at.desc()).first()

            # 获取未读消息数
            unread_count = Message.query.filter_by(
                sender_id=other_user_id,
                recipient_id=current_user.id,
                is_read=False
            ).count()

            conversations.append({
                'user': user,
                'last_message': last_message,
                'unread_count': unread_count
            })

    return render_template('messages.html', title='我的私信', conversations=conversations)

@main.route('/messages/<int:user_id>')
@login_required
def chat_with_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # 获取与该用户的所有消息
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user.id, Message.recipient_id == user_id),
            db.and_(Message.sender_id == user_id, Message.recipient_id == current_user.id)
        )
    ).order_by(Message.created_at.asc()).all()
    
    # 标记接收到的消息为已读
    unread_messages = Message.query.filter_by(
        sender_id=user_id,
        recipient_id=current_user.id,
        is_read=False
    ).all()
    
    for message in unread_messages:
        message.is_read = True
    
    db.session.commit()
    
    form = MessageForm()
    form.recipient_id.data = user_id
    
    return render_template('chat.html', title=f'与 {user.username} 的对话', 
                         user=user, messages=messages, form=form)

@main.route('/send_message', methods=['POST'])
@login_required
@check_banned
def send_message():
    form = MessageForm()
    
    if form.validate_on_submit():
        recipient = User.query.get_or_404(form.recipient_id.data)
        
        # 获取发送者发给接收者的消息数
        sent_count = Message.query.filter_by(
            sender_id=current_user.id,
            recipient_id=recipient.id
        ).count()
        
        # 获取接收者是否回复过
        has_reply = Message.query.filter_by(
            sender_id=recipient.id,
            recipient_id=current_user.id
        ).first()
        
        # 如果没有回复且已发送1条消息，阻止发送
        if not has_reply and sent_count >= 1:
            flash('对方还未回复您的消息，请等待回复后再发送', 'warning')
            return redirect(url_for('main.chat_with_user', user_id=recipient.id))
        
        # 如果有回复但已发送10条消息，阻止发送
        if has_reply and sent_count >= 10:
            flash('您已达到向该用户发送消息的上限（10条）', 'warning')
            return redirect(url_for('main.chat_with_user', user_id=recipient.id))
        
        message = Message(
            sender_id=current_user.id,
            recipient_id=recipient.id,
            content=form.content.data
        )
        
        db.session.add(message)
        db.session.commit()
        
        flash('消息发送成功！', 'success')
        return redirect(url_for('main.chat_with_user', user_id=recipient.id))
    
    flash('消息发送失败，请重试', 'danger')
    return redirect(url_for('main.messages'))

@main.route('/start_chat/<int:user_id>')
@login_required
@check_banned
def start_chat(user_id):
    """从用户资料页面开始聊天"""
    if user_id == current_user.id:
        flash('不能给自己发消息', 'warning')
        return redirect(url_for('main.profile', username=current_user.username))
    
    return redirect(url_for('main.chat_with_user', user_id=user_id))

@main.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)

    if form.validate_on_submit():
        # 检查昵称更改权限
        if form.username.data != current_user.username:
            if not current_user.can_change_nickname():
                flash('您一个月内只能更改一次昵称', 'danger')
                return redirect(url_for('main.edit_profile'))

        # 处理头像上传
        if form.avatar.data:
            try:
                # 生成唯一文件名
                picture_fn = secure_filename(form.avatar.data.filename)
                unique_filename = f"{uuid.uuid4().hex}_{picture_fn}"

                # 确保目录存在
                avatar_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars')
                if not os.path.exists(avatar_dir):
                    os.makedirs(avatar_dir, exist_ok=True)

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
                avatar_path = os.path.join(avatar_dir, unique_filename)
                img.save(avatar_path)

                # 删除旧头像（如果不是默认头像）
                if current_user.avatar != 'default_avatar.jpg':
                    old_avatar_path = os.path.join(avatar_dir, current_user.avatar)
                    if os.path.exists(old_avatar_path):
                        os.remove(old_avatar_path)

                current_user.avatar = unique_filename
            except Exception as e:
                flash(f'头像处理出错: {str(e)}', 'danger')
                return redirect(url_for('main.edit_profile'))

        # 如果昵称有变更
        if form.username.data != current_user.username:
            current_user.username = form.username.data
            current_user.nickname_last_changed = get_beijing_time()

        # 更新其他资料
        current_user.title = form.title.data

        db.session.commit()
        flash('个人资料更新成功！', 'success')
        return redirect(url_for('main.profile', username=current_user.username))

    # GET请求，填充表单
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.title.data = current_user.title
        form.email.data = current_user.email

    return render_template('profile_edit.html', title='编辑个人资料', form=form)

@main.route('/api/user/search')
def search_user():
    username = request.args.get('username', '').strip()
    
    if not username or len(username) < 2:
        return jsonify({'found': False})
    
    # 通过用户名或邮箱搜索用户
    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()
    
    if user:
        return jsonify({
            'found': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'avatar': user.avatar,
                'role': user.role,
                'title': user.title
            }
        })
    else:
        return jsonify({'found': False})
