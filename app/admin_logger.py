from app import db
from app.models import AdminLog
from flask_login import current_user

def log_admin_action(action, target_type=None, target_id=None, details=None):
    """记录管理员操作"""
    if not current_user.is_authenticated or current_user.role not in ['admin', 'owner']:
        return
    
    log = AdminLog(
        admin_id=current_user.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details
    )
    db.session.add(log)
    db.session.commit()
