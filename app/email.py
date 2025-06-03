from flask import current_app, render_template
from flask_mail import Mail, Message
from threading import Thread
import os

mail = Mail()

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, text_body=None, html_body=None):
    msg = Message(
        subject=f"[喵崽社区] {subject}",
        recipients=recipients,
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    
    if text_body:
        msg.body = text_body
    if html_body:
        msg.html = html_body
    
    # 异步发送
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()

def send_verification_email(user):
    """发送验证邮件"""
    token = user.generate_email_token()
    
    verify_url = f"http://catcubs.xyz/verify-email/{token}"
    
    html_body = f"""
    <h2>欢迎加入喵崽社区！</h2>
    <p>亲爱的 {user.username}，</p>
    <p>请点击下面的链接验证您的邮箱地址：</p>
    <p><a href="{verify_url}" style="background-color: #f4a261; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">验证邮箱</a></p>
    <p>或复制以下链接到浏览器：</p>
    <p>{verify_url}</p>
    <p>此链接24小时内有效。</p>
    <p>如果这不是您的操作，请忽略此邮件。</p>
    <br>
    <p>喵崽社区团队</p>
    """
    
    text_body = f"""
    欢迎加入喵崽社区！
    
    亲爱的 {user.username}，
    
    请访问以下链接验证您的邮箱地址：
    {verify_url}
    
    此链接24小时内有效。
    
    如果这不是您的操作，请忽略此邮件。
    
    喵崽社区团队
    """
    
    send_email(
        subject="请验证您的邮箱",
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body
    )
