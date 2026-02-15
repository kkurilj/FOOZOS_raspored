document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds (osim conflict upozorenja)
    document.querySelectorAll('.alert-dismissible').forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirm delete actions
    document.querySelectorAll('form[data-confirm]').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!confirm(form.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // Filter form auto-submit on change
    document.querySelectorAll('.filter-bar select').forEach(function(select) {
        select.addEventListener('change', function() {
            this.closest('form').submit();
        });
    });
});
