document.addEventListener("DOMContentLoaded", function () {
    const clientInput = document.getElementById("client");
    const clientList = document.getElementById("client-list");

    clientInput.addEventListener("input", async function () {
        const query = clientInput.value.trim();
        if (query.length < 2) return;  // Начинаем поиск с 2 символов

        try {
            const response = await fetch(`/incomings/search-users/?q=${query}`);
            if (response.ok) {
                const data = await response.json();

                clientList.innerHTML = ""; // Очистка списка перед добавлением новых результатов

                data.forEach(user => {
                    const option = document.createElement("option");
                    option.value = user.phone_number;  // Вставляем номер телефона
                    option.textContent = `${user.full_name} (${user.email}, ${user.phone_number || "Нет телефона"})`;
                    clientList.appendChild(option);
                });
            } else {
                console.error("Ошибка загрузки данных:", response.statusText);
            }
        } catch (error) {
            console.error("Ошибка запроса:", error);
        }
    });

    // При выборе клиента вставляем номер телефона в input
    clientInput.addEventListener("change", function () {
        const selectedOption = [...clientList.options].find(option => option.value === clientInput.value);
        if (selectedOption) {
            clientInput.value = selectedOption.value; // Устанавливаем номер телефона
        }
    });
});