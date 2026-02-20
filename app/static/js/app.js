document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds (osim conflict upozorenja)
    document.querySelectorAll('.alert-dismissible').forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirm delete actions via Bootstrap modal
    var deleteModal = document.getElementById('confirmDeleteModal');
    var pendingDeleteForm = null;
    if (deleteModal) {
        var bsDeleteModal = new bootstrap.Modal(deleteModal);
        document.getElementById('confirmDeleteBtn').addEventListener('click', function() {
            if (pendingDeleteForm) {
                pendingDeleteForm.removeAttribute('data-confirm');
                pendingDeleteForm.requestSubmit();
                bsDeleteModal.hide();
                pendingDeleteForm = null;
            }
        });
        document.querySelectorAll('form[data-confirm]').forEach(function(form) {
            form.addEventListener('submit', function(e) {
                if (!form.hasAttribute('data-confirm')) return;
                e.preventDefault();
                pendingDeleteForm = form;
                var warningEl = document.getElementById('confirmDeleteWarning');
                var msgEl = document.getElementById('confirmDeleteMessage');
                var warning = form.dataset.confirmWarning;
                if (warning) {
                    warningEl.innerHTML = '<i class="bi bi-exclamation-triangle"></i> ' + warning;
                    warningEl.style.display = '';
                } else {
                    warningEl.style.display = 'none';
                }
                msgEl.textContent = form.dataset.confirm;
                bsDeleteModal.show();
            });
        });
    }

    // Filter form auto-submit on change
    document.querySelectorAll('.filter-bar select').forEach(function(select) {
        select.addEventListener('change', function() {
            this.closest('form').submit();
        });
    });

    // CSRF: auto-inject token into all POST forms on submit
    var csrfMeta = document.querySelector('meta[name="csrf-token"]');
    if (csrfMeta) {
        document.addEventListener('submit', function(e) {
            var form = e.target;
            if (form.method && form.method.toUpperCase() === 'POST') {
                if (!form.querySelector('input[name="csrf_token"]')) {
                    var input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = 'csrf_token';
                    input.value = csrfMeta.content;
                    form.appendChild(input);
                }
            }
        });
    }

    // CSRF: patch fetch() to automatically include X-CSRFToken header on POST/PUT/DELETE
    var originalFetch = window.fetch;
    window.fetch = function(url, options) {
        options = options || {};
        if (options.method && ['POST', 'PUT', 'DELETE', 'PATCH'].indexOf(options.method.toUpperCase()) !== -1) {
            var meta = document.querySelector('meta[name="csrf-token"]');
            if (meta) {
                options.headers = options.headers || {};
                if (options.headers instanceof Headers) {
                    if (!options.headers.has('X-CSRFToken')) {
                        options.headers.set('X-CSRFToken', meta.content);
                    }
                } else {
                    if (!options.headers['X-CSRFToken']) {
                        options.headers['X-CSRFToken'] = meta.content;
                    }
                }
            }
        }
        return originalFetch.call(this, url, options);
    };
});
