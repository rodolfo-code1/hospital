// static/js/usuarios_busqueda.js

document.addEventListener("DOMContentLoaded", () => {

    const input = document.getElementById('searchUser');
    const tbody = document.getElementById('tbodyUsuarios');
    const btnSearch = document.querySelector('.btn-search');

    let debounceTimer = null;

    // 🟦 función reutilizable para fetch
    function buscar(q) {
        fetch(`/usuarios/gestion/obtener-usuarios/?q=${q}`)
            .then(response => response.json())
            .then(data => {
                tbody.innerHTML = data.tabla;
            })
            .catch(error => console.error("Error en búsqueda AJAX:", error));
    }

    // 🟦 Evento al escribir
    input.addEventListener('keyup', function () {
        clearTimeout(debounceTimer);

        // Si el campo se vacía → mostrar todo sin esperar
        if (input.value.trim() === "") {
            buscar("");
            return;
        }

        debounceTimer = setTimeout(() => {
            buscar(input.value);
        }, 300);
    });

    // 🟦 Evento al presionar el botón lupa
    btnSearch.addEventListener('click', () => {
        buscar(input.value.trim());
    });
});
