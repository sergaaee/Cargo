document.addEventListener('DOMContentLoaded', function () {
    const resetButton = document.getElementById('reset-button');
    const form = document.querySelector('form');

    const initialState = {};
    form.querySelectorAll('input, select').forEach(el => {
        initialState[el.name] = el.value;
    });

    resetButton.addEventListener('click', () => {
        form.querySelectorAll('input, select').forEach(el => {
            if (initialState.hasOwnProperty(el.name)) {
                el.value = initialState[el.name];
            }
        });

        const event = new Event('input', {bubbles: true});
        form.querySelectorAll('input, select').forEach(el => el.dispatchEvent(event));
    });
});