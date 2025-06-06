document.addEventListener("DOMContentLoaded", function () {
    const trackerInput = document.getElementById('tracker-input');
    const selectedTrackersContainer = document.getElementById('selected-trackers');
    const availableInventoryNumbersForLocationsContainer = document.getElementById('available-inventory-numbers-for-location-container');
    const noTrackerCheckbox = document.getElementById('no-tracker-checkbox');
    const selectedTrackersInput = document.getElementById('selected-trackers-input');
    const modal = new bootstrap.Modal(document.getElementById('additionalInputModal'));
    const inventoryInput = document.getElementById('inventory-input');
    const selectedInventoryContainer = document.getElementById('selected-inventory-numbers');
    const selectedInventoryInput = document.getElementById('selected-inventory-input');
    const closeButtonX = document.querySelector('.modal .btn-close');
    const closeButton = document.querySelector('button[name="button-close-close"]');

    let selectedTrackers = [];
    let trackerInventoryMap = JSON.parse(localStorage.getItem('trackerInventoryMap')) || {};

    // Функция для обновления выбранных трек-кодов
    function updateSelectedTrackers() {
        selectedTrackersContainer.innerHTML = '';
        selectedTrackersInput.value = selectedTrackers.join(',');

        selectedTrackers.forEach((code, index) => {
            const trackerDiv = document.createElement('div');
            trackerDiv.classList.add('selected-tracker', 'badge', 'bg-primary', 'me-1', 'mb-1');
            trackerDiv.textContent = code;
            trackerDiv.style.cursor = 'pointer';

            // Делаем трек-код кликабельным, чтобы открывать модальное окно с его инвентарными номерами
            trackerDiv.addEventListener('click', () => {
                loadInventoryNumbersForTracker(code);
                modal.show();
            });

            const removeBtn = document.createElement('span');
            removeBtn.classList.add('ms-2', 'text-white', 'cursor-pointer');
            removeBtn.innerHTML = '&times;';
            removeBtn.addEventListener('click', (event) => {
                event.stopPropagation();
                // Удаляем трек-код из массива
                selectedTrackers.splice(index, 1);
                // Удаляем трек-код из localStorage
                delete trackerInventoryMap[code];
                localStorage.setItem('trackerInventoryMap', JSON.stringify(trackerInventoryMap));
                // Обновляем список выбранных трек-кодов
                updateSelectedTrackers();
            });

            trackerDiv.appendChild(removeBtn);
            selectedTrackersContainer.appendChild(trackerDiv);
        });
    }

    // Функция для загрузки инвентарных номеров для трек-кода
    function loadInventoryNumbersForTracker(trackerCode) {
        document.getElementById('additionalInputModalLabel').textContent = `Инвентарные номера для трек кода: ${trackerCode}`;

        const inventoryNumbers = trackerInventoryMap[trackerCode] || [];
        selectedInventoryContainer.innerHTML = '';
        selectedInventoryInput.value = inventoryNumbers.join(',');

        inventoryNumbers.forEach((number) => {
            const inventoryDiv = document.createElement('div');
            inventoryDiv.classList.add('selected-inventory', 'badge', 'bg-primary', 'me-1', 'mb-1');
            inventoryDiv.textContent = number;

            const removeBtn = document.createElement('span');
            removeBtn.classList.add('ms-2', 'text-white', 'cursor-pointer');
            removeBtn.innerHTML = '&times;';
            removeBtn.addEventListener('click', () => {
                event.stopPropagation();
                const index = inventoryNumbers.indexOf(number);
                if (index > -1) {
                    inventoryNumbers.splice(index, 1);
                    trackerInventoryMap[trackerCode] = inventoryNumbers;
                    localStorage.setItem('trackerInventoryMap', JSON.stringify(trackerInventoryMap));
                    loadInventoryNumbersForTracker(trackerCode); // обновить отображение
                }
            });

            inventoryDiv.appendChild(removeBtn);
            selectedInventoryContainer.appendChild(inventoryDiv);
        });
    }

    function loadAvailableInventoryNumbers(trackerCode) {
        const inventoryNumbers = trackerInventoryMap[trackerCode] || [];
        availableInventoryNumbersForLocationsContainer.innerHTML = '';

        inventoryNumbers.forEach((number) => {
            const inventoryDiv = document.createElement('div');
            inventoryDiv.classList.add('selected-inventory', 'badge', 'bg-secondary', 'me-1', 'mb-1'); // Используем bg-secondary для серого цвета
            inventoryDiv.textContent = number;
            inventoryDiv.dataset.number = number;

            availableInventoryNumbersForLocationsContainer.appendChild(inventoryDiv);
        });
    }

    // Функция для добавления трек-кода и открытия модального окна для инвентарных номеров
    function addSelectedTracker() {
        let selectedCode = trackerInput.value.trim();
        if (noTrackerCheckbox.checked) {
            const currentDatetime = new Date().toISOString().replace(/[-:.TZ]/g, '');
            selectedCode = `undefined-${currentDatetime}`;
        }
        if (selectedCode && !selectedTrackers.includes(selectedCode)) {
            selectedTrackers.push(selectedCode);
            updateSelectedTrackers();
            loadInventoryNumbersForTracker(selectedCode);
            loadAvailableInventoryNumbers(selectedCode);
            modal.show();
        } else if (selectedTrackers.includes(selectedCode)) {
            loadInventoryNumbersForTracker(selectedCode);
            loadAvailableInventoryNumbers(selectedCode);
            modal.show();
        }
        trackerInput.value = '';
    }

    noTrackerCheckbox.addEventListener('change', function () {
        trackerInput.disabled = noTrackerCheckbox.checked;
        if (noTrackerCheckbox.checked) {
            trackerInput.value = '';
            const currentDatetime = new Date().toISOString().replace(/[-:.TZ]/g, '');
            selectedCode = `undefined-${currentDatetime}`;
            selectedTrackers.push(selectedCode);
            updateSelectedTrackers();
            loadInventoryNumbersForTracker(selectedCode);
            loadAvailableInventoryNumbers(selectedCode);
            modal.show();
        }
    });

    // Добавление инвентарного номера
    inventoryInput.addEventListener('keydown', function (event) {
        if (event.keyCode === 13) {  // проверяем нажатие Enter
            event.preventDefault();
            const selectedNumber = inventoryInput.value.trim();

            for (const tracker in trackerInventoryMap) {
                if (trackerInventoryMap[tracker].includes(selectedNumber)) {
                    alert(`Инвентарный номер ${selectedNumber} уже привязан к трек-коду ${tracker}`);
                    inventoryInput.value = '';
                    return;
                }
            }

            // Получаем текущий трек-код из заголовка модального окна
            const modalTitle = document.getElementById("additionalInputModalLabel").textContent;
            const currentTracker = modalTitle.replace("Инвентарные номера для трек кода: ", "").trim();

            if (selectedNumber && currentTracker) {
                trackerInventoryMap[currentTracker] = trackerInventoryMap[currentTracker] || [];
                if (!trackerInventoryMap[currentTracker].includes(selectedNumber)) {
                    trackerInventoryMap[currentTracker].push(selectedNumber);
                    localStorage.setItem('trackerInventoryMap', JSON.stringify(trackerInventoryMap));
                    loadInventoryNumbersForTracker(currentTracker);
                    loadAvailableInventoryNumbers(currentTracker);
                }
            }
            inventoryInput.value = ''; // очищаем поле ввода
        }
    });


    function addInventoryNumber() {
        const selectedNumber = inventoryInput.value.trim();
        // Получаем текущий трек-код из заголовка модального окна
        const modalTitle = document.getElementById("additionalInputModalLabel").textContent;
        const currentTracker = modalTitle.replace("Инвентарные номера для трек кода: ", "").trim();

        if (selectedNumber && currentTracker) {
            trackerInventoryMap[currentTracker] = trackerInventoryMap[currentTracker] || [];
            if (!trackerInventoryMap[currentTracker].includes(selectedNumber)) {
                trackerInventoryMap[currentTracker].push(selectedNumber);
                localStorage.setItem('trackerInventoryMap', JSON.stringify(trackerInventoryMap));
                loadInventoryNumbersForTracker(currentTracker);
                loadAvailableInventoryNumbers(currentTracker);
            }
        }
        inventoryInput.value = ''; // очищаем поле ввода
    }

    // Привязываем инвентарный номер при нажатии на кнопку "Закрыть"
    closeButtonX.addEventListener('click', function () {
        addInventoryNumber();
    });
    closeButton.addEventListener('click', function () {
        addInventoryNumber();
    });

    trackerInput.addEventListener('change', addSelectedTracker);
    trackerInput.addEventListener('keydown', function (event) {
        if (event.keyCode === 13) {
            event.preventDefault();
            addSelectedTracker();
        }
    });
});