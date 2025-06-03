class AvatarCropper {
    constructor(options) {
        this.options = {
            containerSelector: options.containerSelector,
            inputSelector: options.inputSelector,
            previewSelector: options.previewSelector,
            cropSize: options.cropSize || 200,
            quality: options.quality || 0.8,
            onCrop: options.onCrop || function() {}
        };
        
        this.cropper = null;
        this.init();
    }
    
    init() {
        this.container = document.querySelector(this.options.containerSelector);
        this.input = document.querySelector(this.options.inputSelector);
        this.preview = document.querySelector(this.options.previewSelector);
        
        if (this.input) {
            this.input.addEventListener('change', this.handleFileSelect.bind(this));
        }
        
        // 创建裁剪模态框
        this.createCropModal();
    }
    
    createCropModal() {
        const modalHTML = `
            <div class="avatar-crop-modal" id="avatarCropModal" style="display: none;">
                <div class="crop-modal-overlay"></div>
                <div class="crop-modal-content">
                    <div class="crop-modal-header">
                        <h3><i class="fas fa-crop"></i> 裁剪头像</h3>
                        <button type="button" class="crop-close-btn" onclick="avatarCropper.closeCropModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="crop-modal-body">
                        <div class="crop-container">
                            <img id="cropImage" style="max-width: 100%; display: none;">
                        </div>
                    </div>
                    <div class="crop-modal-footer">
                        <button type="button" class="btn btn-secondary" onclick="avatarCropper.closeCropModal()">
                            <i class="fas fa-times"></i> 取消
                        </button>
                        <button type="button" class="btn btn-primary" onclick="avatarCropper.cropAndSave()">
                            <i class="fas fa-check"></i> 确认裁剪
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }
    
    handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        if (!file.type.startsWith('image/')) {
            alert('请选择图片文件！');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = (e) => {
            this.showCropModal(e.target.result);
        };
        reader.readAsDataURL(file);
    }
    
    showCropModal(imageSrc) {
        const modal = document.getElementById('avatarCropModal');
        const cropImage = document.getElementById('cropImage');
        
        cropImage.src = imageSrc;
        modal.style.display = 'flex';
        
        // 等待图片加载完成再初始化 Cropper
        cropImage.onload = () => {
            if (this.cropper) {
                this.cropper.destroy();
            }
            
            this.cropper = new Cropper(cropImage, {
                aspectRatio: 1,
                viewMode: 1,
                dragMode: 'move',
                autoCropArea: 0.8,
                restore: false,
                guides: true,
                center: true,
                highlight: false,
                cropBoxMovable: true,
                cropBoxResizable: true,
                toggleDragModeOnDblclick: false,
            });
        };
    }
    
    closeCropModal() {
        const modal = document.getElementById('avatarCropModal');
        modal.style.display = 'none';
        
        if (this.cropper) {
            this.cropper.destroy();
            this.cropper = null;
        }
        
        // 清空文件输入
        if (this.input) {
            this.input.value = '';
        }
    }
    
    cropAndSave() {
        if (!this.cropper) return;
        
        const canvas = this.cropper.getCroppedCanvas({
            width: this.options.cropSize,
            height: this.options.cropSize,
            imageSmoothingQuality: 'high'
        });
        
        // 更新预览
        const croppedDataURL = canvas.toDataURL('image/jpeg', this.options.quality);
        if (this.preview) {
            this.preview.src = croppedDataURL;
        }
        
        // 转换为 Blob 并触发回调
        canvas.toBlob((blob) => {
            this.options.onCrop(blob, croppedDataURL);
        }, 'image/jpeg', this.options.quality);
        
        this.closeCropModal();
    }
}

// 全局实例
let avatarCropper;
