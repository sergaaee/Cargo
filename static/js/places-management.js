document.addEventListener("DOMContentLoaded", function () {
    const placesList = document.getElementById("places-list");
    const trackCodeInput = document.querySelector('input[name="track_code"]');
    const trackCode = trackCodeInput ? trackCodeInput.value : '';
    let itemToDelete = null;

    // Инициализация пула номеров
    window.availableNumbers = new Set();
    window.trackCode = trackCode;
    const selectedIncomingsData = JSON.parse(document.getElementById('initialIncomingsJson').textContent) || [];
    selectedIncomingsData.forEach(incoming => {
        if (incoming.inventory_numbers) {
            incoming.inventory_numbers.forEach(num => window.availableNumbers.add(num));
        }
    });

    trackCodeInput.addEventListener('input', function () {
        const newTrackCode = this.value.trim();
        // Обновляем глобальную переменную trackCode
        window.trackCode = newTrackCode;

        // Обновляем значения всех существующих полей place_consolidated
        const placeInputs = document.querySelectorAll('input[name^="place_consolidated_"]');
        placeInputs.forEach((input, index) => {
            input.value = `${newTrackCode}-${index + 1}`;
        });
    });

    // Функция для создания новой строки места
    function createNewPlace(index) {
    const newItem = document.createElement("li");
    newItem.className = "list-group-item place-item";
    newItem.dataset.itemIndex = index;

    const deleteButtonHtml = index > 0 ? `
        <button type="button" class="btn btn-icon btn-outline-danger delete-place-btn" data-item-index="${index}">
            <span class="bi bi-trash me-2"></span>
        </button>
    ` : '';

    newItem.innerHTML = `
        <div class="row">
            <div class="col-md-3">
                <label for="inventory-input-${index}">Инвентарные номера</label>
                <input id="inventory-input-${index}"
                       class="form-control inventory-input"
                       data-item-index="${index}"
                       placeholder="Введите номер">
                <input type="hidden"
                       name="inventory_numbers_${index}"
                       id="hidden-inventory-numbers-${index}"
                       value="">
                <div id="place-inventory-numbers-list-${index}" class="mt-2"></div>
            </div>
            <div class="col-md-2">
                <label for="place_${index}">Код места</label>
                <input type="text"
                       name="place_consolidated_${index}"
                       class="form-control"
                       value="${window.trackCode}-${index + 1}"
                       readonly>
            </div>
            <div class="col-md-2">
                <label for="package_type_${index}">Упаковка</label>
                <select name="package_type_${index}" class="form-select">
                    ${JSON.parse(document.getElementById('packageTypesJson').textContent).map(pt => `<option value="${pt}">${pt}</option>`).join('')}
                </select>
            </div>
            <div class="col-md-1 d-flex align-items-center">
                ${deleteButtonHtml}
            </div>
        </div>
    `;

    return newItem;
}

    // Обработка ввода инвентарных номеров для мест
    function setupInventoryInput(input) {
        input.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                event.preventDefault();
                const itemIndex = input.dataset.itemIndex;
                const hiddenInput = document.getElementById(`hidden-inventory-numbers-${itemIndex}`);
                const listContainer = document.getElementById(`place-inventory-numbers-list-${itemIndex}`);

                const number = input.value.trim();
                if (number) {
                    if (!window.availableNumbers.has(number)) {
                        window.showError(`Инвентарный номер ${number} не доступен.`);
                        input.value = "";
                        return;
                    }

                    let currentNumbers = hiddenInput.value.split(",").filter(Boolean);
                    if (!currentNumbers.includes(number)) {
                        const allUsedNumbers = new Set();
                        document.querySelectorAll('input[name^="inventory_numbers_"]').forEach(otherHiddenInput => {
                            if (otherHiddenInput !== hiddenInput) {
                                const otherNumbers = otherHiddenInput.value.split(",").filter(Boolean);
                                otherNumbers.forEach(num => allUsedNumbers.add(num));
                            }
                        });

                        if (allUsedNumbers.has(number)) {
                            window.showError(`Инвентарный номер ${number} уже используется в другом месте.`);
                            input.value = "";
                            return;
                        }

                        currentNumbers.push(number);
                        hiddenInput.value = currentNumbers.join(",");
                        window.availableNumbers.delete(number);

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
                            window.availableNumbers.add(number);
                        });

                        numberBadge.appendChild(removeBtn);
                        listContainer.appendChild(numberBadge);
                        input.value = "";
                    }
                }
            }
        });
    }

    // Добавление начального места
    const initialPlace = createNewPlace(0);
    placesList.appendChild(initialPlace);
    const initialInventoryInput = initialPlace.querySelector(".inventory-input");
    setupInventoryInput(initialInventoryInput);

    // Обработка добавления места
    document.querySelector(".add-place-btn").addEventListener("click", function () {
        const lastItem = placesList.querySelector(".place-item:last-child");
        const lastIndex = parseInt(lastItem.dataset.itemIndex);
        const newIndex = lastIndex + 1;

        const newItem = createNewPlace(newIndex);
        placesList.appendChild(newItem);
        const newInventoryInput = newItem.querySelector(".inventory-input");
        setupInventoryInput(newInventoryInput);
    });

    // Обработка кликов на кнопки удаления
    placesList.addEventListener("click", function (event) {
        const deleteBtn = event.target.closest(".delete-place-btn");
        if (deleteBtn) {
            console.log("Delete button clicked, item:", deleteBtn.closest(".place-item"));
            itemToDelete = deleteBtn.closest(".place-item");
            const modalElement = document.getElementById("deletePlaceModal");
            if (modalElement) {
                console.log("Modal element found, showing modal");
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
            } else {
                console.error("Modal element #deletePlaceModal not found");
            }
        }
    });

    // Обработка подтверждения удаления
    document.getElementById("confirmDeletePlaceBtn").addEventListener("click", function () {
        console.log("Confirm delete button clicked, itemToDelete:", itemToDelete);
        if (!itemToDelete) {
            console.error("itemToDelete is null or undefined");
            return;
        }

        const hiddenInput = itemToDelete.querySelector('input[name^="inventory_numbers_"]');
        if (hiddenInput) {
            const numbersToReturn = hiddenInput.value.split(",").filter(Boolean);
            console.log("Returning inventory numbers:", numbersToReturn);
            numbersToReturn.forEach(num => window.availableNumbers.add(num));
        } else {
            console.warn("No hidden input found for inventory numbers");
        }

        itemToDelete.remove();
        const modalElement = document.getElementById("deletePlaceModal");
        if (!modalElement) {
            console.error("Modal element #deletePlaceModal not found");
            return;
        }

        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
        } else {
            console.error("Modal instance not found");
        }

        modalElement.addEventListener("hidden.bs.modal", function handler() {
            console.log("Modal hidden, updating remaining items");
            const backdrops = document.querySelectorAll(".modal-backdrop");
            backdrops.forEach(backdrop => backdrop.remove());

            document.body.classList.remove("modal-open");
            document.body.style.overflow = "auto";
            document.body.style.paddingRight = "";

            const remainingItems = placesList.querySelectorAll(".place-item");
            remainingItems.forEach((item, index) => {
                console.log("Updating item index:", index);
                item.dataset.itemIndex = index;

                const inventoryInput = item.querySelector(".inventory-input");
                inventoryInput.id = `inventory-input-${index}`;
                inventoryInput.dataset.itemIndex = index;

                const hiddenInput = item.querySelector(`input[name^="inventory_numbers_"]`);
                hiddenInput.id = `hidden-inventory-numbers-${index}`;
                hiddenInput.name = `inventory_numbers_${index}`;

                const listContainer = item.querySelector(`div[id^="place-inventory-numbers-list-"]`);
                listContainer.id = `place-inventory-numbers-list-${index}`;

                const placeInput = item.querySelector(`input[name^="place_consolidated_"]`);
                placeInput.name = `place_consolidated_${index}`;
                placeInput.id = `place_${index}`;
                placeInput.value = `${trackCode}-${index + 1}`;

                const packageTypeSelect = item.querySelector(`select[name^="package_type_"]`);
                packageTypeSelect.name = `package_type_${index}`;
                packageTypeSelect.id = `package_type_${index}`;

                const deleteBtn = item.querySelector(".delete-place-btn");
                if (deleteBtn) {
                    deleteBtn.dataset.itemIndex = index;
                }
            });

            itemToDelete = null;
            modalElement.removeEventListener("hidden.bs.modal", handler);
        }, {once: true});
    });
});