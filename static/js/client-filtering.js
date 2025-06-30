document.addEventListener("DOMContentLoaded", function () {
    const clientInput = document.getElementById("client");
    const selectionTable = document.getElementById("selection-table");
    const selectedIncomingsData = JSON.parse(document.getElementById('initialIncomingsJson').textContent) || [];
    const selectedIncomingsIds = selectedIncomingsData.map(item => item.id);

    // Установка начального состояния readonly
    if (selectedIncomingsIds.length > 0 && clientInput.value.trim()) {
        clientInput.readOnly = true;
        console.log("Initial client readOnly set to true, value:", clientInput.value);
    } else {
        clientInput.readOnly = false;
        console.log("Initial client readOnly set to false, value:", clientInput.value);
    }

    // Фильтрация строк таблицы в модальном окне
    window.filterRows = function () {
        console.log("Filtering rows with client value:", clientInput.value);
        const clientValue = clientInput.value.trim().toLowerCase();
        const rows = selectionTable.querySelectorAll("tbody tr:not(#no-results-message)");
        let visibleRows = 0;

        rows.forEach(row => {
            const clientCell = row.cells[row.cells.length - 1]; // Последний столбец (phone_number)
            const clientText = clientCell ? clientCell.textContent.trim().toLowerCase() : "";
            const matches = clientText.includes(clientValue) || clientValue === "";
            row.style.display = matches ? "" : "none";
            if (matches) visibleRows++;
        });

        let noResultsMessage = document.getElementById("no-results-message");
        if (!noResultsMessage) {
            noResultsMessage = document.createElement("tr");
            noResultsMessage.id = "no-results-message";
            noResultsMessage.innerHTML = `<td colspan="${selectionTable.querySelector('thead tr').cells.length}" class="text-center fw-bold">Не найдено поступлений для этого клиента</td>`;
            selectionTable.querySelector("tbody").appendChild(noResultsMessage);
        }
        noResultsMessage.style.display = visibleRows === 0 && clientValue ? "" : "none";
    };

    // Запуск фильтрации при вводе в поле client
    clientInput.addEventListener("input", window.filterRows);

    // Запуск фильтрации при открытии модального окна
    document.getElementById("consolidationModal").addEventListener("shown.bs.modal", window.filterRows);

    // Начальная фильтрация, если поле client не пустое
    if (clientInput.value.trim()) {
        window.filterRows();
    }
});

// Функция для показа сообщения об ошибке
window.showError = function (message) {
    let alertBox = document.getElementById("custom-alert-box");
    if (!alertBox) {
        alertBox = document.createElement("div");
        alertBox.id = "custom-alert-box";
        alertBox.className = "alert alert-danger mt-3";
        alertBox.style.position = "fixed";
        alertBox.style.top = "20px";
        alertBox.style.right = "20px";
        alertBox.style.zIndex = "1050";
        document.body.appendChild(alertBox);
    }
    alertBox.innerHTML = message;
    alertBox.style.display = "block";

    setTimeout(() => {
        alertBox.style.display = "none";
    }, 5000);
};