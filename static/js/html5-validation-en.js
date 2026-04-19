/**
 * Force English HTML5 constraint validation messages (override browser locale).
 * Use on forms: <form data-html5-lang="en" ...>
 */
(function () {
    function attachField(el) {
        if (!el.willValidate) {
            return;
        }
        el.addEventListener('invalid', function () {
            if (el.validity.valueMissing) {
                el.setCustomValidity('Please fill out this field.');
            } else if (el.type === 'email' && el.validity.typeMismatch) {
                el.setCustomValidity(
                    'Please enter a valid email address that includes an "@".'
                );
            } else if (el.validity.tooShort) {
                el.setCustomValidity('This value is too short.');
            } else if (el.validity.tooLong) {
                el.setCustomValidity('This value is too long.');
            } else if (el.validity.patternMismatch) {
                el.setCustomValidity('Please match the requested format.');
            } else {
                el.setCustomValidity('Please correct this field.');
            }
        });
        function clearCustom() {
            el.setCustomValidity('');
        }
        el.addEventListener('input', clearCustom);
        el.addEventListener('change', clearCustom);
    }

    function initForm(form) {
        form.querySelectorAll('input, textarea, select').forEach(attachField);
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('form[data-html5-lang="en"]').forEach(initForm);
    });
})();
