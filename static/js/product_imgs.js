const img_group = document.querySelector('div.row.g-5');
const img_input = (i) => {
    const res = document.createElement('div');
    const add_src = document.querySelector('meta[name="add-icon"]').content
    res.className = 'col-auto';

    res.innerHTML = `
        <input type="file" id="image-upload-${i}" name="image${i}" class="d-none" accept="image/!*" onChange="handleImageUpload(this)"/>
        <label for="image-upload-${i}" style="cursor: pointer; display: inline-block;">
            <img src="${add_src}" alt="add_img" style="width: 100px; height: 100px; object-fit: contain;"/>
        </label>
        <div id="preview${i}" class="position-relative d-none" style="display: inline-block;">
            <img id="image${i}" src="" alt="view_img" style="width: 100px; height: 100px; object-fit: cover;"/>
            <button type="button" id="del_img${i}"
                    class="position-absolute top-0 start-100 translate-middle badge rounded-pill border-0 btn-danger"
                    onclick="handleDelImg(${i})"
            style="cursor: pointer;">
                x
            </button>
        </div>
    `
    return res;
};

let img_inputs = [img_input(1)];
let is_end = false;

document.addEventListener(
    'DOMContentLoaded',
    (e) => {
        if (is_img_data) {
            load_img_data()
        } else {
            img_group.append(...img_inputs);
        }
    }
)

function handleImageUpload(input) {
    const label = document.querySelector(`label[for=${input.id}]`);
    const img_count = img_inputs.length;

    if (input.files && input.files[0]) {
        label.classList.add('d-none')

        const file = input.files[0];
        const reader = new FileReader();
        reader.onload = function (e) {
            const preview = document.getElementById(`preview${img_count}`);
            const img = document.getElementById(`image${img_count}`);
            img.src = e.target.result;
            preview.classList.remove('d-none');

        };
        if (img_count < 5) {
            const items = img_input(img_count + 1);
            img_inputs.push(items);
            img_group.append(items);
        } else {
            is_end = true;
        }

        reader.readAsDataURL(file);
    }
}

function handleDelImg(n) {
    const elementToRemove = img_inputs[n - 1];
    if (elementToRemove && elementToRemove.parentNode) {
        elementToRemove.remove();
    }

    img_inputs.splice(n - 1, 1);

    img_inputs.forEach((item, index) => {
        const newIndex = index + 1;

        const input = item.querySelector('input[type="file"]');
        if (input) {
            input.id = `image-upload-${newIndex}`;
            input.name = `image${newIndex}`;
        }

        const label = item.querySelector('label');
        if (label) {
            label.htmlFor = `image-upload-${newIndex}`;
        }

        const preview = item.querySelector('[id^="preview"]');
        if (preview) {
            preview.id = `preview${newIndex}`;

            const img = preview.querySelector('img');
            if (img) {
                img.id = `image${newIndex}`;
            }

            const delButton = preview.querySelector('button');
            if (delButton) {
                delButton.id = `del_img${newIndex}`;
                delButton.onclick = () => handleDelImg(newIndex);
            }
        }
    });

    if (is_end) {
        const newItem = img_input(img_inputs.length + 1);
        img_inputs.push(newItem);
        img_group.append(newItem);
        is_end = false;
    }
}

