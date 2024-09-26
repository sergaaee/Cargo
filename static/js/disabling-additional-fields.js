var places_count_el = document.getElementById("id_places_count");
var weight_el = document.getElementById("id_weight");
var size_el = document.getElementById('id_size');

places_count_el.onchange = function () {
    var is_multiple_places = places_count_el.value > 1;

    console.log(weight_el.value);
    weight_el.value = is_multiple_places ? 1 : weight_el.value;
    weight_el.disabled = is_multiple_places;
    size_el.disabled = is_multiple_places;
};