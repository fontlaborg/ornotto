// this_file: src_docs/md/js/tables.js
// Sort every benchmark table by clicking a header (tablesort reads data-sort), and filter rows as you type.
// MaterialX swaps pages without reloading, so this runs on every page change via document$.
function setUpTables() {
  document.querySelectorAll(".bench table.sortable").forEach((table) => {
    if (!table.dataset.sortReady) {
      new Tablesort(table);
      table.dataset.sortReady = "1";
    }
  });
  document.querySelectorAll(".bench .table-filter").forEach((input) => {
    const table = document.getElementById(input.dataset.table);
    input.oninput = () => {
      const words = input.value.toLowerCase().split(/\s+/).filter(Boolean);
      table.querySelectorAll("tbody tr").forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.hidden = !words.every((w) => text.includes(w));
      });
    };
  });
}
if (typeof document$ !== "undefined") {
  document$.subscribe(setUpTables);
} else {
  document.addEventListener("DOMContentLoaded", setUpTables);
}
