document.addEventListener("DOMContentLoaded", function () {
    // Функция для обновления отображения пула номеров
    window.updateInventoryPool = function (incomingId) {
        const listContainer = document.getElementById(`inventory-numbers-list-${incomingId}`);
        if (!listContainer) return;

        const storedData = localStorage.getItem(`incoming_${incomingId}`);
        const selectedNumbers = storedData ? JSON.parse(storedData) : [];

        listContainer.innerHTML = selectedNumbers
            .map(num => `<span class="badge bg-primary me-1">${num}<span class="ms-2 text-white cursor-pointer" data-number="${num}" onclick="removeInventoryNumber('${incomingId}', '${num}')">×</span></span>`)
            .join('');

        updatePlacesCount(incomingId);
    };

    // Функция для удаления инвентарного номера
    window.removeInventoryNumber = function (incomingId, number) {
        let selectedNumbers = localStorage.getItem(`incoming_${incomingId}`)
            ? JSON.parse(localStorage.getItem(`incoming_${incomingId}`))
            : [];
        selectedNumbers = selectedNumbers.filter(num => num !== number);
        localStorage.setItem(`incoming_${incomingId}`, JSON.stringify(selectedNumbers));
        window.availableNumbers.add(number);
        window.updateInventoryPool(incomingId);
        updateSelectedInventoryField();
    };

    // Функция для обновления количества мест
    function updatePlacesCount(incomingId) {
        const storedData = localStorage.getItem(`incoming_${incomingId}`);
        const selectedNumbers = storedData ? JSON.parse(storedData) : [];
        const placesCountInput = document.querySelector(`input[data-incoming-id="${incomingId}"][name="places_consolidated"]`);
        if (placesCountInput) {
            const maxPlaces = parseInt(placesCountInput.dataset.maxPlaces, 10);
            const selectedCount = selectedNumbers.length;
            placesCountInput.value = `${selectedCount}/${maxPlaces}`;
            placesCountInput.dataset.submitValue = selectedCount;
        }
    }

    // Обновление поля selected_inventory
    function updateSelectedInventoryField() {
        const inventoryInput = document.getElementById("selected_inventory");
        let inventoryData = JSON.parse(inventoryInput.value || "{}");

        document.querySelectorAll('.inventory-checkbox').forEach(checkbox => {
            const incomingId = checkbox.dataset.incomingId;
            const inventoryNumber = checkbox.dataset.inventoryNumber;

            if (checkbox.checked) {
                if (!inventoryData[incomingId]) {
                    inventoryData[incomingId] = [];
                }
                if (!inventoryData[incomingId].includes(inventoryNumber)) {
                    inventoryData[incomingId].push(inventoryNumber);
                }
            } else {
                if (inventoryData[incomingId]) {
                    inventoryData[incomingId] = inventoryData[incomingId].filter(num => num !== inventoryNumber);
                    if (inventoryData[incomingId].length === 0) {
                        delete inventoryData[incomingId];
                    }
                }
            }
        });

        inventoryInput.value = JSON.stringify(inventoryData);
        console.log("Updated selected_inventory:", inventoryInput.value);
    }

    // Обработка выбора инвентарных номеров
    document.addEventListener('change', function (event) {
        if (event.target.classList.contains('inventory-checkbox')) {
            const incomingId = event.target.dataset.incomingId;
            let selectedNumbers = localStorage.getItem(`incoming_${incomingId}`)
                ? JSON.parse(localStorage.getItem(`incoming_${incomingId}`))
                : [];

            if (event.target.checked) {
                if (!selectedNumbers.includes(event.target.dataset.inventoryNumber)) {
                    selectedNumbers.push(event.target.dataset.inventoryNumber);
                    window.availableNumbers.add(event.target.dataset.inventoryNumber);
                }
            } else {
                selectedNumbers = selectedNumbers.filter(num => num !== event.target.dataset.inventoryNumber);
                window.availableNumbers.delete(event.target.dataset.inventoryNumber);
            }

            localStorage.setItem(`incoming_${incomingId}`, JSON.stringify(selectedNumbers));
            window.updateInventoryPool(incomingId);
            updateSelectedInventoryField();
            console.log("Selected numbers for incoming", incomingId, ":", selectedNumbers);
        }
    });

    // Инициализация отображения инвентарных номеров для всех поступлений
    const selectedIncomingsData = JSON.parse(document.getElementById('initialIncomingsJson').textContent) || [];
    selectedIncomingsData.forEach(incoming => {
        window.updateInventoryPool(incoming.id);
    });
});