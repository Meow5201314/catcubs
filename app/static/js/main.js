// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 闪现消息自动消失
    const flashMessages = document.querySelectorAll('.flash-message');
    if (flashMessages.length > 0) {
        flashMessages.forEach(message => {
            setTimeout(function() {
                message.style.opacity = '0';
                setTimeout(function() {
                    message.style.display = 'none';
                }, 500);
            }, 5000);
        });
    }
    
    // 为表单添加验证
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            const requiredInputs = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredInputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    const formGroup = input.closest('.form-group');
                    if (formGroup && !formGroup.querySelector('.invalid-feedback')) {
                        const feedback = document.createElement('div');
                        feedback.className = 'invalid-feedback';
                        feedback.textContent = '此字段为必填项';
                        formGroup.appendChild(feedback);
                    }
                }
            });
            
            if (!isValid) {
                event.preventDefault();
            }
        });
    });
});
