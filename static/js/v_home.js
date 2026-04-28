document.addEventListener('DOMContentLoaded', () => {
    const modalEl = document.getElementById('exampleModal');
    const confirmBtn = document.getElementById('confirm_btn');
    const form = document.getElementById('vendor-delete-product-form');
    const deleteBtns = document.querySelectorAll('.vendor-product-delete-btn');

    if (!modalEl || !confirmBtn || !form || deleteBtns.length === 0) {
        return;
    }

    const modal = new bootstrap.Modal(modalEl);
    let pendingDeleteUrl = '';

    deleteBtns.forEach((btn) => {
        btn.addEventListener('click', () => {
            pendingDeleteUrl = btn.getAttribute('data-delete-url');
            modal.show();
        });
    });

    confirmBtn.addEventListener('click', () => {
        if (!pendingDeleteUrl) {
            return;
        }
        form.action = pendingDeleteUrl;
        form.submit();
        pendingDeleteUrl = '';
    });
});
