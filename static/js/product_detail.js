const carousel = document.querySelector('.carousel');
const carousel_items = document.querySelectorAll('.carousel-item');
const imgs = document.querySelectorAll('img.d-block');

let highest = 0;
let loadedCount = 0;

const finalizeCarousel = () => {
    carousel.style.height = highest + 'px';
    carousel_items[0].classList.add('active');
};

const onImageReady = (img, index) => {
    let carouselItem = carousel_items[index];
    const height = carouselItem.clientHeight;

    if (height > 0 && height > highest) {
        highest = height;
    }

    carouselItem.classList.remove('active');
    loadedCount++;

    if (loadedCount >= imgs.length) {
        finalizeCarousel();
    }
};

document.addEventListener(
    'DOMContentLoaded',
    (e) => {
        if (!carousel || imgs.length === 0) {
            return;
        }
        imgs.forEach((img, index) => {
            if (img.complete && img.naturalHeight > 0) {
                onImageReady(img, index);
            } else {
                img.addEventListener('load', () => {
                    onImageReady(img, index);
                });
                img.addEventListener('error', () => {
                    console.warn(`图片加载失败：${img.src}`);
                    onImageReady(img, index);
                });
            }
        });

        let resizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            highest = 0;
            loadedCount = 0;
            carousel.style.height = 'auto';
            resizeTimer = setTimeout(() => {
                imgs.forEach((img, index) => {
                    onImageReady(img, index);
                });
            }, 1000);
        });
    }
);
