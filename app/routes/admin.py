from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app, jsonify
from flask_login import login_required, current_user
from app.models import User, Post, Comment, Notification, Report, Announcement, Message, AdminLog, PostView
from app import db
from datetime import datetime, timedelta
from app.utils import get_beijing_time
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired
from app.admin_logger import log_admin_action
import markdown

admin = Blueprint('admin', __name__, url_prefix='/admin')

class BanUserForm(FlaskForm):
    ban_duration = SelectField('封禁时长', choices=[
        ('1', '1天'),
        ('3', '3天'),
        ('7', '7天'),
        ('30', '30天'),
        ('permanent', '永久封禁')
    ])
    ban_reason = TextAreaField('封禁原因', validators=[DataRequired()])
    submit = SubmitField('确认封禁')

class SetAdminForm(FlaskForm):
    submit = SubmitField('确认设置')

@admin.before_request
def check_admin():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    if current_user.role not in ['admin', 'owner']:
        abort(403)  # 权限不足

# 管理后台首页
@admin.route('/')
def index():
    # 根据当前用户权限显示不同内容
    is_owner = current_user.role == 'owner'
    
    # 统计数据
    users_count = User.query.count()
    posts_count = Post.query.count()
    
    # 尝试获取评论数，如果字段不存在则使用备用方案
    try:
        comments_count = Comment.query.filter_by(is_deleted=False).count()
    except:
        comments_count = Comment.query.count()
    
    # 尝试获取举报数，如果 Report 表不存在则设为0
    try:
        reports_count = Report.query.filter_by(status='pending').count()
    except:
        reports_count = 0
    
    return render_template('admin/index.html', 
                          users_count=users_count,
                          posts_count=posts_count,
                          comments_count=comments_count,
                          reports_count=reports_count,
                          is_owner=is_owner)

# 用户管理
@admin.route('/users')
@admin.route('/users/<int:page>')
def manage_users(page=1):
    # 根据权限获取不同用户列表
    if current_user.role == 'owner':
        users_pagination = User.query.paginate(
            page=page, per_page=10, error_out=False
        )
    else:
        # 管理员只能看普通用户
        users_pagination = User.query.filter_by(role='user').paginate(
            page=page, per_page=10, error_out=False
        )
    
    return render_template('admin/users.html', 
                         users=users_pagination.items,
                         pagination=users_pagination,
                         ban_form=BanUserForm(),
                         admin_form=SetAdminForm())

# 封禁用户
@admin.route('/users/<int:user_id>/ban', methods=['POST'])
def ban_user(user_id):
    user = User.query.get_or_404(user_id)
    form = BanUserForm()
    
    # 权限检查
    if current_user.role == 'admin' and user.role != 'user':
        flash('您没有权限对该用户执行此操作', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    if form.validate_on_submit():
        ban_duration = form.ban_duration.data
        ban_reason = form.ban_reason.data
        
        # 计算封禁结束时间
        if ban_duration == 'permanent' and current_user.role == 'owner':
            banned_until = None  # 永久封禁
        else:
            # 转换为天数
            days = int(ban_duration)
            banned_until = get_beijing_time() + timedelta(days=days)
        
        user.is_banned = True
        user.banned_until = banned_until
        user.banned_reason = ban_reason
        
        # 给用户发送通知
        try:
            notification = Notification(
                user_id=user.id,
                sender_id=current_user.id,
                content=f"您的账号已被封禁。原因: {ban_reason}",
                type='system'
            )
            db.session.add(notification)
        except:
            pass  # 如果通知系统有问题，不影响封禁功能
        
        # 添加日志记录
        log_admin_action(
                action='ban_user',
                target_type='user',
                target_id=user.id,
                details=f'封禁原因: {ban_reason}, 时长: {ban_duration}'
        )

        db.session.commit()
        
        flash(f'用户 {user.username} 已被封禁', 'success')
    else:
        flash('封禁用户失败，请检查输入信息', 'danger')
    
    return redirect(url_for('admin.manage_users'))

# 解封用户
@admin.route('/users/<int:user_id>/unban', methods=['POST'])
def unban_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # 权限检查
    if current_user.role == 'admin' and user.role != 'user':
        flash('您没有权限对该用户执行此操作', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    user.is_banned = False
    user.banned_until = None
    user.banned_reason = None
    
    # 给用户发送通知
    try:
        notification = Notification(
            user_id=user.id,
            sender_id=current_user.id,
            content="您的账号已被解封。",
            type='system'
        )
        db.session.add(notification)
    except:
        pass  # 如果通知系统有问题，不影响解封功能
    
    # 添加日志记录
    log_admin_action(
            action='unban_user',
            target_type='user',
            target_id=user.id,
            details='解除封禁'
    )

    db.session.commit()
    
    flash(f'用户 {user.username} 已被解封', 'success')
    return redirect(url_for('admin.manage_users'))

# 设置管理员
@admin.route('/users/<int:user_id>/set_admin', methods=['POST'])
def set_admin(user_id):
    if current_user.role != 'owner':
        abort(403)
    
    user = User.query.get_or_404(user_id)
    form = SetAdminForm()
    
    if form.validate_on_submit():
        if user.role == 'user':
            user.role = 'admin'
            action_text = '设为管理员'
        elif user.role == 'admin':
            user.role = 'user'
            action_text = '取消管理员'
        else:
            flash('无法修改该用户的权限', 'danger')
            return redirect(url_for('admin.manage_users'))
        
        # 给用户发送通知
        try:
            notification = Notification(
                user_id=user.id,
                sender_id=current_user.id,
                content=f"您的账号权限已被{action_text}。",
                type='system'
            )
            db.session.add(notification)
        except:
            pass  # 如果通知系统有问题，不影响权限设置
        
        db.session.commit()
        
        flash(f'用户 {user.username} 已{action_text}', 'success')
    else:
        flash('操作失败', 'danger')
    
    return redirect(url_for('admin.manage_users'))

# 管理帖子
@admin.route('/posts')
@admin.route('/posts/<int:page>')
def manage_posts(page=1):
    posts_pagination = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    
    return render_template('admin/posts.html', 
                         posts=posts_pagination.items,
                         pagination=posts_pagination)

# 删除帖子
@admin.route('/posts/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    post_title = post.title  # 添加这行，保存帖子标题
    
    try:
        # 删除帖子相关的浏览记录
        from app.models import PostView
        PostView.query.filter_by(post_id=post.id).delete()
        
        # 删除帖子相关的通知
        try:
            Notification.query.filter_by(post_id=post.id).delete()
        except:
            pass
        
        # 添加日志记录（移到删除之前）
        log_admin_action(
            action='delete_post',
            target_type='post',
            target_id=post_id,
            details=f'删除帖子: {post_title}'
        )
        
        # 删除帖子（会级联删除评论）
        db.session.delete(post)
        db.session.commit()
        
        flash('帖子已成功删除！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除帖子时出错: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_posts'))

# 管理评论
@admin.route('/comments')
@admin.route('/comments/<int:page>')
def manage_comments(page=1):
    try:
        # 尝试使用新的查询方式（检查是否有 is_deleted 字段）
        comments_pagination = Comment.query.filter_by(is_deleted=False).order_by(Comment.created_at.desc()).paginate(
            page=page, per_page=15, error_out=False
        )
    except Exception as e:
        # 如果字段不存在或有其他错误，使用旧的查询方式
        current_app.logger.warning(f"使用备用评论查询方式: {str(e)}")
        comments_pagination = Comment.query.order_by(Comment.created_at.desc()).paginate(
            page=page, per_page=15, error_out=False
        )
    
    return render_template('admin/comments.html', 
                         comments=comments_pagination.items,
                         pagination=comments_pagination)

# 删除评论
@admin.route('/comments/<int:comment_id>/delete', methods=['POST'])
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    try:
        # 检查评论是否有 is_deleted 属性
        if hasattr(comment, 'is_deleted'):
            # 使用软删除
            comment.is_deleted = True
            comment.deleted_at = get_beijing_time()
            comment.deleted_by = current_user.id
        else:
            # 如果没有软删除功能，则硬删除
            db.session.delete(comment)
        
        # 删除评论相关的通知
        try:
            Notification.query.filter_by(comment_id=comment.id).delete()
        except:
            pass
        
        # 添加日志记录
        log_admin_action(
            action='delete_comment',
            target_type='comment',
            target_id=comment_id,
            details=f'删除评论'
        )

        db.session.commit()
        flash('评论已删除', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除评论时出错: {str(e)}")
        flash(f'删除评论时出错: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_comments'))  # 这里添加缺失的右括号
            

@admin.route('/stats')
@login_required
def get_stats():
    if current_user.role not in ['admin', 'owner']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    # 获取今日活跃用户数（24小时内登录）
    now = get_beijing_time()
    today_start = now - timedelta(hours=24)
    
    active_users = User.query.filter(
        User.last_login >= today_start
    ).count()
    
    # 获取今日发帖数
    today_posts = Post.query.filter(
        Post.created_at >= today_start
    ).count()
    
    # 获取今日评论数
    try:
        today_comments = Comment.query.filter(
            Comment.created_at >= today_start,
            Comment.is_deleted == False
        ).count()
    except:
        today_comments = Comment.query.filter(
            Comment.created_at >= today_start
        ).count()
    
    return jsonify({
        'active_users': active_users,
        'today_posts': today_posts,
        'today_comments': today_comments,
        'server_status': 'normal',
        'recent_activities': []  # 可以后续添加
    })

# 修改用户昵称（站长功能）
@admin.route('/users/<int:user_id>/change_username', methods=['POST'])
def change_username(user_id):
    if current_user.role != 'owner':
        abort(403)
    
    user = User.query.get_or_404(user_id)
    new_username = request.form.get('new_username', '').strip()
    
    if not new_username:
        flash('用户名不能为空', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    # 检查用户名是否已存在
    existing_user = User.query.filter_by(username=new_username).first()
    if existing_user and existing_user.id != user_id:
        flash('该用户名已被使用', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    old_username = user.username
    user.username = new_username
    
    # 记录日志
    log_admin_action(
        action='change_username',
        target_type='user',
        target_id=user.id,
        details=f'修改用户名: {old_username} -> {new_username}'
    )
    
    db.session.commit()
    flash(f'用户名已修改为: {new_username}', 'success')
    
    return redirect(url_for('admin.manage_users'))

# 删除用户及其数据（站长功能）
@admin.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    if current_user.role != 'owner':
        flash('只有站长可以删除用户', 'danger')
        abort(403)

    user = User.query.get_or_404(user_id)

    # 不能删除自己
    if user.id == current_user.id:
        flash('不能删除自己的账号', 'danger')
        return redirect(url_for('admin.manage_users'))

    # 不能删除其他站长
    if user.role == 'owner':
        flash('不能删除其他站长账号', 'danger')
        return redirect(url_for('admin.manage_users'))

    username = user.username

    try:
        # 删除用户的所有数据
        # 1. 删除通知
        Notification.query.filter_by(user_id=user.id).delete()
        Notification.query.filter_by(sender_id=user.id).delete()

        # 2. 删除消息
        Message.query.filter_by(sender_id=user.id).delete()
        Message.query.filter_by(recipient_id=user.id).delete()

        # 3. 删除举报
        Report.query.filter_by(reporter_id=user.id).delete()

        # 4. 删除评论的回复关系
        # 先将回复给该用户的评论的 reply_to_user_id 设为 null
        Comment.query.filter_by(reply_to_user_id=user.id).update({'reply_to_user_id': None})

        # 5. 删除评论
        Comment.query.filter_by(user_id=user.id).delete()

        # 6. 删除帖子浏览记录
        PostView.query.filter_by(user_id=user.id).delete()

        # 7. 删除帖子
        Post.query.filter_by(user_id=user.id).delete()

        # 8. 删除公告（如果有）
        if hasattr(user, 'announcements'):
            Announcement.query.filter_by(created_by=user.id).delete()

        # 9. 删除管理日志（如果有）
        AdminLog.query.filter_by(admin_id=user.id).delete()

        # 10. 记录日志
        log_admin_action(
            action='delete_user',
            target_type='user',
            target_id=user.id,
            details=f'删除用户及其所有数据: {username}'
        )

        # 11. 删除用户
        db.session.delete(user)
        db.session.commit()

        flash(f'用户 {username} 及其所有数据已被删除', 'success')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'删除用户失败: {str(e)}')
        flash(f'删除用户时出错: {str(e)}', 'danger')

    return redirect(url_for('admin.manage_users'))


# 管理举报
@admin.route('/reports')
@admin.route('/reports/<int:page>')
def manage_reports(page=1):
    try:
        reports_pagination = Report.query.filter_by(status='pending').order_by(
            Report.created_at.desc()
        ).paginate(page=page, per_page=20, error_out=False)

        return render_template('admin/reports.html',
                             reports=reports_pagination.items,
                             pagination=reports_pagination)
    except Exception as e:
        # 如果 Report 表不存在，返回空页面
        return render_template('admin/reports.html',
                             reports=[],
                             pagination=None)

# 处理举报
@admin.route('/reports/<int:report_id>/resolve', methods=['POST'])
def resolve_report(report_id):
    try:
        report = Report.query.get_or_404(report_id)
        action = request.form.get('action')

        if action == 'accept':
            report.status = 'resolved'

            # 根据举报类型采取行动
            if report.post_id:
                # 删除帖子
                post = Post.query.get(report.post_id)
                if post:
                    # 删除帖子相关的浏览记录
                    PostView.query.filter_by(post_id=post.id).delete()

                    # 删除帖子相关的通知
                    Notification.query.filter_by(post_id=post.id).delete()

                    # 删除帖子（会级联删除评论）
                    db.session.delete(post)
                    flash('举报已处理，帖子已删除', 'success')

            elif report.comment_id:
                # 删除评论
                comment = Comment.query.get(report.comment_id)
                if comment:
                    if hasattr(comment, 'soft_delete'):
                        comment.soft_delete()
                    else:
                        # 如果没有软删除功能，则硬删除
                        db.session.delete(comment)
                    flash('举报已处理，评论已删除', 'success')

        elif action == 'reject':
            report.status = 'rejected'
            flash('举报已驳回', 'info')

        # 记录日志
        log_admin_action(
            action='resolve_report',
            target_type='report',
            target_id=report.id,
            details=f'处理举报: {action}'
        )

        db.session.commit()
        return redirect(url_for('admin.manage_reports'))

    except Exception as e:
        db.session.rollback()
        flash(f'处理举报时出错: {str(e)}', 'danger')
        return redirect(url_for('admin.manage_reports'))
