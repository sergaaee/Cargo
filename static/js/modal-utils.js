function openIncomingModal(incomingId) {
    const modalElement = document.getElementById(`incomingDetailModal${incomingId}`);
    if (modalElement) {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    } else {
        console.error("Модальное окно не найдено для ID:", incomingId);
    }
}

window.createIncomingModal = function (incomingData) {
    if (document.getElementById(`incomingModal${incomingData.id}`)) return;

    let modalHtml = `
        <div class="modal fade" id="incomingModal${incomingData.id}" tabindex="-1" aria-labelledby="incomingModalLabel${incomingData.id}" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="incomingModalLabel${incomingData.id}">Детали поступления #${incomingData.id}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <h6>Трек-коды и их инвентарные номера:</h6>
                        <ul>`;
    if (incomingData.track_inv_map && incomingData.track_inv_map.length > 0) {
        incomingData.track_inv_map.forEach(tracker => {
            modalHtml += `
                <li><strong>${tracker.code}</strong>
                    <ul>`;
            if (tracker.inventory_numbers && tracker.inventory_numbers.length > 0) {
                tracker.inventory_numbers.forEach(inventory => {
                    const isChecked = isInventoryChecked(incomingData.id, inventory) ? "checked" : "";
                    modalHtml += `
                        <li>
                            <input type="checkbox" class="inventory-checkbox"
                                   data-incoming-id="${incomingData.id}"
                                   data-inventory-number="${inventory}" ${isChecked}>
                            ${inventory}
                        </li>`;
                });
            } else {
                modalHtml += `<li>Нет связанных инвентарных номеров</li>`;
            }
            modalHtml += `</ul></li>`;
        });
    } else {
        modalHtml += `<li>Нет трек-кодов</li>`;
    }

    modalHtml += `
                    </ul>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
                </div>
            </div>
        </div>
    </div>`;

    document.body.insertAdjacentHTML("beforeend", modalHtml);
};

function isInventoryChecked(incomingId, inventoryNumber) {
    const storedData = localStorage.getItem(`incoming_${incomingId}`);
    return storedData ? JSON.parse(storedData).includes(inventoryNumber) : false;
}