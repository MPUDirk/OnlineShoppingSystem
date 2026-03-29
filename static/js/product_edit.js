const main_image_input = (i) => {
    const add_src = document.querySelector('meta[name="add-icon"]').content;
    const csrftoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    const res = document.createElement('form');
    res.innerHTML = `
        <input type="hidden" name="csrfmiddlewaretoken" value="${csrftoken}">
        <input type="hidden" name="title" value="{{ properties.title }}">
        <input type="file" id="main_input${i}" name="image" class="d-none" accept="image/!*" onChange="handleMainPropImageUpload(this)"/>
        <label for="main_input${i}" class="position-relative" style="cursor: pointer; display: inline-block;">
            <img id="main_image${i}" src="${add_src}" alt="add_img" style="width: 50px; height: 50px; object-fit: contain;"/>
            <button id="main_add_btn${i}"
                    class="position-absolute top-0 start-100 translate-middle badge rounded-circle rounded-circle border-0 btn-success d-none"
            >
                +
            </button>
            <button id="main_del_btn${i}"
                    class="position-absolute top-0 start-100 translate-middle badge rounded-circle rounded-circle border-0 btn-danger d-none"
            >
                x
            </button>
        </label>
        <div id="main_input-group${i}">
            <input type="text" name="name" class="form-control mt-1 mb-1 p-1" data-bs-toggle="tooltip" data-bs-placement="top" title="Name" style="width: 50px; font-size: 0.75rem">
            <input type="number" name="change_value" class="form-control p-1" data-bs-toggle="tooltip" data-bs-placement="top" title="Price changes"  style="width: 50px; font-size: 0.75rem">
            <input type="text" name="sku" class="form-control p-1" data-bs-toggle="tooltip"
                                   data-bs-placement="top" title="SKU"
                                   style="width: 50px; font-size: 0.75rem">
        </div>
    `
    res.className = 'col-auto d-flex flex-column';
    res.id = `main_prop${i}`;

    return res;
}

const input_change_event = (el) => {
        el.addEventListener('change', (e) => {
            const this_number = parseInt(el.parentElement.id.charAt(el.parentElement.id.length - 1));
            document.getElementById(`main_add_btn${this_number}`).classList.remove('d-none');
            document.getElementById(`main_del_btn${this_number}`).classList.add('d-none');
            const prop = document.getElementById(`main_prop${this_number}`);
            prop.action = `/vendor/products/property/${document.querySelector('meta[name="pk"]').content}/edit/`;
        })
    };
const add_btn_event = (e) => {
    let btn = e.target;
    const this_number = parseInt(btn.id.charAt(btn.id.length - 1));
    btn.classList.add('d-none');
    document.getElementById(`main_del_btn${this_number}`).classList.remove('d-none');
    if (document.getElementById(`main_prop${this_number}`).querySelector('input[name="existed"]') === null) {
        document.getElementById('main_props').append(main_image_input(this_number + 1));
        document.getElementById(`main_add_btn${this_number + 1}`).addEventListener('click', add_btn_event);
        document.getElementById(`main_del_btn${this_number + 1}`).addEventListener('click', del_btn_event);
        document.querySelectorAll('input[data-bs-toggle="tooltip"]').forEach(input_change_event);
    }
}
const del_btn_event = (e) => {
    let btn = e.target;
    const this_number = parseInt(btn.id.charAt(btn.id.length - 1));
    document.getElementById(`main_prop${this_number}`).remove();
}

document.addEventListener('DOMContentLoaded', (e) => {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    document.getElementById('main_add_btn1').addEventListener('click', add_btn_event);
    document.getElementById('main_del_btn1').addEventListener('click', del_btn_event);
    document.querySelectorAll('input[data-bs-toggle="tooltip"]').forEach(input_change_event);

    const title_form = document.getElementById("prop_title");
    title_form.querySelectorAll("input").forEach(el => {
        el.addEventListener('change', (e) => {
            document.getElementById("delete_property_btn").classList.add("d-none");
            document.getElementById("add_property_btn").classList.remove("d-none");
            title_form.action = `/vendor/products/title/${document.querySelector('meta[name="pk"]').content}/edit/`;
        })
    })
})

function handleMainPropImageUpload(input) {
    const image_count = parseInt(input.id.charAt(input.id.length - 1));
    document.getElementById(`main_add_btn${image_count}`).classList.remove('d-none');
    document.getElementById(`main_del_btn${image_count}`).classList.add('d-none');

    if (input.files && input.files[0]) {
        const file = input.files[0];
        const reader = new FileReader();
        reader.onload = function (e) {
            const img = document.getElementById(`main_image${image_count}`);
            img.src = e.target.result;
        };

        reader.readAsDataURL(file);
    }
}