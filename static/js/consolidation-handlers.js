class ConsolidationHandlers {
    constructor() {
        this.form = document.getElementById("consolidation-form");
        this.incomingsData = JSON.parse(document.getElementById("incomingsJson").textContent);
        this.initialIncomingsData = JSON.parse(document.getElementById("initialIncomingsJson").textContent);
        this.selectedInventoryMap = new Map();

        this.init();
    }

    init() {
        this.setupInitialData();
        this.restoreLocalStorage();
        this.setupEventListeners();
    }

    setupInitialData() {
        // Установка начальных данных для консолидации
        if (this.initialIncomingsData) {
            this.initialIncomingsData.forEach(incoming => {
                this.selectedInventoryMap.set(incoming.id, new Set(incoming.inventory_numbers));
            });
        }
    }

    restoreLocalStorage() {
        // Восстанавливаем данные выбора инвентарных номеров из localStorage
        this.incomingsData.forEach(incoming => {
            const storedData = localStorage.getItem(`incoming_${incoming.id}`);
            if (storedData) {
                const selectedNumbers = JSON.parse(storedData);
                this.selectedInventoryMap.set(incoming.id, new Set(selectedNumbers));
                this.updatePlacesCount(incoming.id, selectedNumbers);
            }
        });
    }

    saveToLocalStorage(incomingId, selectedInventoryNumbers) {
        localStorage.setItem(`incoming_${incomingId}`, JSON.stringify(selectedInventoryNumbers));
    }

    updatePlacesCount(incomingId, selectedInventoryNumbers) {
        const displayInput = document.querySelector(`#places_display_${incomingId}`);
        const hiddenInput = document.querySelector(`input[name="places_consolidated"][data-incoming-id="${incomingId}"]`);

        if (displayInput && hiddenInput) {
            const maxPlaces = parseInt(displayInput.getAttribute('data-max-places'));
            const currentCount = selectedInventoryNumbers.length;

            displayInput.value = `${currentCount}/${maxPlaces}`;
            hiddenInput.value = currentCount;
        }
    }

    updateHiddenInventoryFields() {
        // Синхронизация скрытого поля selected_inventory перед отправкой
        const inventoryInput = document.getElementById("selected_inventory");
        const inventoryData = {};

        this.selectedInventoryMap.forEach((numbers, incomingId) => {
            inventoryData[incomingId] = Array.from(numbers);
        });

        inventoryInput.value = JSON.stringify(inventoryData);
    }

    validateForm() {
        const selectedIncomings = document.querySelectorAll("#consolidation-list .list-group-item");

        for (const item of selectedIncomings) {
            const incomingId = item.getAttribute("data-id");
            const selectedNumbers = this.selectedInventoryMap.get(incomingId) || new Set();
            const placesCountInput = item.querySelector('input[name="places_consolidated"]');
            const placesCount = parseInt(placesCountInput.value || 0, 10);

            item.classList.remove("border", "border-danger");

            if (selectedNumbers.size === 0) {
                item.classList.add("border", "border-danger");
                return {
                    isValid: false,
                    message: `Поступление #${incomingId} не содержит выбранных инвентарных номеров!`
                };
            }

            if (selectedNumbers.size < placesCount) {
                item.classList.add("border", "border-danger");
                return {
                    isValid: false,
                    message: `Для поступления #${incomingId} выбрано ${selectedNumbers.size} инвентарных номеров, но указано ${placesCount} мест.`
                };
            }
        }

        return {isValid: true};
    }

    showAlert(message) {
        // Отображение всплывающего сообщения об ошибке
        let alertBox = document.getElementById("custom-alert-box");
        if (!alertBox) {
            alertBox = document.createElement("div");
            alertBox.id = "custom-alert-box";
            alertBox.className = "alert alert-danger mt-3";
            document.body.appendChild(alertBox);
        }
        alertBox.innerHTML = message;
        alertBox.style.display = "block";

        setTimeout(() => (alertBox.style.display = "none"), 5000);
    }

    setupEventListeners() {
        // Обработка чекбоксов инвентарных номеров
        document.querySelectorAll(".inventory-checkbox").forEach(checkbox => {
            checkbox.addEventListener("change", (event) => {
                const incomingId = event.target.dataset.incomingId;
                const inventoryNumber = event.target.dataset.inventoryNumber;

                if (!this.selectedInventoryMap.has(incomingId)) {
                    this.selectedInventoryMap.set(incomingId, new Set());
                }

                const numberSet = this.selectedInventoryMap.get(incomingId);
                if (event.target.checked) {
                    numberSet.add(inventoryNumber);
                } else {
                    numberSet.delete(inventoryNumber);
                }

                this.saveToLocalStorage(incomingId, Array.from(numberSet));
                this.updatePlacesCount(incomingId, Array.from(numberSet));
            });
        });

        // Валидация и отправка формы
        this.form.addEventListener("submit", (event) => {
            const validationResult = this.validateForm();

            if (!validationResult.isValid) {
                event.preventDefault();
                this.showAlert(validationResult.message);
            } else {
                this.updateHiddenInventoryFields();
            }
        });
    }
}