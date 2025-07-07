document.addEventListener('DOMContentLoaded', function () {
    const weightInput = document.querySelector('input[name="weight"]');
    const volumeInput = document.querySelector('input[name="volume"]');
    const densityInput = document.querySelector('input[name="density"]');

    function calculateDensity() {
        const weight = parseFloat(weightInput.value.replace(',', '.'));
        const volume = parseFloat(volumeInput.value.replace(',', '.'));

        if (!isNaN(weight) && !isNaN(volume) && volume !== 0) {
            const density = weight / volume;
            densityInput.value = density.toFixed(2);  // округление до 2 знаков
        } else {
            densityInput.value = '';
        }
    }

    weightInput.addEventListener('input', calculateDensity);
    volumeInput.addEventListener('input', calculateDensity);
});