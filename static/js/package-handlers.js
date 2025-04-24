// static/js/package-handlers.js
class PackageHandlers {
    constructor() {
        this.inventoryNumbersElement = document.getElementById("inventory-numbers");
        this.allInventoryNumbers = this.inventoryNumbersElement ?
            JSON.parse(this.inventoryNumbersElement.textContent) : [];
        this.inventoryPool = document.getElementById("inventory-numbers-pool");
        this.form = document.getElementById("consolidation-form");
        this.consolidationList = document.getElementById("consolidation-list");
        this.availableNumbers = new Set(this.allInventoryNumbers);
        this.itemToDelete = null;

        this.init();
    }

    init() {
        this.initializeFirstItem();
        this.setupEventListeners();
    }

    setPlaceCode(item, index) {
        const placeInput = item.querySelector('input[name^="place_consolidated_"]');
        const trackCodeInput = document.querySelector('input[name="track_code"]');
        const trackCode = trackCodeInput ? trackCodeInput.value : '';

        if (placeInput && trackCode) {
            placeInput.value = `${trackCode}-${index + 1}`;
        }
    }

    updateInventoryPool() {
        this.inventoryPool.innerHTML = Array.from(this.availableNumbers)
            .map(num => `<span class="badge bg-secondary me-1">${num}</span>`)
            .join('');
    }

    createNewItem(index) {
        // Логика создания новой строки для упаковки
        // ... (весь существующий код создания элемента)
    }

    setupInventoryInput(input) {
        // Логика обработки ввода инвентарных номеров
        // ... (весь существующий код обработки)
    }

    validateForm() {
        // Логика валидации формы упаковки
        // ... (весь существующий код валидации)
        return true;
    }

    setupEventListeners() {
        this.consolidationList.addEventListener("click", (event) => {
            const addBtn = event.target.closest(".add-item-btn");
            const deleteBtn = event.target.closest(".delete-item-btn");

            if (addBtn) {
                // Логика добавления новой строки
            }

            if (deleteBtn) {
                // Логика удаления строки
            }
        });

        document.getElementById("confirmDeleteBtn")?.addEventListener("click", () => {
            // Логика подтверждения удаления
        });

        this.form.addEventListener("submit", (event) => {
            CommonHandlers.handleFormSubmit(event, () => this.validateForm());
        });
    }
}