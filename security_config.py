# 额外的安全配置

# 1. 限制登录尝试
LOGIN_ATTEMPT_LIMIT = 5  # 5次失败后锁定
LOGIN_LOCKOUT_DURATION = 300  # 锁定5分钟

# 2. 密码复杂度要求
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPER = True
PASSWORD_REQUIRE_LOWER = True
PASSWORD_REQUIRE_DIGIT = True
PASSWORD_REQUIRE_SPECIAL = True

# 3. Session 安全
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# 4. 内容安全策略
CSP_POLICY = {
    'default-src': "'self'",
    'script-src': "'self' 'unsafe-inline' https://www.google.com https://www.gstatic.com",
    'style-src': "'self' 'unsafe-inline' https://cdnjs.cloudflare.com",
    'img-src': "'self' data: https:",
    'font-src': "'self' https://cdnjs.cloudflare.com"
}
