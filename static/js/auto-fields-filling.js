document.addEventListener("DOMContentLoaded", function () {
    const trackerInput = document.getElementById('tracker-input');
    const selectedTrackersContainer = document.getElementById('selected-trackers');
    const noTrackerCheckbox = document.getElementById('no-tracker-checkbox');
    const selectedTrackersInput = document.getElementById('selected-trackers-input');
    const modal = new bootstrap.Modal(document.getElementById('additionalInputModal'));
    const inventoryInput = document.getElementById('inventory-input');
    const selectedInventoryContainer = document.getElementById('selected-inventory-numbers');
    const selectedInventoryInput = document.getElementById('selected-inventory-input');
    const availableInventoryNumbersForLocationsContainer = document.getElementById('available-inventory-numbers-for-location-container');
    const closeButtonX = document.querySelector('.modal .btn-close');

    let selectedTrackers = [];
    let trackerInventoryMap = JSON.parse(localStorage.getItem('trackerInventoryMap')) || {};

    for (let trackerCode in codesNumsMap) {
        let inventoryNumbers = codesNumsMap[trackerCode];
        if (!trackerInventoryMap[trackerCode]) {
            trackerInventoryMap[trackerCode] = [];
        }
        trackerInventoryMap[trackerCode] = inventoryNumbers;
        if (!selectedTrackers.includes(trackerCode)) {
            selectedTrackers.push(trackerCode);
        }
    }

    localStorage.setItem('trackerInventoryMap', JSON.stringify(trackerInventoryMap));
    updateSelectedTrackers();

    // Function to update selected trackers
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

    // Function to load inventory numbers for a tracker
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

    // Function to add a selected tracker
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
            modal.show();
        } else if (selectedTrackers.includes(selectedCode)) {
            loadInventoryNumbersForTracker(selectedCode);
            modal.show();
        }
        trackerInput.value = '';
    }

    noTrackerCheckbox.addEventListener('change', function () {
        trackerInput.disabled = noTrackerCheckbox.checked;
        if (noTrackerCheckbox.checked) {
            trackerInput.value = '';
            const currentDatetime = new Date().toISOString().replace(/[-:.TZ]/g, '');
            selectedTrackers.push(`undefined-${currentDatetime}`);
            updateSelectedTrackers();
            loadInventoryNumbersForTracker(`undefined-${currentDatetime}`);
            modal.show();
        }
    });

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

    function loadAvailableInventoryNumbers(trackerCode) {
        const inventoryNumbers = trackerInventoryMap[trackerCode] || [];
        availableInventoryNumbersForLocationsContainer.innerHTML = '';

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

    closeButtonX.addEventListener('click', function () {
        const selectedNumber = inventoryInput.value.trim();
        const modalTitle = document.getElementById("additionalInputModalLabel").textContent;
        const currentTracker = modalTitle.replace("Инвентарные номера для трек кода: ", "").trim();
        if (selectedNumber && currentTracker) {
            trackerInventoryMap[currentTracker] = trackerInventoryMap[currentTracker] || [];
            if (!trackerInventoryMap[currentTracker].includes(selectedNumber)) {
                trackerInventoryMap[currentTracker].push(selectedNumber);
                localStorage.setItem('trackerInventoryMap', JSON.stringify(trackerInventoryMap));
                loadInventoryNumbersForTracker(currentTracker);
            }
        }
        inventoryInput.value = '';
    });

    trackerInput.addEventListener('change', addSelectedTracker);
    trackerInput.addEventListener('keydown', function (event) {
        if (event.keyCode === 13) {
            event.preventDefault();
            addSelectedTracker();
        }
    });

    // New Functions for Location Management

    // Check if inventory number is associated with the incoming
    function isInventoryNumberAssociated(number) {
        for (let tracker in trackerInventoryMap) {
            if (trackerInventoryMap[tracker].includes(number)) {
                return true;
            }
        }
        return false;
    }

    // Get all assigned inventory numbers across locations
    function getAssignedInventoryNumbers() {
        const assigned = new Set();
        document.querySelectorAll('input[name^="inventory_numbers_"]').forEach(input => {
            const numbers = input.value.split(',').filter(Boolean);
            numbers.forEach(num => assigned.add(num));
        });
        return assigned;
    }

    // Update the global selected-inventory-input
    function updateSelectedInventoryInput() {
        const allHiddenInputs = document.querySelectorAll('input[name^="inventory_numbers_"]');
        const allNumbers = new Set();
        allHiddenInputs.forEach(input => {
            const numbers = input.value.split(",").filter(Boolean);
            numbers.forEach(num => allNumbers.add(num));
        });
        document.getElementById("selected-inventory-input").value = Array.from(allNumbers).join(",");
    }

    // Setup inventory input for adding badges
    function setupInventoryInput(input) {
        input.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                event.preventDefault();
                const itemIndex = input.dataset.itemIndex;
                const hiddenInput = document.getElementById(`hidden-inventory-numbers-${itemIndex}`);
                const listContainer = document.getElementById(`inventory-numbers-list-${itemIndex}`);
                const number = input.value.trim();

                if (number) {
                    let currentNumbers = hiddenInput.value.split(",").filter(Boolean);
                    if (!currentNumbers.includes(number)) {
                        const assignedNumbers = getAssignedInventoryNumbers();
                        if (isInventoryNumberAssociated(number) && !assignedNumbers.has(number)) {
                            currentNumbers.push(number);
                            hiddenInput.value = currentNumbers.join(",");
                            const numberBadge = document.createElement("span");
                            numberBadge.className = "badge bg-primary me-1";
                            numberBadge.textContent = number;
                            numberBadge.dataset.number = number;

                            const removeBtn = document.createElement("span");
                            removeBtn.className = "ms-2 text-white cursor-pointer";
                            removeBtn.innerHTML = "×";
                            removeBtn.addEventListener("click", function () {
                                currentNumbers = currentNumbers.filter(n => n !== number);
                                hiddenInput.value = currentNumbers.join(",");
                                numberBadge.remove();
                                updateSelectedInventoryInput();

                                const inventoryDiv = document.createElement('div');
                                inventoryDiv.classList.add('selected-inventory', 'badge', 'bg-secondary', 'me-1', 'mb-1');
                                inventoryDiv.textContent = number;
                                inventoryDiv.dataset.number = number;

                                availableInventoryNumbersForLocationsContainer.appendChild(inventoryDiv);
                            });

                            numberBadge.appendChild(removeBtn);
                            listContainer.appendChild(numberBadge);
                            input.value = "";

                            const availableContainer = document.getElementById(`available-inventory-numbers-for-location-container`);
                            if (availableContainer) {
                                const badges = availableContainer.querySelectorAll(`div.badge[data-number="${number}"]`);
                                badges.forEach(badge => badge.remove());
                            }

                            updateSelectedInventoryInput();
                        } else {
                            alert("Инвентарный номер не связан с этим поступлением или уже привязан к другой локации.");
                        }
                    }
                }
            }
        });
    }

    // Initialize existing inventory inputs
    document.querySelectorAll('.inventory-input').forEach(input => {
        setupInventoryInput(input);
    });

    // Attach remove functionality to existing badges
    document.querySelectorAll('.location-item').forEach(item => {
        const itemIndex = item.dataset.itemIndex;
        const hiddenInput = document.getElementById(`hidden-inventory-numbers-${itemIndex}`);
        const badgeList = document.getElementById(`inventory-numbers-list-${itemIndex}`);
        badgeList.querySelectorAll('.badge').forEach(badge => {
            const removeBtn = badge.querySelector('.cursor-pointer');
            removeBtn.addEventListener('click', function () {
                const number = badge.dataset.number;
                let currentNumbers = hiddenInput.value.split(',').filter(n => n !== number);
                hiddenInput.value = currentNumbers.join(',');
                badge.remove();
                updateSelectedInventoryInput();
            });
        });
    });

    // Handle adding new location items
    document.querySelector('.add-item-btn').addEventListener('click', function () {
        const locationSelection = document.getElementById('location-selection');
        const newItemIndex = locationSelection.children.length;
        const newItem = locationSelection.children[0].cloneNode(true);

        // Clear values in the new item
        const inventoryInput = newItem.querySelector('.inventory-input');
        inventoryInput.value = '';
        const hiddenInput = newItem.querySelector('input[type="hidden"]');
        hiddenInput.value = '';
        const badgeList = newItem.querySelector('.mt-2');
        badgeList.innerHTML = '';
        const locationSelect = newItem.querySelector('select');
        locationSelect.value = '';

        // Update attributes
        newItem.setAttribute('data-item-index', newItemIndex);
        inventoryInput.setAttribute('id', `inventory-input-${newItemIndex}`);
        inventoryInput.setAttribute('data-item-index', newItemIndex);
        hiddenInput.setAttribute('id', `hidden-inventory-numbers-${newItemIndex}`);
        hiddenInput.setAttribute('name', `inventory_numbers_${newItemIndex}`);
        badgeList.setAttribute('id', `inventory-numbers-list-${newItemIndex}`);
        locationSelect.setAttribute('id', `location-${newItemIndex}`);
        locationSelect.setAttribute('name', `location_${newItemIndex}`);
        const deleteBtn = newItem.querySelector('.delete-item-btn');
        deleteBtn.setAttribute('data-item-index', newItemIndex);

        locationSelection.appendChild(newItem);

        // Setup new inventory input
        setupInventoryInput(inventoryInput);
    });

    // Handle deletion of location items
    document.getElementById('location-selection').addEventListener('click', function (event) {
        const deleteBtn = event.target.closest('.delete-item-btn');
        if (deleteBtn) {
            const itemIndex = deleteBtn.dataset.itemIndex;
            const item = document.querySelector(`.location-item[data-item-index="${itemIndex}"]`);
            if (item) {
                item.remove();
                updateSelectedInventoryInput();
            }
        }
    });
});