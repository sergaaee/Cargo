// static/js/common-handlers.js
class CommonHandlers {
    static initDateTimePicker() {
        // Общая логика инициализации datetime picker
        const dateInputs = document.querySelectorAll('input[type="datetime-local"]');
        dateInputs.forEach(input => {
            const now = new Date();
            input.value = now.toISOString().slice(0, 16);
        });
    }

    static showError(message) {
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
    }

    static handleFormSubmit(event, validateCallback) {
        event.preventDefault();
        const form = event.target;
        const submitter = event.submitter;

        const input = document.createElement("input");
        input.type = "hidden";
        input.name = submitter.name;
        input.value = submitter.value;
        form.appendChild(input);

        if (validateCallback && !validateCallback()) {
            return;
        }

        const formData = new FormData(form);

        fetch(form.action, {
            method: "POST",
            body: formData
        })
        .then(response => response.text())
        .then(text => {
            try {
                const data = JSON.parse(text);
                if (data.success) {
                    localStorage.removeItem("trackerInventoryMap");
                    window.location.href = data.redirect_url;
                } else {
                    this.showError(data.errors.join("<br>"));
                }
            } catch (error) {
                console.error("Ошибка обработки JSON:", text);
                this.showError("Произошла ошибка сервера. Проверьте консоль.");
            }
        })
        .catch(error => {
            this.showError("Ошибка соединения с сервером.");
            console.error("Ошибка отправки формы:", error);
        });
    }
}