document.addEventListener("click", function (e) {

    // ADD ROW
    if (e.target.closest(".js-add-row")) {
        const currentRow = e.target.closest(".journal-row");
        const newRow = currentRow.cloneNode(true);

        // clear inputs
        newRow.querySelectorAll("input").forEach(i => i.value = "");
        newRow.querySelectorAll("select").forEach(s => s.selectedIndex = 0);

        currentRow.after(newRow);
    }

    // REMOVE ROW
    if (e.target.closest(".js-remove-row")) {
        const rows = document.querySelectorAll(".journal-row");

        // prevent deleting the last row
        if (rows.length === 1) {
            return; // do nothing
        }

        e.target.closest(".journal-row").remove();
    }
    function updateRemoveButtons() {
        const rows = document.querySelectorAll(".journal-row");
        const disable = rows.length === 1;

        rows.forEach(row => {
            row.querySelector(".js-remove-row").disabled = disable;
        });
    }

// call this after add/remove

});
