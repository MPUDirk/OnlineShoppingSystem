/**
 * Product detail: carousel height + optional configurable options (Block D).
 * Backend: inject JSON in #product-config-data (override template block product_config_data).
 * Empty {} = simple product (existing add-to-cart only).
 */
(function () {
    const parseConfig = () => {
        const el = document.getElementById('product-config-data');
        if (!el || !el.textContent.trim()) return {};
        try {
            return JSON.parse(el.textContent);
        } catch (e) {
            console.warn('product-config-data JSON parse failed', e);
            return {};
        }
    };

    const initCarousel = () => {
        const carousel = document.querySelector('.carousel');
        const carousel_items = document.querySelectorAll('.carousel-item');
        const imgs = document.querySelectorAll('img.d-block');

        let highest = 0;
        let loadedCount = 0;

        const finalizeCarousel = () => {
            if (!carousel || !carousel_items.length) return;
            carousel.style.height = highest + 'px';
            carousel_items.forEach((el, i) => el.classList.toggle('active', i === 0));
        };

        const onImageReady = (img, index) => {
            const carouselItem = carousel_items[index];
            if (!carouselItem) return;
            const height = carouselItem.clientHeight;
            if (height > 0 && height > highest) highest = height;
            carouselItem.classList.remove('active');
            loadedCount++;
            if (loadedCount >= imgs.length) finalizeCarousel();
        };

        if (!carousel || imgs.length === 0) return;

        imgs.forEach((img, index) => {
            if (img.complete && img.naturalHeight > 0) {
                onImageReady(img, index);
            } else {
                img.addEventListener('load', () => onImageReady(img, index));
                img.addEventListener('error', () => {
                    console.warn('Image failed:', img.src);
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
                imgs.forEach((img, index) => onImageReady(img, index));
            }, 400);
        });
    };

    const findVariant = (variants, selection) => {
        if (!variants || !variants.length) return null;
        return (
            variants.find((v) => {
                const sel = v.selection || {};
                return Object.keys(selection).every((k) => String(sel[k]) === String(selection[k]));
            }) || null
        );
    };

    const initConfigurable = () => {
        const cfg = parseConfig();
        const options = cfg.options || [];
        const variants = cfg.variants || [];
        const mount = document.getElementById('product-option-mount');
        const panel = document.getElementById('product-config-panel');
        const mainImg = document.getElementById('product-main-image');
        const skuLine = document.getElementById('product-sku-display');
        const stockBanner = document.getElementById('variant-stock-banner');
        const addBtn = document.getElementById('product-add-cart-btn');
        const qtyInput = document.getElementById('quantity');

        if (!panel || !mount || options.length === 0) {
            if (panel) panel.classList.add('is-hidden');
            return;
        }

        panel.classList.remove('is-hidden');

        const selection = {};
        options.forEach((opt) => {
            const first = opt.values && opt.values[0];
            if (first) selection[opt.id] = first.id;
        });

        const applyVariantUi = () => {
            const v = findVariant(variants, selection);
            let inStock = false;
            let stockMsg = 'Out of stock';
            if (v) {
                inStock = v.inStock !== false;
                stockMsg = inStock ? 'In stock' : 'Out of stock';
            } else if (options.length && variants.length) {
                inStock = false;
                stockMsg = 'This combination is not available';
            } else if (options.length && !variants.length) {
                inStock = false;
                stockMsg = 'No variants configured';
            }

            if (skuLine) {
                skuLine.textContent = v && v.sku ? v.sku : '—';
            }
            if (stockBanner) {
                stockBanner.hidden = false;
                stockBanner.className = 'variant-stock-banner ' + (inStock ? 'variant-stock-banner--ok' : 'variant-stock-banner--out');
                stockBanner.textContent = stockMsg;
            }
            if (addBtn) {
                addBtn.disabled = !inStock;
                addBtn.title = inStock ? '' : 'This configuration is unavailable';
            }
            if (qtyInput) qtyInput.disabled = !inStock;

            // Optional: swap main image from first option that defines images (e.g. colour)
            const imageOption = options.find((o) => (o.values || []).some((val) => val.image));
            if (mainImg && imageOption) {
                const sid = selection[imageOption.id];
                const val = (imageOption.values || []).find((x) => String(x.id) === String(sid));
                if (val && val.image) {
                    mainImg.src = val.image;
                    mainImg.alt = val.label || mainImg.alt;
                }
            }

            const hiddenSku = document.getElementById('cf-product-sku-field');
            if (hiddenSku) {
                hiddenSku.value = v && v.sku ? v.sku : '';
            }
        };

        mount.innerHTML = '';
        options.forEach((opt) => {
            const wrap = document.createElement('div');
            wrap.className = 'product-option-group';
            const lab = document.createElement('span');
            lab.className = 'product-option-label';
            lab.textContent = opt.label || opt.id;
            const vals = document.createElement('div');
            const isSwatch = opt.ui === 'swatch';
            vals.className = 'product-option-values' + (isSwatch ? ' product-option-values--swatch' : '');

            (opt.values || []).forEach((val) => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = isSwatch ? 'option-chip option-swatch' : 'option-chip';
                btn.setAttribute('aria-pressed', String(selection[opt.id] === val.id));
                if (isSwatch && val.image) {
                    const im = document.createElement('img');
                    im.src = val.image;
                    im.alt = val.label || '';
                    btn.appendChild(im);
                } else {
                    btn.textContent = val.label || val.id;
                }
                if (String(selection[opt.id]) === String(val.id)) btn.classList.add('is-selected');

                btn.addEventListener('click', () => {
                    selection[opt.id] = val.id;
                    vals.querySelectorAll('.option-chip').forEach((b) => b.classList.remove('is-selected'));
                    btn.classList.add('is-selected');
                    applyVariantUi();
                });

                vals.appendChild(btn);
            });

            wrap.appendChild(lab);
            wrap.appendChild(vals);
            mount.appendChild(wrap);
        });

        applyVariantUi();
    };

    document.addEventListener('DOMContentLoaded', () => {
        initCarousel();
        initConfigurable();
    });
})();
