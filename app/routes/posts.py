from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, session, jsonify
from flask_login import login_required, current_user
from app.models import Post, Comment, PostView, Notification, User
from app import db
import markdown
from markdown.extensions import Extension
from markdown.extensions.toc import TocExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.attr_list import AttrListExtension
from markdown.extensions.def_list import DefListExtension
from markdown.extensions.abbr import AbbrExtension
from markdown.extensions.footnotes import FootnoteExtension
from markdown.extensions.md_in_html import MarkdownInHtmlExtension
from datetime import datetime
from sqlalchemy import func
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length
from app.utils import get_beijing_time
from app.check_permissions import check_banned

posts = Blueprint('posts', __name__)

# 帖子表单
class PostForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(min=1, max=255)])
    content = TextAreaField('内容', validators=[DataRequired()])
    is_markdown = BooleanField('使用Markdown格式')
    submit = SubmitField('发布')

# 评论表单
class CommentForm(FlaskForm):
    content = TextAreaField('评论', validators=[DataRequired()])
    parent_id = HiddenField()  # 隐藏字段用于回复
    submit = SubmitField('提交评论')

# 回复表单
class ReplyForm(FlaskForm):
    content = TextAreaField('回复', validators=[DataRequired()])
    parent_id = HiddenField()
    submit = SubmitField('回复')

# 删除表单
class DeleteForm(FlaskForm):
    submit = SubmitField('删除')

@posts.route('/post/create', methods=['GET', 'POST'])
@login_required
@check_banned
def create():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            content=form.content.data,
            is_markdown=form.is_markdown.data,
            author=current_user
        )
        db.session.add(post)
        db.session.commit()
        
        flash('帖子发布成功！', 'success')
        return redirect(url_for('posts.view', post_id=post.id))
    
    return render_template('posts/create.html', title='发布新帖子', form=form)

@posts.route('/post/<int:post_id>')
def view(post_id):
    post = Post.query.get_or_404(post_id)
    
    # 解析Markdown内容
    if post.is_markdown:
        extensions = [
            'extra',  # 包含tables, footnotes等扩展
            'codehilite',
            'toc',
            'fenced_code',
            'nl2br',  # 换行转为 <br>
            AttrListExtension(),
            DefListExtension(),
            FootnoteExtension(),
            MarkdownInHtmlExtension()
        ]
        
        # 使用扩展的 Markdown 渲染
        post_content = markdown.markdown(
            post.content, 
            extensions=extensions
        )
    else:
        post_content = post.content
    
    # 记录浏览量
    # 检查会话中是否已经浏览过此帖子
    if 'viewed_posts' not in session:
        session['viewed_posts'] = []
    
    if str(post_id) not in session['viewed_posts']:
        # 增加浏览记录
        ip_address = request.remote_addr
        post_view = PostView(
            post_id=post.id, 
            user_id=current_user.id if current_user.is_authenticated else None, 
            ip_address=ip_address
        )
        db.session.add(post_view)
        
        # 增加帖子浏览计数
        post.views += 1
        db.session.commit()
        
        # 在会话中记录此次浏览
        session['viewed_posts'].append(str(post_id))
    
    # 获取顶级评论（没有父评论的评论）
    try:
        comments = Comment.query.filter_by(
            post_id=post.id, 
            parent_id=None,
            is_deleted=False
        ).order_by(Comment.created_at.asc()).all()
            
    except Exception as e:
        print(f"查询评论时出错: {e}")
        # 备用查询
        comments = Comment.query.filter_by(
            post_id=post.id, 
            parent_id=None
        ).order_by(Comment.created_at.asc()).all()
    
    # 评论表单
    form = CommentForm()
    
    return render_template(
        'posts/view.html', 
        title=post.title,
        post=post, 
        post_content=post_content, 
        comments=comments,
        form=form
    )

@posts.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
@check_banned
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    
    # 获取表单数据
    parent_id = request.form.get('parent_id')
    reply_to_user_id = request.form.get('reply_to_user_id')
    content = request.form.get('content')
    
    if not content:
        flash('评论内容不能为空', 'danger')
        return redirect(url_for('posts.view', post_id=post.id))
    
    # 处理回复逻辑
    actual_parent_id = None
    actual_reply_to_user_id = None
    
    if parent_id and parent_id.strip():
        parent_comment = Comment.query.get(int(parent_id))
        if parent_comment:
            # 如果父评论本身就是顶级评论，直接回复它
            if parent_comment.parent_id is None:
                actual_parent_id = parent_comment.id
                actual_reply_to_user_id = parent_comment.user_id
            else:
                # 如果父评论是个回复，则回复到顶级评论，但标记回复的用户
                root_comment = parent_comment.get_root_parent()
                actual_parent_id = root_comment.id
                actual_reply_to_user_id = parent_comment.user_id
    
    # 创建评论
    comment = Comment(
        content=content,
        author=current_user,
        post=post,
        parent_id=actual_parent_id,
        reply_to_user_id=actual_reply_to_user_id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    # 发送通知
    try:
        # 如果是回复评论，通知被回复的用户
        if actual_reply_to_user_id and actual_reply_to_user_id != current_user.id:
            notification = Notification(
                user_id=actual_reply_to_user_id,
                sender_id=current_user.id,
                content=f'{current_user.username} 回复了您的评论：{comment.content[:50]}...',
                type='reply',
                post_id=post.id,
                comment_id=comment.id
            )
            db.session.add(notification)
        
        # 如果是评论帖子，通知帖子作者
        if not actual_parent_id and post.user_id != current_user.id:
            notification = Notification(
                user_id=post.user_id,
                sender_id=current_user.id,
                content=f'{current_user.username} 评论了您的帖子：{comment.content[:50]}...',
                type='comment',
                post_id=post.id,
                comment_id=comment.id
            )
            db.session.add(notification)
        
        db.session.commit()
    except Exception as e:
        print(f"通知发送失败: {e}")
    
    flash('评论添加成功！', 'success')
    return redirect(url_for('posts.view', post_id=post.id))

@posts.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post = comment.post  # 获取评论所属的帖子

    # 检查权限：评论作者、管理员、站长或帖子作者可以删除
    if not (current_user.id == comment.user_id or 
            current_user.role in ['admin', 'owner'] or 
            current_user.id == post.user_id):
        abort(403)

    # 软删除评论
    comment.soft_delete()

    # 如果是帖子作者删除他人评论，发送通知
    if current_user.id == post.user_id and current_user.id != comment.user_id:
        try:
            notification = Notification(
                user_id=comment.user_id,
                sender_id=current_user.id,
                content=f'您在帖子《{post.title}》中的评论已被帖子作者删除',
                type='system'
            )
            db.session.add(notification)
            db.session.commit()
        except:
            pass

    flash('评论已删除', 'success')
    return redirect(url_for('posts.view', post_id=comment.post_id))

@posts.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(post_id):
    post = Post.query.get_or_404(post_id)
    
    # 检查当前用户是否是帖子作者
    if post.author != current_user:
        abort(403)
    
    form = PostForm()
    
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.is_markdown = form.is_markdown.data
        db.session.commit()
        
        flash('帖子更新成功！', 'success')
        return redirect(url_for('posts.view', post_id=post.id))
    
    # GET请求，填充表单
    if request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        form.is_markdown.data = post.is_markdown
    
    return render_template('posts/edit.html', title='编辑帖子', form=form, post=post)

@posts.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete(post_id):
    post = Post.query.get_or_404(post_id)
    
    # 检查当前用户是否是帖子作者
    if post.author != current_user:
        abort(403)
    
    try:
        # 首先删除所有相关的浏览记录
        PostView.query.filter_by(post_id=post.id).delete()
        
        # 然后删除帖子（这会自动删除关联的评论，如果设置了级联删除）
        db.session.delete(post)
        db.session.commit()
        
        flash('帖子已成功删除！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除帖子时出错: {str(e)}', 'danger')
    
    return redirect(url_for('main.index'))
