const cancel_btn = document.querySelectorAll('button[data-action]');
const form = document.getElementById('modal-form');

cancel_btn.forEach(btn => btn.addEventListener(
    'click',
    (e) => {
        const modal = new bootstrap.Modal(document.getElementById('exampleModal'));
        modal.show();
        form.action = btn.dataset.action;
    }
))

document.getElementById('confirm_btn').addEventListener(
    'click',
    (e) => {
        form.submit();
    }
)