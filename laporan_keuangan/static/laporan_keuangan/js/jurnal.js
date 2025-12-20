document.addEventListener("DOMContentLoaded", function () {
    const tableBody = document.querySelector("#journal-lines tbody");

    tableBody.addEventListener("click", function (e) {
        const row = e.target.closest(".journal-line");

        if (e.target.classList.contains("add-line")) {
            const newRow = row.cloneNode(true);

            // clear inputs
            newRow.querySelectorAll("input").forEach(i => i.value = "");

            tableBody.appendChild(newRow);
        }

        if (e.target.classList.contains("remove-line")) {
            const rows = tableBody.querySelectorAll(".journal-line");

            if (rows.length > 1) {
                row.remove();
            }
        }
    });
});
