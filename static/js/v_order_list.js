const tempForm = document.createElement('form');
tempForm.method = 'POST';

document.getElementById('confirm_btn').addEventListener(
    'click',
    (e) => {
        const csrf = document.querySelector('input[name="csrfmiddlewaretoken"]');

        tempForm.appendChild(csrf);

        document.body.appendChild(tempForm);
        tempForm.submit();
    }
)
