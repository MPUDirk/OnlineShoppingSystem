/**
 * Product detail: carousel height + optional configurable options (Block D).
 * Inject JSON in #product-config-data (template block product_config_data).
 * Empty {} = simple product (add-to-cart unchanged).
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

    const findVariant = (variants, selection, options) => {
        if (!variants || !variants.length) return null;
        if (!options || !options.length) return null;
        const complete = options.every((o) => {
            const v = selection[o.id];
            return v !== undefined && v !== null && v !== '';
        });
        if (!complete) return null;
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
        const form = document.querySelector('.add-to-cart-actions');

        if (!panel || !mount) return;

        if (options.length === 0) {
            panel.classList.add('is-hidden');
            const hiddenSku = document.getElementById('cf-product-sku-field');
            if (hiddenSku) {
                hiddenSku.disabled = true;
                hiddenSku.value = '';
            }
            const simpleInStock = cfg.simpleInStock !== false;
            const cannotCfg = cfg.cannotAddConfigurable === true;
            const canAdd = simpleInStock && !cannotCfg;
            if (addBtn) {
                addBtn.disabled = !canAdd;
                addBtn.title = canAdd
                    ? ''
                    : cannotCfg
                      ? 'No in-stock option for this configuration'
                      : 'This product is out of stock';
            }
            if (qtyInput) qtyInput.disabled = !canAdd;
            return;
        }

        panel.classList.remove('is-hidden');

        const selection = {};
        options.forEach((opt) => {
            selection[opt.id] = null;
        });

        const applyVariantUi = () => {
            const complete = options.every((o) => {
                const v = selection[o.id];
                return v !== undefined && v !== null && v !== '';
            });

            const v = complete ? findVariant(variants, selection, options) : null;

            let inStock = false;
            let stockMsg = 'Select all options to continue';
            let bannerClass = 'variant-stock-banner--pending';

            if (!complete) {
                stockMsg = 'Choose a value for each option before adding to cart';
                inStock = false;
                bannerClass = 'variant-stock-banner--pending';
            } else if (v) {
                inStock = v.inStock !== false;
                stockMsg = inStock ? 'In stock' : 'Out of stock';
                bannerClass = inStock ? 'variant-stock-banner--ok' : 'variant-stock-banner--out';
            } else if (variants.length) {
                inStock = false;
                stockMsg = 'This combination is not available';
                bannerClass = 'variant-stock-banner--out';
            } else {
                inStock = false;
                stockMsg = 'No SKU rows configured for this product';
                bannerClass = 'variant-stock-banner--out';
            }

            if (skuLine) {
                skuLine.textContent = v && v.sku ? v.sku : '—';
            }
            if (stockBanner) {
                stockBanner.hidden = false;
                stockBanner.className = 'variant-stock-banner ' + bannerClass;
                stockBanner.textContent = stockMsg;
            }
            const canAdd = complete && v && inStock;
            if (addBtn) {
                addBtn.disabled = !canAdd;
                addBtn.title = canAdd ? '' : complete && v && !inStock ? 'This configuration is out of stock' : 'Complete your selection';
            }
            if (qtyInput) qtyInput.disabled = !canAdd;

            const imageOption = options.find((o) => (o.values || []).some((val) => val.image));
            if (mainImg && imageOption && complete) {
                const sid = selection[imageOption.id];
                const val = (imageOption.values || []).find((x) => String(x.id) === String(sid));
                if (val && val.image) {
                    mainImg.src = val.image;
                    mainImg.alt = val.label || mainImg.alt;
                }
            }

            const hiddenSku = document.getElementById('cf-product-sku-field');
            if (hiddenSku) {
                if (canAdd && v && v.sku) {
                    hiddenSku.disabled = false;
                    hiddenSku.value = v.sku;
                    hiddenSku.setAttribute('name', 'product_sku');
                } else {
                    hiddenSku.disabled = true;
                    hiddenSku.value = '';
                    hiddenSku.removeAttribute('name');
                }
            }

            if (form) {
                form.setAttribute('data-selection-complete', complete ? 'true' : 'false');
            }
        };

        mount.innerHTML = '';
        options.forEach((opt) => {
            const wrap = document.createElement('div');
            wrap.className = 'product-option-group';
            const lab = document.createElement('span');
            lab.className = 'product-option-label';
            lab.textContent = opt.label || opt.id;
            lab.id = 'opt-label-' + String(opt.id).replace(/\s+/g, '-');
            const vals = document.createElement('div');
            const isSwatch = opt.ui === 'swatch';
            vals.className = 'product-option-values' + (isSwatch ? ' product-option-values--swatch' : '');
            vals.setAttribute('role', isSwatch ? 'group' : 'radiogroup');
            vals.setAttribute('aria-labelledby', lab.id);

            (opt.values || []).forEach((val) => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = isSwatch ? 'option-chip option-swatch' : 'option-chip';
                btn.setAttribute('aria-pressed', 'false');
                btn.setAttribute('aria-label', (opt.label || opt.id) + ': ' + (val.label || val.id));
                if (isSwatch && val.image) {
                    const im = document.createElement('img');
                    im.src = val.image;
                    im.alt = val.label || '';
                    btn.appendChild(im);
                } else {
                    btn.textContent = val.label || val.id;
                }

                btn.addEventListener('click', () => {
                    selection[opt.id] = val.id;
                    vals.querySelectorAll('.option-chip').forEach((b) => {
                        b.classList.remove('is-selected');
                        b.setAttribute('aria-pressed', 'false');
                    });
                    btn.classList.add('is-selected');
                    btn.setAttribute('aria-pressed', 'true');
                    applyVariantUi();
                });

                vals.appendChild(btn);
            });

            wrap.appendChild(lab);
            wrap.appendChild(vals);
            mount.appendChild(wrap);
        });

        if (form) {
            form.addEventListener('submit', (e) => {
                const complete = options.every((o) => {
                    const x = selection[o.id];
                    return x !== undefined && x !== null && x !== '';
                });
                if (!complete) {
                    e.preventDefault();
                    alert('Please select a value for every option.');
                    return;
                }
                const v = findVariant(variants, selection, options);
                if (!v || v.inStock === false) {
                    e.preventDefault();
                    alert('This configuration cannot be added (unavailable or out of stock).');
                }
            });
        }

        applyVariantUi();
    };

    /** Django-rendered radios: show option thumbnails in template; swap main image when swatch group has images. */
    const initVariantSwatchPreview = () => {
        const form = document.querySelector('.add-to-cart-actions');
        const main = document.getElementById('product-main-image');
        if (!form || !main) return;

        const applyPreview = () => {
            let url = null;
            const primary = form.querySelector(
                'fieldset[data-group-swatches="true"] input[type="radio"]:checked[data-preview-url]',
            );
            if (primary && primary.dataset.previewUrl) {
                url = primary.dataset.previewUrl;
            } else {
                const any = form.querySelector('input[type="radio"]:checked[data-preview-url]');
                if (any && any.dataset.previewUrl) url = any.dataset.previewUrl;
            }
            if (url) {
                main.src = url;
                main.alt = '';
            }
        };

        form.querySelectorAll('input[type="radio"][name^="prop_"]').forEach((el) => {
            el.addEventListener('change', applyPreview);
        });
    };

    document.addEventListener('DOMContentLoaded', () => {
        initCarousel();
        initConfigurable();
        initVariantSwatchPreview();
    });
})();
