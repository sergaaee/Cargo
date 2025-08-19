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

                // Удаляем все его инвентарные номера из localStorage
                const inventoryNumbers = trackerInventoryMap[code] || [];
                delete trackerInventoryMap[code];
                localStorage.setItem('trackerInventoryMap', JSON.stringify(trackerInventoryMap));

                // Удаляем инвентарные номера из скрытых полей
                if (selectedInventoryInput) {
                    let currentValues = selectedInventoryInput.value.split(',').filter(v => v.trim() !== "");
                    currentValues = currentValues.filter(num => !inventoryNumbers.includes(num));
                    selectedInventoryInput.value = currentValues.join(',');
                }

                // Удаляем все бейджи из available-inventory-numbers-for-location-container
                const availableContainer = document.getElementById('available-inventory-numbers-for-location-container');
                if (availableContainer) {
                    inventoryNumbers.forEach(num => {
                        const badge = availableContainer.querySelector(`div.badge[data-number="${num}"]`);
                        if (badge) {
                            badge.remove();
                        }
                    });
                }


                const inventoryContainer = document.getElementById('inventory-container');
                if (inventoryContainer) {
                    inventoryNumbers.forEach(num => {
                        const badge = inventoryContainer.querySelector(`div.badge[data-number="${num}"]`);
                        if (badge) {
                            badge.remove();
                        }
                    });
                }

                // Удаляем бейджи этого трекера из всех inventory-numbers-list-*
                const allTrackerContainers = document.querySelectorAll('[id^="inventory-numbers-list-"]');
                allTrackerContainers.forEach(trackerContainer => {
                    inventoryNumbers.forEach(num => {
                        const badge = trackerContainer.querySelector(`span.badge[data-number="${num}"]`);
                        if (badge) {
                            badge.remove();
                        }
                    });
                });

                const allInventoriesHiddenInputs = document.querySelectorAll(`[id^="hidden-inventory-numbers-"]`);
                allInventoriesHiddenInputs.forEach(inventoryInput => {
                    // Получаем текущие значения из скрытого поля
                    let currentValues = inventoryInput.value.split(',').map(v => v.trim()).filter(v => v !== '');

                    // Удаляем все номера, принадлежащие трекеру
                    currentValues = currentValues.filter(num => !inventoryNumbers.includes(num));

                    // Записываем обратно
                    inventoryInput.value = currentValues.join(',');
                });


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
            removeBtn.addEventListener('click', (event) => {
                event.stopPropagation();
                const removedNumber = number; // сохраняем номер, который удаляем
                const index = inventoryNumbers.indexOf(number);
                if (index > -1) {
                    inventoryNumbers.splice(index, 1);
                    trackerInventoryMap[trackerCode] = inventoryNumbers;
                    localStorage.setItem('trackerInventoryMap', JSON.stringify(trackerInventoryMap));
                    loadInventoryNumbersForTracker(trackerCode);

                    // Удаляем из скрытых полей
                    if (selectedInventoryInput) {
                        let currentValues = selectedInventoryInput.value.split(',').filter(v => v.trim() !== "");
                        currentValues = currentValues.filter(num => num !== removedNumber);
                        selectedInventoryInput.value = currentValues.join(',');
                    }

                    // Удаляем бейджи из available-inventory-numbers-for-location-container
                    const availableContainer = document.getElementById('available-inventory-numbers-for-location-container');
                    if (availableContainer) {
                        const badge = availableContainer.querySelector(`div.badge[data-number="${removedNumber}"]`);
                        if (badge) badge.remove();
                    }

                    // Удаляем из inventory-container
                    const inventoryContainer = document.getElementById('inventory-container');
                    if (inventoryContainer) {
                        const badge = inventoryContainer.querySelector(`div.badge[data-number="${removedNumber}"]`);
                        if (badge) badge.remove();
                    }

                    // Удаляем бейджи из всех inventory-numbers-list-*
                    const allTrackerContainers = document.querySelectorAll('[id^="inventory-numbers-list-"]');
                    allTrackerContainers.forEach(trackerContainer => {
                        const badge = trackerContainer.querySelector(`span.badge[data-number="${removedNumber}"]`);
                        if (badge) badge.remove();
                    });

                    // Удаляем из всех hidden input
                    const allInventoriesHiddenInputs = document.querySelectorAll(`[id^="hidden-inventory-numbers-"]`);
                    allInventoriesHiddenInputs.forEach(inventoryInput => {
                        let currentValues = inventoryInput.value.split(',').map(v => v.trim()).filter(v => v !== '');
                        currentValues = currentValues.filter(num => num !== removedNumber);
                        inventoryInput.value = currentValues.join(',');
                    });
                }
            });


            inventoryDiv.appendChild(removeBtn);
            selectedInventoryContainer.appendChild(inventoryDiv);
        });
    }

    availableInventoryNumbersForLocationsContainer.innerHTML = '';

    function loadAvailableInventoryNumbers(trackerCode) {
        const inventoryNumbers = trackerInventoryMap[trackerCode] || [];

        inventoryNumbers.forEach((number) => {
            let alreadyExists = false;

            const allTrackerContainers = document.querySelectorAll('[id^="inventory-numbers-list-"]');
            allTrackerContainers.forEach(trackerContainer => {
                const badge = trackerContainer.querySelector(`span.badge[data-number="${number}"]`);
                if (badge) {
                    alreadyExists = true;
                }
            });

            if (!alreadyExists) {
                const inventoryDiv = document.createElement('div');
                inventoryDiv.classList.add('selected-inventory', 'badge', 'bg-secondary', 'me-1', 'mb-1');
                inventoryDiv.textContent = number;
                inventoryDiv.dataset.number = number;

                availableInventoryNumbersForLocationsContainer.appendChild(inventoryDiv);
            }
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