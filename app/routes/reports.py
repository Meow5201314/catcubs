from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import Report, Post, Comment, db
from app.check_permissions import check_banned
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, RadioField
from wtforms.validators import DataRequired, Length

reports = Blueprint('reports', __name__)

class ReportForm(FlaskForm):
    reason_type = RadioField('举报原因', choices=[
        ('spam', '垃圾信息'),
        ('abuse', '辱骂/人身攻击'),
        ('inappropriate', '不当内容'),
        ('copyright', '侵权'),
        ('other', '其他')
    ], validators=[DataRequired()])
    
    reason = TextAreaField('详细说明', validators=[DataRequired(), Length(min=10, max=500)])
    submit = SubmitField('提交举报')

@reports.route('/report/post/<int:post_id>', methods=['GET', 'POST'])
@login_required
@check_banned
def report_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # 检查是否已经举报过
    existing_report = Report.query.filter_by(
        reporter_id=current_user.id,
        post_id=post_id,
        status='pending'
    ).first()
    
    if existing_report:
        flash('您已经举报过此帖子，请等待处理', 'warning')
        return redirect(url_for('posts.view', post_id=post_id))
    
    form = ReportForm()
    
    if form.validate_on_submit():
        report = Report(
            reporter_id=current_user.id,
            post_id=post_id,
            reason=f"[{form.reason_type.data}] {form.reason.data}"
        )
        db.session.add(report)
        db.session.commit()
        
        flash('举报已提交，我们会尽快处理', 'success')
        return redirect(url_for('posts.view', post_id=post_id))
    
    return render_template('reports/report.html', 
                         title='举报帖子',
                         form=form,
                         target_type='帖子',
                         target_title=post.title)

@reports.route('/report/comment/<int:comment_id>', methods=['GET', 'POST'])
@login_required
@check_banned
def report_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    # 检查是否已经举报过
    existing_report = Report.query.filter_by(
        reporter_id=current_user.id,
        comment_id=comment_id,
        status='pending'
    ).first()
    
    if existing_report:
        flash('您已经举报过此评论，请等待处理', 'warning')
        return redirect(url_for('posts.view', post_id=comment.post_id))
    
    form = ReportForm()
    
    if form.validate_on_submit():
        report = Report(
            reporter_id=current_user.id,
            comment_id=comment_id,
            reason=f"[{form.reason_type.data}] {form.reason.data}"
        )
        db.session.add(report)
        db.session.commit()
        
        flash('举报已提交，我们会尽快处理', 'success')
        return redirect(url_for('posts.view', post_id=comment.post_id))
    
    return render_template('reports/report.html', 
                         title='举报评论',
                         form=form,
                         target_type='评论',
                         target_title=comment.content[:50] + '...')
