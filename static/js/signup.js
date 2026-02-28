document.addEventListener(
    'DOMContentLoaded',
    () => {
        const form = document.getElementById('signup');
        if (form) {
            form.addEventListener(
                'submit',
                (event) => submit_signup(event.target, event)
            )
        }
    }
)

function submit_signup(form, event) {
    event.preventDefault();

    const password = form.password.value;
    const confirmPassword = document.getElementById('regConfirmPassword').value;

    if (password !== confirmPassword) {
        document.getElementById('messages').innerHTML = '<li style="color: red">Passwords do not match</li>';
        return false;
    }

    form.submit();
    return true
}