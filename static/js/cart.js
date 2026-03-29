document.addEventListener('DOMContentLoaded', function() {
    const quantityInputs = document.querySelectorAll('input[name="quantity"]');

    quantityInputs.forEach(input => {
        // 监听键盘事件
        input.addEventListener('keypress', function(e) {
            // 检查是否按下了Enter键（keyCode 13）
            if (e.key === 'Enter' || e.keyCode === 13) {
                e.preventDefault();
                input.dispatchEvent(new Event('change'))
            }
        });
    });
});

function edit_submit(action, qtyInput) {
    const formEl = qtyInput && qtyInput.closest ? qtyInput.closest('form') : null;
    const csrfField = formEl ? formEl.querySelector('input[name="csrfmiddlewaretoken"]') : document.querySelector('input[name="csrfmiddlewaretoken"]');
    const quantityField = qtyInput || (formEl ? formEl.querySelector('input[name="quantity"]') : document.querySelector('input[name="quantity"]'));
    const csrf = csrfField ? csrfField.value : '';
    const quantity = quantityField ? quantityField.value : '1';

    const edit_form = document.createElement("form");
    edit_form.method = "POST";
    edit_form.action = action;

    const csrf_input = document.createElement("input");
    csrf_input.name = "csrfmiddlewaretoken";
    csrf_input.value = csrf;

    const quantity_input = document.createElement("input");
    quantity_input.name = "quantity";
    quantity_input.value = quantity;

    edit_form.appendChild(csrf_input);
    edit_form.appendChild(quantity_input);

    document.body.appendChild(edit_form);
    edit_form.submit();
}

function subtotal_change() {
    const total = document.getElementById("cart-total-price")
    const items = document.querySelectorAll("#cart-form input[name=\"items\"]:checked");
    let price = 0;

    for (let i = 0; i < items.length; i++) {
        price += parseFloat(items[i].getAttribute("data-price"));
    }

    total.innerHTML = price.toString();
}