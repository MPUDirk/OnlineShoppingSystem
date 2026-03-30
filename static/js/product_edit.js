/**
 * Optional: legacy dynamic property UI removed — attribute types are server-rendered.
 * Keeps product image gallery behaviour from product_imgs.js only when present.
 */
document.addEventListener('DOMContentLoaded', () => {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl));
});

function handleMainPropImageUpload(input) {
    const image_count = parseInt(input.id.charAt(input.id.length - 1), 10);
    const addBtn = document.getElementById(`main_add_btn${image_count}`);
    const delBtn = document.getElementById(`main_del_btn${image_count}`);
    const imgEl = document.getElementById(`main_image${image_count}`);
    if (addBtn) addBtn.classList.remove('d-none');
    if (delBtn) delBtn.classList.add('d-none');

    if (input.files && input.files[0] && imgEl) {
        const reader = new FileReader();
        reader.onload = function (e) {
            imgEl.src = e.target.result;
        };
        reader.readAsDataURL(input.files[0]);
    }
}
