document.addEventListener("DOMContentLoaded", function() {
        var dateInput = document.querySelector('input[name="consolidation_date"]');
        if (dateInput) {
            var now = new Date();
            var year = now.getFullYear();
            var month = ('0' + (now.getMonth() + 1)).slice(-2);
            var day = ('0' + now.getDate()).slice(-2);
            var hours = ('0' + now.getHours()).slice(-2);
            var minutes = ('0' + now.getMinutes()).slice(-2);

            dateInput.value = year + '-' + month + '-' + day + 'T' + hours + ':' + minutes;
        }
    });