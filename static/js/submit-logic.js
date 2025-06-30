document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");
    const cancelButton = document.querySelector(".btn-secondary");

    const alertBox = document.createElement("div");
    alertBox.classList.add("alert", "alert-danger", "d-none");
    form.prepend(alertBox);

    form.addEventListener("submit", function (event) {
        event.preventDefault();  // ❌ Останавливаем стандартную отправку формы

        const submitter = event.submitter;
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = submitter.name;
        input.value = submitter.value;
        form.appendChild(input);

        var trackerInventoryMap = JSON.parse(localStorage.getItem("trackerInventoryMap")) || {};
        var trackerCodes = Object.keys(trackerInventoryMap);
        var inventoryNumbers = Object.values(trackerInventoryMap);

        let uiTrackers = Array.from(document.querySelectorAll("#selected-trackers .selected-tracker"))
            .map(el => el.textContent.replace("×", "").trim()); // Убираем символ удаления

        // 📌 Находим трек-коды без инвентарных номеров
        let emptyTrackers = uiTrackers.filter(tracker =>
            !trackerCodes.includes(tracker) || !trackerInventoryMap[tracker] || trackerInventoryMap[tracker].length === 0
        );

        if (emptyTrackers.length > 0) {
            alert(`❌ Внимание: Трек-код(ы) ${emptyTrackers.join(", ")} не содержат ни одного инвентарного номера!`);
            return false;
        }

        const trackerCodesInput = document.getElementById("selected-trackers-input");
        if (trackerCodesInput) {
            trackerCodesInput.value = trackerCodes.join(",");
        }

        const selectedInventoryInput = document.getElementById("selected-inventory-input");
        if (selectedInventoryInput) {
            selectedInventoryInput.value = inventoryNumbers.join(",");
        }

        trackerInventoryMap = JSON.stringify(trackerInventoryMap);
        document.getElementById("tracker_inventory_map_input").value = trackerInventoryMap;

        // 📌 Отправляем AJAX-запрос
        const formData = new FormData(form);

        fetch(form.action, {
            method: "POST",
            body: formData
        })
            .then(response => response.text())  // Ожидаем текст (может быть HTML или JSON)
            .then(text => {
                try {
                    const data = JSON.parse(text);  // Пытаемся разобрать как JSON
                    if (data.success) {
                        localStorage.removeItem("trackerInventoryMap");  // Удаляем localStorage после сабмита
                        window.location.href = data.redirect_url;
                    } else {
                        alertBox.innerHTML = data.errors.join("<br>");
                        alertBox.classList.remove("d-none");
                        window.scrollTo({top: 0, behavior: "smooth"});
                    }
                } catch (error) {
                    console.error("Ошибка обработки JSON:", text);
                    alertBox.innerHTML = "Произошла ошибка сервера. Проверьте консоль.";
                    alertBox.classList.remove("d-none");
                }
            })
            .catch(error => {
                alertBox.innerHTML = "Ошибка соединения с сервером.";
                alertBox.classList.remove("d-none");
                console.error("Ошибка отправки формы:", error);
            });


    });

    // Очищаем localStorage при нажатии "Отмена"
    cancelButton.addEventListener("click", function () {
        localStorage.removeItem("trackerInventoryMap");
    });
});
