// Main JavaScript for MoTeC Log Generator

document.addEventListener('DOMContentLoaded', function() {
    // File upload drag and drop
    const fileUploads = document.querySelectorAll('.file-upload');
    
    fileUploads.forEach(upload => {
        const input = upload.querySelector('input[type="file"]');
        const label = upload.querySelector('.file-upload-label');
        
        upload.addEventListener('click', () => input.click());
        upload.addEventListener('dragover', handleDragOver);
        upload.addEventListener('dragleave', handleDragLeave);
        upload.addEventListener('drop', handleDrop);
        
        input.addEventListener('change', handleFileSelect);
    });
    
    function handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.add('dragover');
    }
    
    function handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.remove('dragover');
    }
    
    function handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        const input = e.currentTarget.querySelector('input[type="file"]');
        
        if (files.length > 0) {
            input.files = files;
            handleFileSelect({ currentTarget: input });
        }
    }
    
    function handleFileSelect(e) {
        const input = e.currentTarget;
        const container = input.closest('.file-upload');
        const label = container.querySelector('.file-upload-label');
        
        if (input.files && input.files.length > 0) {
            const file = input.files[0];
            label.innerHTML = `
                <i class="bi bi-file-earmark-check text-success"></i>
                <div class="mt-2">
                    <strong>${file.name}</strong><br>
                    <small class="text-muted">${formatFileSize(file.size)}</small>
                </div>
            `;
        }
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Auto-hide alerts after 5 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});