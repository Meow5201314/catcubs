from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import User, Post, Comment, Notification, Announcement, AdminLog, db
from app.utils import get_beijing_time
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired
from app.admin_logger import log_admin_action

admin_actions = Blueprint('admin_actions', __name__, url_prefix='/admin')

def owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'owner':
            flash('您没有权限访问此页面', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

class AnnouncementForm(FlaskForm):
    content = TextAreaField('公告内容', validators=[DataRequired()])
    submit = SubmitField('发布公告')

@admin_actions.route('/announcements')
@owner_required
def manage_announcements():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    form = AnnouncementForm()
    return render_template('admin/announcements.html', announcements=announcements, form=form)

@admin_actions.route('/announcements/create', methods=['POST'])
@owner_required
def create_announcement():
    form = AnnouncementForm()
    if form.validate_on_submit():
        announcement = Announcement(
            content=form.content.data,
            created_by=current_user.id
        )
        db.session.add(announcement)
        db.session.commit()
        
        # 向所有用户发送通知
        users = User.query.all()
        for user in users:
            notification = Notification(
                user_id=user.id,
                sender_id=current_user.id,
                content=f'新公告：{form.content.data[:50]}...',
                type='system'
            )
            db.session.add(notification)

        db.session.commit()
        flash('公告发布成功！', 'success')
    
    return redirect(url_for('admin_actions.manage_announcements'))

@admin_actions.route('/announcements/<int:id>/toggle', methods=['POST'])
@owner_required
def toggle_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    announcement.is_active = not announcement.is_active
    db.session.commit()
    flash('公告状态已更新', 'success')
    return redirect(url_for('admin_actions.manage_announcements'))

@admin_actions.route('/announcements/<int:id>/delete', methods=['POST'])
@owner_required
def delete_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    db.session.delete(announcement)
    db.session.commit()
    flash('公告已删除', 'success')
    return redirect(url_for('admin_actions.manage_announcements'))

@admin_actions.route('/logs')
@owner_required
def view_logs():
    page = request.args.get('page', 1, type=int)
    logs = AdminLog.query.order_by(AdminLog.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/logs.html', logs=logs)

@admin_actions.route('/stats')
@login_required
def get_stats():
    if current_user.role not in ['admin', 'owner']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # 获取今日活跃用户数
    today = datetime.now(current_app.config['TIMEZONE']).date()
    today_start = datetime.combine(today, datetime.min.time())
    today_start = current_app.config['TIMEZONE'].localize(today_start)
    
    active_users = User.query.filter(
        User.last_login >= today_start
    ).count()
    
    # 获取今日发帖数
    today_posts = Post.query.filter(
        Post.created_at >= today_start
    ).count()
    
    return jsonify({
        'active_users': active_users,
        'today_posts': today_posts,
        'server_status': 'normal'
    })
