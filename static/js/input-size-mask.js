document.addEventListener("DOMContentLoaded", function() {
        var sizeInput = document.querySelector('input[name="size"]');
        if (sizeInput) {
            Inputmask({
                mask: "999x999x999",  // Маска для поля ввода
                placeholder: "0",  // По умолчанию вводятся нули
                definitions: {
                    '999': {  // Определение для цифры
                        validator: "[0-999]",  // Разрешены только цифры
                        cardinality: 1,
                        placeholder: "0"
                    }
                },
                keepStatic: true  // Символы "x" остаются постоянными
            }).mask(sizeInput);
        }
    });