(function () {
    const form = document.getElementById('vendor-product-form');
    if (!form) return;
    const input = form.querySelector('input[type="file"][name="thumbnail"]');
    const btn = document.getElementById('product-thumbnail-choose-btn');
    const status = document.getElementById('product-thumbnail-filename');
    if (!input || !btn || !status) return;
    btn.addEventListener('click', function () {
        input.click();
    });
    input.addEventListener('change', function () {
        status.textContent =
            input.files && input.files.length ? input.files[0].name : 'No file chosen';
    });
})();
