document.addEventListener("DOMContentLoaded", function() {
    const trackerInput = document.getElementById('tracker-input');
    const selectedTrackersContainer = document.getElementById('selected-trackers');
    const selectedTrackersInput = document.getElementById('selected-trackers-input');

    let selectedTrackers = [];

    function updateSelectedTrackers() {
        selectedTrackersContainer.innerHTML = '';
        selectedTrackersInput.value = selectedTrackers.join(',');  // Обновляем скрытое поле

        selectedTrackers.forEach((code, index) => {
            const trackerDiv = document.createElement('div');
            trackerDiv.classList.add('selected-tracker', 'badge', 'bg-primary', 'me-1', 'mb-1');
            trackerDiv.textContent = code;

            const removeBtn = document.createElement('span');
            removeBtn.classList.add('ms-2', 'text-white', 'cursor-pointer');
            removeBtn.innerHTML = '&times;';
            removeBtn.style.cursor = 'pointer';

            removeBtn.addEventListener('click', () => {
                selectedTrackers.splice(index, 1);  // Удаляем выбранный код из массива
                updateSelectedTrackers();  // Обновляем отображение
            });

            trackerDiv.appendChild(removeBtn);
            selectedTrackersContainer.appendChild(trackerDiv);
        });
    }

    trackerInput.addEventListener('change', function() {
        const selectedCode = trackerInput.value.trim();

        if (selectedCode && !selectedTrackers.includes(selectedCode)) {
            selectedTrackers.push(selectedCode);
            updateSelectedTrackers();
        }

        trackerInput.value = '';  // Очищаем поле ввода для следующего ввода
    });

    // Обновляем скрытое поле непосредственно перед отправкой формы
    document.querySelector('form').addEventListener('submit', function() {
        selectedTrackersInput.value = selectedTrackers.join(',');
    });
});
