from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from app.utils import get_beijing_time

def beijing_time():
    """返回北京时间"""
    from flask import current_app
    return datetime.now(current_app.config['TIMEZONE'])

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.String(255), default='default_avatar.jpg')
    title = db.Column(db.String(50), nullable=True)
    registration_date = db.Column(db.DateTime, default=get_beijing_time)
    last_login = db.Column(db.DateTime)
    role = db.Column(db.String(20), default='user')  # 'user', 'admin', 'owner'
    is_banned = db.Column(db.Boolean, default=False)
    banned_until = db.Column(db.DateTime, nullable=True)
    banned_reason = db.Column(db.Text, nullable=True)
    nickname_last_changed = db.Column(db.DateTime, nullable=True)

    # 邮箱验证相关
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100), nullable=True)
    email_verification_sent_at = db.Column(db.DateTime, nullable=True)

    # 用户删除相关
    delete_requested_at = db.Column(db.DateTime, nullable=True)
    delete_confirmed = db.Column(db.Boolean, default=False)
    
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    # 修改这里，增加foreign_keys参数指定使用哪个外键
    comments = db.relationship('Comment', backref='author', lazy='dynamic', foreign_keys='Comment.user_id')
    # 定义接收回复的关系，但不再使用反向引用，因为我们会在Comment中定义
    received_replies = db.relationship('Comment', lazy='dynamic', foreign_keys='Comment.reply_to_user_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

    def can_change_nickname(self):
        """检查用户是否可以更改昵称（一个月只能改一次）"""
        if not self.nickname_last_changed:
            return True

        from flask import current_app
        now = datetime.now(current_app.config['TIMEZONE'])
        one_month_ago = now - timedelta(days=30)
        return self.nickname_last_changed < one_month_ago

    def is_currently_banned(self):
        """检查用户是否当前被封禁"""
        if not self.is_banned:
            return False
        if not self.banned_until:
            return True # 永久封禁

        from flask import current_app
        from app.utils import get_beijing_time

        # 使用相同的时区进行比较
        now = get_beijing_time()

        # 确保 banned_until 也有时区信息
        if self.banned_until.tzinfo is None:
            # 如果 banned_until 没有时区信息，假设它是北京时间
            import pytz
            beijing_tz = pytz.timezone('Asia/Shanghai')
            banned_until_with_tz = beijing_tz.localize(self.banned_until)
        else:
            banned_until_with_tz = self.banned_until

        return now < banned_until_with_tz

    @property
    def unread_notifications_count(self):
        """获取用户未读通知数量"""
        try:
            return Notification.query.filter_by(user_id=self.id, is_read=False).count()
        except:
            return 0

    @property
    def unread_messages_count(self):
        """获取用户未读私信数量"""
        try:
            return Message.query.filter_by(recipient_id=self.id, is_read=False).count()
        except:
            return 0

    def generate_email_token(self):
        """生成邮箱验证令牌"""
        import secrets
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_sent_at = get_beijing_time()
        return self.email_verification_token

    def is_active_user(self):
        """检查用户是否可以执行操作（未封禁且邮箱已验证）"""
        return not self.is_currently_banned() and self.email_verified

class Post(db.Model):
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_markdown = db.Column(db.Boolean, default=True)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=get_beijing_time)
    updated_at = db.Column(db.DateTime, default=get_beijing_time, onupdate=get_beijing_time)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    
    reports = db.relationship('Report', backref='post', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Post {self.title}>'

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=get_beijing_time)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False, server_default='0')
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    reply_to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 新增：回复的用户ID
    
    # 建立关系
    replies = db.relationship('Comment', 
                             backref=db.backref('parent', remote_side=[id]), 
                             lazy='dynamic',
                             cascade='all, delete-orphan')
    
    reply_to_user = db.relationship('User', 
                                  foreign_keys=[reply_to_user_id],
                                  overlaps="received_replies")
    
    def __repr__(self):
        return f'<Comment {self.id}>'
    
    def get_display_content(self):
        """获取显示内容（如果已删除显示特殊信息）"""
        if getattr(self, 'is_deleted', False):
            return "该评论已被删除"
        return self.content
    
    def soft_delete(self):
        """软删除评论"""
        self.is_deleted = True
        self.deleted_at = get_beijing_time()
        db.session.commit()
    
    def get_replies_with_replies(self):
        """获取所有回复（包括回复的回复），按时间排序"""
        try:
            # 获取所有子级评论，无论层级，都放在同一层显示
            all_replies = []
            
            # 获取直接回复
            direct_replies = self.replies.filter_by(is_deleted=False).all()
            
            for reply in direct_replies:
                all_replies.append(reply)
                # 获取这个回复的所有回复，但不递归，都放在同一层
                sub_replies = reply.replies.filter_by(is_deleted=False).all()
                all_replies.extend(sub_replies)
            
            # 按时间排序
            all_replies.sort(key=lambda x: x.created_at)
            return all_replies
            
        except:
            # 如果 is_deleted 字段不存在，使用备用方案
            all_replies = []
            direct_replies = self.replies.all()
            
            for reply in direct_replies:
                all_replies.append(reply)
                sub_replies = reply.replies.all()
                all_replies.extend(sub_replies)
            
            all_replies.sort(key=lambda x: x.created_at)
            return all_replies
    
    def get_root_parent(self):
        """获取根评论（顶级评论）"""
        if self.parent_id is None:
            return self
        else:
            parent = Comment.query.get(self.parent_id)
            if parent and parent.parent_id is None:
                return parent
            elif parent:
                return parent.get_root_parent()
        return self
    
    @property
    def reply_count(self):
        """获取所有回复数量（包括回复的回复）"""
        try:
            return len(self.get_replies_with_replies())
        except:
            return self.replies.count()

class PostView(db.Model):
    __tablename__ = 'post_views'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    ip_address = db.Column(db.String(45), nullable=False)
    viewed_at = db.Column(db.DateTime, default=get_beijing_time)
    
    post = db.relationship('Post', backref=db.backref('views_details', lazy='dynamic', passive_deletes=True))
    
    def __repr__(self):
        return f'<PostView {self.id}>'

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    type = db.Column(db.String(20), nullable=False)  # 'comment', 'reply', 'system'
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=get_beijing_time)

    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('notifications', lazy='dynamic'))
    sender = db.relationship('User', foreign_keys=[sender_id])

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_beijing_time)

    sender = db.relationship('User', foreign_keys=[sender_id])
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref=db.backref('messages', lazy='dynamic'))

class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'resolved', 'rejected'
    created_at = db.Column(db.DateTime, default=get_beijing_time)

    reporter = db.relationship('User', foreign_keys=[reporter_id])

class Announcement(db.Model):
    __tablename__ = 'announcements'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    is_markdown = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_beijing_time)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    author = db.relationship('User', backref='announcements')

            
class AdminLog(db.Model):
    __tablename__ = 'admin_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    target_type = db.Column(db.String(50))
    target_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=get_beijing_time)

    admin = db.relationship('User', foreign_keys=[admin_id])

    def __repr__(self):
        return f'<AdminLog {self.id}: {self.action}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
