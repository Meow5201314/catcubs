import re
from urllib.parse import urlparse, urljoin
from flask import request, url_for
from datetime import datetime
import pytz

def is_safe_url(target):
    """检查URL是否安全"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def get_redirect_target():
    """获取安全的重定向目标"""
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target

def get_beijing_time():
    """返回当前北京时间"""
    return datetime.now(pytz.timezone('Asia/Shanghai'))

def format_datetime(dt):
    """格式化时间"""
    if dt is None:
        return ""
    
    # 直接格式化时间，不进行转换
    # 因为我们已经将MySQL时区设置为+08:00，所以数据库返回的时间已经是北京时间
    return dt.strftime('%Y-%m-%d %H:%M')
