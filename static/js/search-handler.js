document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.querySelector('input[name="q"]');
    const tableRows = document.querySelectorAll("tbody tr");

    searchInput.addEventListener("input", function () {
        const query = this.value.toLowerCase().trim();
        tableRows.forEach(row => {
            const rowText = row.innerText.toLowerCase();
            row.style.display = rowText.includes(query) ? "" : "none";
        });
    });
});