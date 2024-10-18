document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector('form');
    const cancelButton = document.querySelector('.btn-secondary');

    form.addEventListener('submit', function () {
        var trackerInventoryMap = JSON.parse(localStorage.getItem('trackerInventoryMap')) || {};
        var trackerCodes = Object.keys(trackerInventoryMap);
        var inventoryNumbers = Object.values(trackerInventoryMap);

        const trackerCodesInput = document.getElementById('selected-trackers-input')
        if (trackerCodesInput) {
            trackerCodesInput.value = trackerCodes.join(',');
        }

        const selectedInventoryInput = document.getElementById('selected-inventory-input');
        if (selectedInventoryInput) {
            selectedInventoryInput.value = inventoryNumbers.join(',');
        }
        trackerInventoryMap = JSON.stringify(trackerInventoryMap);
        document.getElementById('tracker_inventory_map_input').value = trackerInventoryMap;
        // Удаляем данные из localStorage
        localStorage.removeItem('trackerInventoryMap');
    });

    // Очищаем localStorage при нажатии на "Отмена"
    cancelButton.addEventListener('click', function () {
        localStorage.removeItem('trackerInventoryMap');
    });
});