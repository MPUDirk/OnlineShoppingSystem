document.addEventListener(
    'submit',
    (e) =>{
        const password = document.querySelector('input[name="password"]').value;
        const confirm_password = document.querySelector('input[name="confirm_password"]').value;
        if (password !== confirm_password) {
            e.preventDefault();
            const li = document.createElement('li');
            li.innerText = 'Passwords do not match';
            li.style.color = 'red';
            document.getElementById('messages').appendChild(li);
        }
    }
)