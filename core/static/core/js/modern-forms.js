// Modern Forms JavaScript - Q360 Layihəsi
// Real-time validation və interaktiv UI funksionallığı

document.addEventListener('DOMContentLoaded', function() {
    
    // === FORM VALİDASİYASI ===
    
    // Real-time validation
    const forms = document.querySelectorAll('.modern-form');
    forms.forEach(form => {
        // Form sahələrində real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', validateField);
            input.addEventListener('input', debounce(validateField, 500));
        });
        
        // Form göndərmə zamanı tam validation
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
                showNotification('Zəhmət olmasa bütün sahələri düzgün doldurun', 'error');
            }
        });
    });
    
    function validateField() {
        const field = this;
        const value = field.value.trim();
        const fieldType = field.type;
        const required = field.hasAttribute('required');
        
        // Validation qaydaları
        let isValid = true;
        let errorMessage = '';
        
        if (required && !value) {
            isValid = false;
            errorMessage = 'Bu sahə mütləqdir';
        } else if (value) {
            switch (fieldType) {
                case 'email':
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (!emailRegex.test(value)) {
                        isValid = false;
                        errorMessage = 'Düzgün e-poçt ünvanı daxil edin';
                    }
                    break;
                    
                case 'tel':
                    const phoneRegex = /^[\+]?[0-9\s\-\(\)]{10,}$/;
                    if (!phoneRegex.test(value)) {
                        isValid = false;
                        errorMessage = 'Düzgün telefon nömrəsi daxil edin';
                    }
                    break;
                    
                case 'password':
                    if (value.length < 8) {
                        isValid = false;
                        errorMessage = 'Şifrə ən azı 8 simvol olmalıdır';
                    }
                    break;
            }
            
            // Username yoxlanması
            if (field.name === 'username' && value.length < 3) {
                isValid = false;
                errorMessage = 'İstifadəçi adı ən azı 3 simvol olmalıdır';
            }
        }
        
        // Visual feedback
        updateFieldValidation(field, isValid, errorMessage);
        
        return isValid;
    }
    
    function updateFieldValidation(field, isValid, errorMessage) {
        const formGroup = field.closest('.form-group');
        
        // Köhnə error mesajlarını sil
        const existingError = formGroup.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }
        
        // CSS sinifləri yenilə
        field.classList.remove('is-valid', 'is-invalid');
        
        if (isValid) {
            field.classList.add('is-valid');
        } else {
            field.classList.add('is-invalid');
            
            // Error mesajı əlavə et
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.style.color = '#ef4444';
            errorDiv.style.fontSize = '0.825rem';
            errorDiv.style.marginTop = '0.25rem';
            errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${errorMessage}`;
            
            formGroup.appendChild(errorDiv);
        }
    }
    
    function validateForm(form) {
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        let isFormValid = true;
        
        inputs.forEach(input => {
            if (!validateField.call(input)) {
                isFormValid = false;
            }
        });
        
        return isFormValid;
    }
    
    // === PASSWORD TOGGLE ===
    
    // Şifrə göstərmə/gizlətmə funksionallığı
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        if (input.dataset.toggle === 'password') {
            addPasswordToggle(input);
        }
    });
    
    function addPasswordToggle(input) {
        const wrapper = document.createElement('div');
        wrapper.className = 'input-group';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        
        const toggleButton = document.createElement('button');
        toggleButton.type = 'button';
        toggleButton.className = 'btn btn-outline-secondary';
        toggleButton.innerHTML = '<i class="fas fa-eye"></i>';
        toggleButton.addEventListener('click', function() {
            const type = input.type === 'password' ? 'text' : 'password';
            input.type = type;
            this.innerHTML = type === 'password' ? '<i class="fas fa-eye"></i>' : '<i class="fas fa-eye-slash"></i>';
        });
        
        const appendDiv = document.createElement('div');
        appendDiv.className = 'input-group-append';
        appendDiv.appendChild(toggleButton);
        wrapper.appendChild(appendDiv);
    }
    
    // === FILE UPLOAD ENHANCEMENTs ===
    
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        enhanceFileInput(input);
    });
    
    function enhanceFileInput(input) {
        const wrapper = document.createElement('div');
        wrapper.className = 'file-upload-wrapper';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        
        const dropZone = document.createElement('div');
        dropZone.className = 'file-drop-zone';
        dropZone.innerHTML = `
            <div class="drop-zone-content">
                <i class="fas fa-cloud-upload-alt fa-2x mb-2"></i>
                <p>Faylı buraya sürüşdürün və ya <span class="text-primary">seçin</span></p>
                <small class="text-muted">Max ölçü: 10MB</small>
            </div>
        `;
        
        wrapper.insertBefore(dropZone, input);
        
        // Drag & Drop functionality
        dropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('drag-over');
        });
        
        dropZone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');
        });
        
        dropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                input.files = files;
                updateFileDisplay(input, files[0]);
            }
        });
        
        // Click to select
        dropZone.addEventListener('click', function() {
            input.click();
        });
        
        // File seçim zamanı
        input.addEventListener('change', function() {
            if (this.files.length > 0) {
                updateFileDisplay(this, this.files[0]);
            }
        });
    }
    
    function updateFileDisplay(input, file) {
        const wrapper = input.closest('.file-upload-wrapper');
        const dropZone = wrapper.querySelector('.file-drop-zone');
        
        dropZone.innerHTML = `
            <div class="selected-file">
                <i class="fas fa-file fa-2x mb-2"></i>
                <p><strong>${file.name}</strong></p>
                <small class="text-muted">${formatFileSize(file.size)}</small>
                <button type="button" class="btn btn-sm btn-outline-danger mt-2" onclick="clearFileInput(this)">
                    <i class="fas fa-trash"></i> Sil
                </button>
            </div>
        `;
    }
    
    // === SELECT ENHANCEMENTs ===
    
    const selectInputs = document.querySelectorAll('select[data-live-search="true"]');
    selectInputs.forEach(select => {
        enhanceSelect(select);
    });
    
    function enhanceSelect(select) {
        // Bootstrap Select kitabxanası yoxdursa sadə search əlavə et
        if (!window.jQuery || !jQuery.fn.selectpicker) {
            addSimpleSearch(select);
        }
    }
    
    function addSimpleSearch(select) {
        const wrapper = document.createElement('div');
        wrapper.className = 'select-search-wrapper';
        select.parentNode.insertBefore(wrapper, select);
        
        const searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.className = 'form-control mb-2';
        searchInput.placeholder = 'Axtarış...';
        
        const originalOptions = Array.from(select.options);
        
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            
            // Bütün option-ları sil
            select.innerHTML = '';
            
            // Filtrlənmiş option-ları əlavə et
            originalOptions.forEach(option => {
                if (option.text.toLowerCase().includes(searchTerm)) {
                    select.appendChild(option.cloneNode(true));
                }
            });
        });
        
        wrapper.appendChild(searchInput);
        wrapper.appendChild(select);
    }
    
    // === FORM PROGRESS ===
    
    // Multi-step formlar üçün progress bar
    const multiStepForms = document.querySelectorAll('.multi-step-form');
    multiStepForms.forEach(form => {
        initializeMultiStepForm(form);
    });
    
    function initializeMultiStepForm(form) {
        const steps = form.querySelectorAll('.form-step');
        const progressBar = createProgressBar(steps.length);
        form.insertBefore(progressBar, form.firstChild);
        
        let currentStep = 0;
        showStep(currentStep);
        
        function showStep(stepIndex) {
            steps.forEach((step, index) => {
                step.style.display = index === stepIndex ? 'block' : 'none';
            });
            updateProgress(stepIndex + 1, steps.length);
        }
        
        function updateProgress(current, total) {
            const progress = (current / total) * 100;
            const progressBar = form.querySelector('.progress-bar');
            progressBar.style.width = progress + '%';
            progressBar.textContent = `Addım ${current}/${total}`;
        }
    }
    
    // === KÖMƏKÇİ FUNKSİYALAR ===
    
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    function showNotification(message, type = 'info') {
        // Toast notification göstər
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fas fa-${getToastIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Animasiya ilə göstər
        setTimeout(() => toast.classList.add('show'), 100);
        
        // 5 saniyə sonra sil
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }
    
    function getToastIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || icons.info;
    }
    
    function createProgressBar(totalSteps) {
        const progressContainer = document.createElement('div');
        progressContainer.className = 'progress mb-4';
        progressContainer.innerHTML = `
            <div class="progress-bar" role="progressbar" style="width: 0%">
                Addım 0/${totalSteps}
            </div>
        `;
        return progressContainer;
    }
    
    // === GLOBAL FUNKSİYALAR ===
    
    window.clearFileInput = function(button) {
        const wrapper = button.closest('.file-upload-wrapper');
        const input = wrapper.querySelector('input[type="file"]');
        const dropZone = wrapper.querySelector('.file-drop-zone');
        
        input.value = '';
        dropZone.innerHTML = `
            <div class="drop-zone-content">
                <i class="fas fa-cloud-upload-alt fa-2x mb-2"></i>
                <p>Faylı buraya sürüşdürün və ya <span class="text-primary">seçin</span></p>
                <small class="text-muted">Max ölçü: 10MB</small>
            </div>
        `;
    };
    
    // === TEXTAREA AUTO-RESIZE ===
    
    const textareas = document.querySelectorAll('textarea[data-autosize="true"]');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    });
    
});

// CSS də Toast notification stilləri
const toastCSS = `
    .toast-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        z-index: 9999;
        transform: translateX(100%);
        transition: transform 0.3s ease-in-out;
    }
    
    .toast-notification.show {
        transform: translateX(0);
    }
    
    .toast-success { background: #10b981; }
    .toast-error { background: #ef4444; }
    .toast-warning { background: #f59e0b; }
    .toast-info { background: #3b82f6; }
    
    .toast-content {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .file-drop-zone {
        border: 2px dashed #d1d5db;
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
    }
    
    .file-drop-zone:hover, .file-drop-zone.drag-over {
        border-color: #667eea;
        background-color: #f7faff;
    }
    
    .selected-file {
        padding: 1rem;
        text-align: center;
    }
`;

// CSS-i səhifəyə əlavə et
const style = document.createElement('style');
style.textContent = toastCSS;
document.head.appendChild(style);