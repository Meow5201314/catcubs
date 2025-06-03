from functools import wraps
from flask import abort
from flask_login import current_user

def check_banned(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.is_currently_banned():
            abort(403, description="您的账号已被封禁")
        return f(*args, **kwargs)
    return decorated_function
