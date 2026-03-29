/**
 * Vendor product add/edit: configurable product builder (D1, D4).
 * Outputs JSON compatible with #product-config-data on product detail (see product_detail.js).
 * Form field name="config_json" — ignored by backend until wired; safe to submit.
 */
(function () {
    const slug = (s) =>
        String(s || '')
            .trim()
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-|-$/g, '') || 'opt';

    function cartesianSelections(options) {
        if (!options.length) return [];
        const ids = options.map((o) => o.valueIds);
        const out = [];
        function walk(i, acc) {
            if (i >= ids.length) {
                out.push({ ...acc });
                return;
            }
            for (const vid of ids[i]) {
                walk(i + 1, { ...acc, [options[i].optionId]: vid });
            }
        }
        walk(0, {});
        return out;
    }

    /** No placeholder SKUs: every option must have at least one value. */
    function cartesianMatrixFromState(state) {
        if (!state.options.length) return [];
        if (state.options.some((o) => !o.valueIds.length)) return [];
        return cartesianSelections(
            state.options.map((o) => ({
                optionId: o.optionId,
                valueIds: o.valueIds,
            }))
        );
    }

    function escHtml(s) {
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/"/g, '&quot;');
    }

    function buildState(root) {
        const typeInput = root.querySelector('input[name="vendor_product_type"]:checked');
        const type = typeInput ? typeInput.value : 'simple';
        const optionCards = root.querySelectorAll('.vendor-option-card');
        const options = [];
        let optIndex = 0;
        optionCards.forEach((card) => {
            const nameInput = card.querySelector('.vendor-option-name');
            const name = (nameInput && nameInput.value.trim()) || `Option ${optIndex + 1}`;
            const optionId = slug(name) + '-' + optIndex;
            const valueRows = card.querySelectorAll('.vendor-value-row');
            const values = [];
            const valueIds = [];
            let vIndex = 0;
            valueRows.forEach((row) => {
                const labelIn = row.querySelector('.vendor-value-label');
                const imgIn = row.querySelector('.vendor-value-image');
                const label = labelIn && labelIn.value.trim();
                if (!label) return;
                const image = imgIn && imgIn.value.trim() ? imgIn.value.trim() : '';
                const vid = slug(label) + '-' + optIndex + '-' + vIndex;
                values.push({ id: vid, label, image: image || undefined });
                valueIds.push(vid);
                vIndex++;
            });
            options.push({
                optionId,
                name,
                values,
                valueIds,
            });
            optIndex++;
        });
        return { type, options };
    }

    function stateToProductConfigJson(state) {
        if (state.type !== 'configurable' || !state.options.length) {
            return { options: [], variants: [] };
        }

        const optionsOut = state.options
            .filter((o) => o.values.length)
            .map((o) => {
                const hasImage = o.values.some((v) => v.image);
                return {
                    id: o.optionId,
                    label: o.name,
                    ui: hasImage ? 'swatch' : 'radio',
                    values: o.values.map((v) => {
                        const x = { id: v.id, label: v.label };
                        if (v.image) x.image = v.image;
                        return x;
                    }),
                };
            });

        const matrix = cartesianMatrixFromState(state);

        const skuRows = document.querySelectorAll('#vendor-sku-matrix-body tr[data-variant-index]');
        const variants = matrix.map((selection, idx) => {
            const row = skuRows[idx];
            let sku = '';
            let inStock = true;
            if (row) {
                const skuIn = row.querySelector('.vendor-sku-code');
                const stockIn = row.querySelector('.vendor-sku-in-stock');
                sku = skuIn ? skuIn.value.trim() : '';
                inStock = stockIn ? stockIn.checked : true;
            }
            if (!sku) {
                const parts = Object.keys(selection)
                    .sort()
                    .map((k) => selection[k]);
                sku = 'SKU-' + parts.join('-').toUpperCase().replace(/[^A-Z0-9-]/g, '-').slice(0, 64);
            }
            return { sku, inStock, selection };
        });

        return { options: optionsOut, variants };
    }

    function syncHiddenOutput(root) {
        const state = buildState(root);
        const ta = root.querySelector('#vendor-config-json-output');
        if (!ta) return;
        const json = state.type === 'simple' ? '{}' : JSON.stringify(stateToProductConfigJson(state));
        ta.value = json;
    }

    function renderSkuMatrix(root) {
        const tbody = root.querySelector('#vendor-sku-matrix-body');
        const wrap = root.querySelector('#vendor-sku-matrix-wrap');
        if (!tbody || !wrap) return;
        const state = buildState(root);
        if (state.type !== 'configurable' || !state.options.length) {
            wrap.hidden = true;
            tbody.innerHTML = '';
            return;
        }

        const matrix = cartesianMatrixFromState(state);

        if (!matrix.length) {
            wrap.hidden = true;
            tbody.innerHTML = '';
            return;
        }

        wrap.hidden = false;
        tbody.innerHTML = matrix
            .map((sel, idx) => {
                const labels = state.options
                    .map((o) => {
                        const vid = sel[o.optionId];
                        const v = o.values.find((x) => x.id === vid);
                        return v ? v.label : vid;
                    })
                    .join(' / ');
                const parts = Object.keys(sel)
                    .sort()
                    .map((k) => sel[k]);
                const autoSku =
                    'SKU-' + parts.join('-').toUpperCase().replace(/[^A-Z0-9-]/g, '-').slice(0, 64);
                return `
            <tr data-variant-index="${idx}">
                <td><input type="text" class="form-control vendor-sku-code" value="${escHtml(autoSku)}" aria-label="SKU code" /></td>
                <td>${escHtml(labels)}</td>
                <td class="inv-toggle"><label><input type="checkbox" class="vendor-sku-in-stock" checked /> In stock</label></td>
            </tr>`;
            })
            .join('');

        tbody.querySelectorAll('.vendor-sku-code, .vendor-sku-in-stock').forEach((el) => {
            el.addEventListener('input', () => syncHiddenOutput(root));
            el.addEventListener('change', () => syncHiddenOutput(root));
        });
    }

    function addOptionCard(root, name) {
        const list = root.querySelector('#vendor-options-list');
        if (!list) return;
        const card = document.createElement('div');
        card.className = 'vendor-option-card';
        card.innerHTML = `
            <div class="vendor-option-card-header">
                <label>Option name</label>
                <input type="text" class="form-control vendor-option-name" placeholder="e.g. Colour, Size" value="${(name || '').replace(/"/g, '&quot;')}" />
                <button type="button" class="btn btn-outline-danger btn-sm vendor-remove-option">Remove option</button>
            </div>
            <div class="vendor-values-list"></div>
            <button type="button" class="btn btn-outline-secondary btn-sm vendor-add-value">Add value</button>
        `;
        list.appendChild(card);

        const valuesList = card.querySelector('.vendor-values-list');
        const addValue = () => {
            const row = document.createElement('div');
            row.className = 'vendor-value-row';
            row.innerHTML = `
                <div>
                    <label class="form-label small mb-0">Value label</label>
                    <input type="text" class="form-control vendor-value-label" placeholder="e.g. White, M" />
                </div>
                <div>
                    <label class="form-label small mb-0">Swatch image URL (optional)</label>
                    <input type="url" class="form-control vendor-value-image" placeholder="https://…" />
                    <span class="form-hint">Used on the product page to show colour (D2).</span>
                </div>
                <button type="button" class="btn btn-outline-danger btn-sm vendor-remove-value">Remove</button>
            `;
            valuesList.appendChild(row);
            row.querySelectorAll('input').forEach((inp) => {
                inp.addEventListener('input', () => {
                    renderSkuMatrix(root);
                    syncHiddenOutput(root);
                });
            });
            row.querySelector('.vendor-remove-value').addEventListener('click', () => {
                row.remove();
                renderSkuMatrix(root);
                syncHiddenOutput(root);
            });
        };

        addValue();
        addValue();

        card.querySelector('.vendor-option-name').addEventListener('input', () => {
            renderSkuMatrix(root);
            syncHiddenOutput(root);
        });
        card.querySelector('.vendor-add-value').addEventListener('click', addValue);
        card.querySelector('.vendor-remove-option').addEventListener('click', () => {
            card.remove();
            renderSkuMatrix(root);
            syncHiddenOutput(root);
        });
    }

    function updatePanelVisibility(root) {
        const type = root.querySelector('input[name="vendor_product_type"]:checked');
        const panel = root.querySelector('#vendor-configurable-panel');
        const simpleNote = root.querySelector('#vendor-simple-sku-note');
        const isConfigurable = type && type.value === 'configurable';
        if (panel) panel.hidden = !isConfigurable;
        if (simpleNote) simpleNote.hidden = isConfigurable;
        if (!isConfigurable) {
            const wrap = root.querySelector('#vendor-sku-matrix-wrap');
            if (wrap) wrap.hidden = true;
        }
    }

    function refreshPreview(root) {
        const pre = root.querySelector('#vendor-json-preview-pre');
        const ta = root.querySelector('#vendor-config-json-output');
        if (pre && ta) {
            try {
                const o = JSON.parse(ta.value || '{}');
                pre.textContent = JSON.stringify(o, null, 2);
            } catch {
                pre.textContent = ta.value;
            }
        }
    }

    function copyJson(root) {
        const ta = root.querySelector('#vendor-config-json-output');
        if (!ta || !navigator.clipboard) return;
        navigator.clipboard.writeText(ta.value || '{}').then(
            () => alert('Configuration JSON copied. Paste into product detail template block product_config_data for a demo.'),
            () => alert('Copy failed.')
        );
    }

    function initRoot(root) {
        if (!root || root.dataset.vendorConfigInit === '1') return;
        root.dataset.vendorConfigInit = '1';

        const optList = root.querySelector('#vendor-options-list');
        if (optList && !optList.querySelector('.vendor-option-card')) {
            addOptionCard(root, 'Colour');
            addOptionCard(root, 'Size');
        }

        root.querySelectorAll('input[name="vendor_product_type"]').forEach((r) => {
            r.addEventListener('change', () => {
                updatePanelVisibility(root);
                renderSkuMatrix(root);
                syncHiddenOutput(root);
                refreshPreview(root);
            });
        });

        const addOptBtn = root.querySelector('#vendor-add-option');
        if (addOptBtn) {
            addOptBtn.addEventListener('click', () => {
                addOptionCard(root, '');
                renderSkuMatrix(root);
                syncHiddenOutput(root);
                refreshPreview(root);
            });
        }

        const copyBtn = root.querySelector('#vendor-copy-config-json');
        if (copyBtn) copyBtn.addEventListener('click', () => copyJson(root));

        updatePanelVisibility(root);
        renderSkuMatrix(root);
        syncHiddenOutput(root);
        refreshPreview(root);

        const prev = root.querySelector('#vendor-json-preview');
        if (prev) {
            prev.addEventListener('toggle', () => refreshPreview(root));
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('#vendor-product-config').forEach(initRoot);
    });
})();
