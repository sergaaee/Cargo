document.addEventListener("DOMContentLoaded", function() {
        const inventoryInput = document.getElementById('inventory-input');
        const selectedInventoryContainer = document.getElementById('selected-inventory-numbers');
        const selectedInventoryInput = document.getElementById('selected-inventory-input');

        // Массив для хранения выбранных инвентарных номеров
        let selectedInventoryNumbers = [];

        // Функция для обновления отображения выбранных инвентарных номеров и скрытого поля
        function updateSelectedInventoryNumbers() {
            selectedInventoryContainer.innerHTML = '';
            selectedInventoryInput.value = selectedInventoryNumbers.join(',');  // Обновляем скрытое поле

            selectedInventoryNumbers.forEach((number, index) => {
                const inventoryDiv = document.createElement('div');
                inventoryDiv.classList.add('selected-inventory', 'badge', 'bg-primary', 'me-1', 'mb-1');
                inventoryDiv.textContent = number;

                // Добавляем крестик для удаления
                const removeBtn = document.createElement('span');
                removeBtn.classList.add('ms-2', 'text-white', 'cursor-pointer');
                removeBtn.innerHTML = '&times;';
                removeBtn.style.cursor = 'pointer';

                // Добавляем событие для удаления инвентарного номера
                removeBtn.addEventListener('click', () => {
                    selectedInventoryNumbers.splice(index, 1);  // Удаляем выбранный инвентарный номер из массива
                    updateSelectedInventoryNumbers();  // Обновляем отображение
                });

                inventoryDiv.appendChild(removeBtn);
                selectedInventoryContainer.appendChild(inventoryDiv);
            });
        }

        // Событие при выборе инвентарного номера
        inventoryInput.addEventListener('change', function() {
            const selectedNumber = inventoryInput.value.trim();

            // Проверяем, что номер не пустой и не выбран ранее
            if (selectedNumber && !selectedInventoryNumbers.includes(selectedNumber)) {
                selectedInventoryNumbers.push(selectedNumber);
                updateSelectedInventoryNumbers();
            }

            // Очищаем поле ввода для следующего ввода
            inventoryInput.value = '';
        });
    });
