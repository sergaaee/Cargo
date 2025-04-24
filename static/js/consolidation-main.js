document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("consolidation-form");
    const clientInput = document.getElementById("client");
    const consolidationList = document.getElementById("consolidation-list");
    const trackCodeInput = document.querySelector('input[name="track_code"]');
    const trackCode = trackCodeInput ? trackCodeInput.value : '';
    let selectedIncomingsData = JSON.parse(document.getElementById('initialIncomingsJson').textContent) || [];
    let tempSelectedIncomings = [];

    // Обновление поля selected_incomings
    function updateSelectedIncomingsField() {
        const selectedIncomingsField = document.getElementById('selected-incomings');
        const selectedIncomingsIds = selectedIncomingsData.map(item => item.id).filter(id => id);
        selectedIncomingsField.value = selectedIncomingsIds.join(',');
        clientInput.readOnly = selectedIncomingsIds.length > 0;
        console.log("Updated selected_incomings:", selectedIncomingsField.value, "Client readOnly:", clientInput.readOnly);
        window.filterRows(); // Обновляем фильтрацию
    }

    // Добавление поступления в список
    window.addIncomingToList = function (incomingData) {
        if (selectedIncomingsData.some(item => item.id === incomingData.id)) {
            console.log("Incoming already added:", incomingData.id);
            return;
        }

        const newItem = document.createElement('li');
        newItem.className = 'list-group-item';
        newItem.setAttribute('data-id', incomingData.id);
        selectedIncomingsData.push(incomingData);

        newItem.innerHTML = `
            <div class="mb-2">
                <strong>Выбранные инвентарные номера:</strong>
                <div id="inventory-numbers-list-${incomingData.id}" class="mt-2"></div>
            </div>
            <div class="row">
                <div class="col-md-3">
                    <label for="selected_incoming_${incomingData.id}">Поступление</label>
                    <button type="button" class="btn btn-outline-primary"
                            data-bs-toggle="modal"
                            data-bs-target="#incomingModal${incomingData.id}">
                        Показать трек-коды
                    </button>
                </div>
                <div class="col-md-3">
                    <label for="places_count_${incomingData.id}">Количество мест (макс ${incomingData.places_count})</label>
                    <input type="text" name="places_consolidated" class="form-control" readonly
                           value="0/${incomingData.places_count}" data-max-places="${incomingData.places_count}"
                           data-incoming-id="${incomingData.id}">
                </div>
                <div class="col-md-3 d-flex align-items-center">
                    <button type="button" class="btn btn-icon btn-outline-info me-3" onclick="openIncomingModal('${incomingData.id}')">
                        <span class="bi bi-zoom-in me-2"></span>
                    </button>
                    <button type="button" class="btn btn-icon btn-outline-danger" onclick="removeIncomingFromList('${incomingData.id}')">
                        <i class="bi bi-x"></i>
                    </button>
                </div>
            </div>
            <div class="modal fade" id="incomingDetailModal${incomingData.id}" tabindex="-1" aria-labelledby="incomingDetailModalLabel${incomingData.id}" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="incomingDetailModalLabel${incomingData.id}">
                                Детали поступления #${incomingData.id}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <ul class="list-group list-group-flush">
                                <li class="list-group-item"><strong>Трек-коды:</strong> ${incomingData.tracking_codes ? incomingData.tracking_codes.join(', ') : 'Коды не найдены'}</li>
                                <li class="list-group-item"><strong>Инвентарные номера:</strong> ${incomingData.inventory_numbers.join(', ')}</li>
                                <li class="list-group-item"><strong>Количество мест:</strong> ${incomingData.places_count}</li>
                                <li class="list-group-item"><strong>Дата прибытия:</strong> ${incomingData.arrival_date || '-'}</li>
                                <li class="list-group-item"><strong>Размер:</strong> ${incomingData.size || '-'}</li>
                                <li class="list-group-item"><strong>Вес:</strong> ${incomingData.weight || '-'} кг</li>
                                <li class="list-group-item"><strong>Статус:</strong> ${incomingData.status || '-'}</li>
                            </ul>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        consolidationList.appendChild(newItem);
        updateSelectedIncomingsField();
        window.updateInventoryPool(incomingData.id);
        window.createIncomingModal(incomingData);
        console.log("Added incoming to list:", incomingData.id, "Current selectedIncomingsData:", selectedIncomingsData);

        // Обновляем поле client, если выбрано первое поступление
        if (selectedIncomingsData.length === 1 && incomingData.client_phone) {
            clientInput.value = incomingData.client_phone;
            clientInput.readOnly = true;
            console.log("Updated client input with:", incomingData.client_phone, "Client readOnly:", clientInput.readOnly);
        }
    };

    // Удаление поступления из списка
    window.removeIncomingFromList = function (incomingId) {
        const listItem = document.querySelector(`#consolidation-list [data-id="${incomingId}"]`);
        if (listItem) {
            listItem.remove();
            localStorage.removeItem(`incoming_${incomingId}`);
        }

        const checkbox = document.querySelector(`#selection-table input[value="${incomingId}"]`);
        if (checkbox) {
            checkbox.checked = false;
            checkbox.closest('tr').style.display = '';
        } else {
            const incomingData = selectedIncomingsData.find(item => item.id === incomingId);
            if (incomingData) {
                const tableBody = document.querySelector('#selection-table tbody');
                const newRow = document.createElement('tr');
                newRow.innerHTML = `
                    <td><input type="checkbox" class="form-check-input" name="selected_incoming" value="${incomingData.id}"></td>
                    <td><ul>${incomingData.tracking_codes ? incomingData.tracking_codes.map(code => `<li>${code}</li>`).join('') : '<li>Коды не найдены</li>'}</ul></td>
                    <td><ul>${incomingData.inventory_numbers ? incomingData.inventory_numbers.map(number => `<li>${number}</li>`).join('') : '<li>Номера не найдены</li>'}</ul></td>
                    <td>${incomingData.arrival_date || '-'}</td>
                    <td>${incomingData.tag || '-'}</td>
                    <td>${incomingData.client_phone || '-'}</td>
                `;
                tableBody.appendChild(newRow);
                const newCheckbox = newRow.querySelector('input[type="checkbox"]');
                newCheckbox.addEventListener('change', function () {
                    if (this.checked && incomingData) {
                        tempSelectedIncomings.push(incomingData);
                    } else {
                        tempSelectedIncomings = tempSelectedIncomings.filter(item => item.id !== incomingId);
                    }
                });
            }
        }

        selectedIncomingsData = selectedIncomingsData.filter(item => item.id !== incomingId);
        updateSelectedIncomingsField();
        console.log("Removed incoming:", incomingId, "Current selectedIncomingsData:", selectedIncomingsData);

        // Очищаем поле client и снимаем readonly, если больше нет поступлений
        if (selectedIncomingsData.length === 0) {
            clientInput.value = '';
            clientInput.readOnly = false;
            console.log("Cleared client input, Client readOnly:", clientInput.readOnly);
        } else {
            // Устанавливаем client_phone от первого оставшегося поступления
            const firstIncoming = selectedIncomingsData[0];
            if (firstIncoming && firstIncoming.client_phone) {
                clientInput.value = firstIncoming.client_phone;
                clientInput.readOnly = true;
                console.log("Updated client input with:", firstIncoming.client_phone, "Client readOnly:", clientInput.readOnly);
            }
        }

        window.filterRows();
    };

    // Обработка выбора поступлений
    document.querySelectorAll('#selection-table input[name="selected_incoming"]').forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            const incomingId = this.value;
            const incomingData = JSON.parse(document.getElementById('incomingsJson').textContent).find(item => item.id === incomingId);

            if (this.checked && incomingData) {
                tempSelectedIncomings.push(incomingData);
            } else {
                tempSelectedIncomings = tempSelectedIncomings.filter(item => item.id !== incomingId);
            }
            console.log("Checkbox changed, tempSelectedIncomings:", tempSelectedIncomings);
        });
    });

    document.querySelector('[name="consolidation-button"]').addEventListener('click', function () {
        tempSelectedIncomings.forEach(incomingData => {
            window.addIncomingToList(incomingData);
            document.querySelector(`#selection-table input[value="${incomingData.id}"]`).closest('tr').style.display = 'none';
        });
        tempSelectedIncomings = [];
        console.log("Consolidation button clicked, selectedIncomingsData:", selectedIncomingsData);
    });

    // Валидация перед отправкой формы
    form.addEventListener("submit", function (event) {
        // Включаем поле client перед отправкой формы
        if (clientInput) {
            clientInput.disabled = false;
            console.log("Client input enabled, value:", clientInput.value);
        }

        // Проверка, что поле client не пустое
        if (!clientInput.value.trim()) {
            event.preventDefault();
            window.showError("Поле 'Клиент' не может быть пустым.");
            return;
        }

        const allUsedNumbers = new Set();
        const placeNumberMap = new Map();

        document.querySelectorAll(".place-item").forEach(item => {
            const hiddenInput = item.querySelector('input[name^="inventory_numbers_"]');
            const placeCode = item.querySelector('input[name^="place_consolidated_"]').value;
            const numbers = hiddenInput.value.split(",").filter(Boolean);

            placeNumberMap.set(placeCode, numbers);
            numbers.forEach(num => allUsedNumbers.add(num));
        });

        // Проверка уникальности номеров между местами
        const numberToPlaces = new Map();
        placeNumberMap.forEach((numbers, placeCode) => {
            numbers.forEach(num => {
                if (!numberToPlaces.has(num)) {
                    numberToPlaces.set(num, []);
                }
                numberToPlaces.get(num).push(placeCode);
            });
        });

        const duplicateNumbers = [];
        numberToPlaces.forEach((places, num) => {
            if (places.length > 1) {
                duplicateNumbers.push(`Инвентарный номер ${num} используется в местах: ${places.join(", ")}.`);
            }
        });

        if (duplicateNumbers.length > 0) {
            event.preventDefault();
            window.showError(duplicateNumbers.join("<br>"));
            return;
        }

        // Проверка, все ли номера использованы
        const selectedIncomings = document.querySelectorAll("#consolidation-list .list-group-item");
        const allInventoryNumbers = new Set();
        selectedIncomings.forEach(item => {
            const incomingId = item.getAttribute("data-id");
            const storedData = localStorage.getItem(`incoming_${incomingId}`);
            if (storedData) {
                JSON.parse(storedData).forEach(num => allInventoryNumbers.add(num));
            }
        });

        const unusedNumbers = Array.from(allInventoryNumbers).filter(num => !allUsedNumbers.has(num));
        if (unusedNumbers.length > 0) {
            event.preventDefault();
            window.showError(`Следующие инвентарные номера не привязаны ни к одному месту: ${unusedNumbers.join(", ")}.`);
            return;
        }

        // Проверка, что selected_incomings не пустое
        updateSelectedIncomingsField();
        const selectedIncomingsField = document.getElementById('selected-incomings');
        if (!selectedIncomingsField.value) {
            event.preventDefault();
            window.showError("Не выбрано ни одного поступления.");
            return;
        }
    });

    // Инициализация выбранных поступлений
    updateSelectedIncomingsField();

    // Инициализация readonly для поля client при загрузке
    if (selectedIncomingsData.length > 0 && clientInput.value.trim()) {
        clientInput.readOnly = true;
        console.log("Initial client readOnly set to true, value:", clientInput.value);
    } else {
        clientInput.readOnly = false;
        console.log("Initial client readOnly set to false, value:", clientInput.value);
    }

    // Очистка localStorage при закрытии страницы
    window.addEventListener("beforeunload", function () {
        clientInput.disabled = false;
        // localStorage.clear(); // Закомментировано, чтобы сохранить данные при необходимости
    });
});