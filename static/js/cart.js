function escCartMeta(s) {
    if (s == null) return '';
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/"/g, '&quot;');
}

/**
 * Optional cart line display (D3/D4): reads #cart-line-meta-json keyed by cart line pk.
 * Example: {"12":{"sku":"TEE-WHITE-M","configuration":"Color: White; Size: M","outOfStock":false}}
 */
function initCartLineMeta() {
    const el = document.getElementById('cart-line-meta-json');
    if (!el) return;
    let map = {};
    try {
        map = JSON.parse(el.textContent || '{}');
    } catch (e) {
        return;
    }
    document.querySelectorAll('.cart-item[data-cart-line-id]').forEach(function (row) {
        const id = row.getAttribute('data-cart-line-id');
        const meta = map[id];
        const holder = row.querySelector('[data-line-meta]');
        if (!holder || !meta) return;
        const img = row.querySelector('.cart-line-img');
        if (img && meta.imageUrl) {
            img.src = meta.imageUrl;
            img.alt = '';
        }
        const sku = meta.sku || meta.sku_code;
        const cfg = meta.configuration || meta.configuration_label || meta.config;
        var parts = [];
        if (sku) {
            parts.push('<span class="cart-sku-line"><span class="text-muted">SKU:</span> <code class="cart-sku">' + escCartMeta(sku) + '</code></span>');
        }
        if (cfg) {
            parts.push('<span class="cart-config-line">' + escCartMeta(cfg) + '</span>');
        }
        holder.innerHTML = parts.join(' ');
        if (meta.outOfStock) {
            row.classList.add('cart-item--oos');
            var note = document.createElement('p');
            note.className = 'cart-item-oos-note';
            note.textContent = 'This configuration is out of stock. Remove it before checkout (D5).';
            if (!row.querySelector('.cart-item-oos-note')) {
                holder.after(note);
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', function () {
    initCartLineMeta();
    initCheckoutOosGuard();

    const quantityInputs = document.querySelectorAll('input[name="quantity"]');
    quantityInputs.forEach(function (input) {
        input.addEventListener('keypress', function (e) {
            if (e.key === 'Enter' || e.keyCode === 13) {
                e.preventDefault();
                input.dispatchEvent(new Event('change'));
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
    const total = document.getElementById('cart-total-price');
    if (!total) return;
    const items = document.querySelectorAll('#cart-form input[name="items"]:checked');
    let price = 0;

    for (let i = 0; i < items.length; i++) {
        price += parseFloat(items[i].getAttribute('data-price'), 10) || 0;
    }

    total.textContent = price.toFixed(2);
}

/**
 * D5 optional: block checkout if JSON marks a selected line as out of stock.
 */
function initCheckoutOosGuard() {
    const form = document.getElementById('checkout-form');
    if (!form) return;
    form.addEventListener('submit', function (e) {
        const metaEl = document.getElementById('checkout-line-meta-json');
        if (!metaEl) return;
        var map = {};
        try {
            map = JSON.parse(metaEl.textContent || '{}');
        } catch (err) {
            return;
        }
        var bad = [];
        form.querySelectorAll('input[name="items"]').forEach(function (inp) {
            var m = map[inp.value];
            if (m && m.outOfStock) {
                bad.push(inp.value);
            }
        });
        if (bad.length > 0) {
            e.preventDefault();
            alert('One or more items are out of stock. Return to the cart and remove or update those lines (D5).');
        }
    });
}