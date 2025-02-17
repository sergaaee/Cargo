document.addEventListener("DOMContentLoaded", function () {
    const clientInput = document.getElementById("client-input");
    const clientList = document.getElementById("client-list");

    clientInput.addEventListener("input", async function () {
        const query = clientInput.value.trim();
        if (query.length < 2) return;

        try {
            const response = await fetch(`/incomings/search-users/?q=${query}`);
            if (response.ok) {
                const data = await response.json();
                clientList.innerHTML = "";

                data.forEach(user => {
                    const option = document.createElement("option");
                    option.value = user.phone_number;
                    option.textContent = `${user.full_name} (${user.email}, ${user.phone_number || "Нет телефона"})`;
                    clientList.appendChild(option);
                });
            }
        } catch (error) {
            console.error("Ошибка поиска клиентов:", error);
        }
    });
});
