document.addEventListener('DOMContentLoaded', function () {
    const weightInput = document.querySelector('input[name="weight"]');
    const volumeInput = document.querySelector('input[name="volume"]');
    const densityInput = document.querySelector('input[name="density"]');
    const deliveryTypeSelect = document.querySelector('select[name="delivery_type"]');
    const pricePerKgInput = document.querySelector('input[name="price_per_kg"]');
    const constantInput = document.querySelector('input[name="constant"]');
    const totalPriceInput = document.querySelector('input[name="total_price"]');
    const packagePriceInput = document.querySelector('input[name="package_price"]');

    function parseFloatSafe(val) {
        return parseFloat(val) || 0;
    }

    function calculateTotalPrice() {
        const weight = parseFloatSafe(weightInput.value);
        const pricePerKg = parseFloatSafe(pricePerKgInput.value);
        const constant = parseFloatSafe(constantInput.value);
        const packagePrice = parseFloatSafe(packagePriceInput.value)
        const total = (packagePrice + weight * pricePerKg) * constant;
        if (!isNaN(total)) {
            totalPriceInput.value = total.toFixed(2);
        }
    }

    async function updateTariff() {
        const density = parseFloatSafe(densityInput.value);
        const deliveryTypeId = deliveryTypeSelect.options[deliveryTypeSelect.selectedIndex].text.trim();

        if (density === null || !deliveryTypeId) {
            pricePerKgInput.value = '';
            totalPriceInput.value = '';
            return;
        }

        try {
            const response = await fetch(`/incomings/get_tariff?density=${density}&delivery_type=${deliveryTypeId}`);
            if (!response.ok) throw new Error('Ошибка сервера');
            const data = await response.json();
            const price = parseFloatSafe(data.price_per_kg);

            pricePerKgInput.value = parseFloatSafe(price).toFixed(2);
            calculateTotalPrice();
        } catch (error) {
            console.error('Ошибка при получении тарифа:', error);
            pricePerKgInput.value = '';
            totalPriceInput.value = '';
        }
    }

    weightInput.addEventListener('input', () => {
        updateTariff();
    });

    volumeInput.addEventListener('input', () => {
        updateTariff();
    });

    deliveryTypeSelect.addEventListener('change', () => {
        updateTariff();
    });

    packagePriceInput.addEventListener('input', () => {
        calculateTotalPrice()
    });

    pricePerKgInput.addEventListener('input', () => {
        calculateTotalPrice()
    })

    constantInput.addEventListener('input', () => {
        calculateTotalPrice();
    });
});