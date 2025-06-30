document.addEventListener("DOMContentLoaded", function () {
    const trackerInput = document.getElementById('tracker-input');
    const selectedTrackersContainer = document.getElementById('selected-trackers');
    const noTrackerCheckbox = document.getElementById('no-tracker-checkbox');
    const selectedTrackersInput = document.getElementById('selected-trackers-input');
    const modal = new bootstrap.Modal(document.getElementById('additionalInputModal'));
    const inventoryInput = document.getElementById('inventory-input');
    const selectedInventoryContainer = document.getElementById('selected-inventory-numbers');
    const selectedInventoryInput = document.getElementById('selected-inventory-input');
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

            trackerDiv.addEventListener('click', () => {
                loadInventoryNumbersForTracker(code);
                modal.show();
            });

            const removeBtn = document.createElement('span');
            removeBtn.classList.add('ms-2', 'text-white', 'cursor-pointer');
            removeBtn.innerHTML = '×';
            removeBtn.addEventListener('click', (event) => {
                event.stopPropagation();
                selectedTrackers.splice(index, 1);
                delete trackerInventoryMap[code];
                localStorage.setItem('trackerInventoryMap', JSON.stringify(trackerInventoryMap));
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
            removeBtn.innerHTML = '×';
            removeBtn.addEventListener('click', () => {
                const index = inventoryNumbers.indexOf(number);
                if (index > -1) {
                    inventoryNumbers.splice(index, 1);
                    trackerInventoryMap[trackerCode] = inventoryNumbers;
                    localStorage.setItem('trackerInventoryMap', JSON.stringify(trackerInventoryMap));
                    loadInventoryNumbersForTracker(trackerCode);
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
        if (event.keyCode === 13) {
            event.preventDefault();
            const selectedNumber = inventoryInput.value.trim();
            for (const tracker in trackerInventoryMap) {
                if (trackerInventoryMap[tracker].includes(selectedNumber)) {
                    alert(`Инвентарный номер ${selectedNumber} уже привязан к трек-коду ${tracker}`);
                    inventoryInput.value = '';
                    return;
                }
            }
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
        }
    });

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
                            });

                            numberBadge.appendChild(removeBtn);
                            listContainer.appendChild(numberBadge);
                            input.value = "";
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

    // Add listeners for existing inventory inputs
    document.querySelectorAll('.inventory-input').forEach(input => {
        input.addEventListener('input', function () {
            const itemIndex = this.getAttribute('data-item-index');
            updateLocationSelect(itemIndex);
        });
    });
});