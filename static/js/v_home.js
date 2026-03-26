const del_btn = document.querySelector('button[data-action]');
const confirm_btn = document.getElementById('confirm_btn');

const temp_form = document.createElement('form');


del_btn.addEventListener(
    'click',
    (e) => {
        const modal = new bootstrap.Modal(document.getElementById('exampleModal'));

        modal.show();

        temp_form.method = 'POST';
        temp_form.action = del_btn.dataset.action;

        const csrf_token = document.querySelector('input[name="csrfmiddlewaretoken"]');
        temp_form.appendChild(csrf_token);
    }
)

confirm_btn.addEventListener(
    'click',
    (e) => {
        document.appendChild(temp_form);
        temp_form.submit();
    }
)