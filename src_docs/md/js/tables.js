// this_file: src_docs/md/js/tables.js
// Benchmark tables: click a header to sort, type in the box above a table to filter its rows.
// Numeric cells sort by their data-sort value; empty cells (no measurement) always sort last.
// The first click on a numeric column sorts it high to low, on a text column A to Z.
function sortTable(table, th) {
  const col = [...th.parentNode.children].indexOf(th);
  const body = table.tBodies[0];
  const rows = [...body.rows];
  const key = (row) => {
    const cell = row.cells[col];
    const raw = cell.dataset.sort ?? cell.textContent.trim();
    return raw === "" ? null : raw;
  };
  const numeric = rows.every((r) => key(r) === null || !isNaN(parseFloat(key(r))));
  const current = th.getAttribute("aria-sort");
  const dir = current ? (current === "descending" ? 1 : -1) : (numeric ? -1 : 1);
  rows.sort((a, b) => {
    const x = key(a), y = key(b);
    if (x === null || y === null) return (x === null) - (y === null);
    return dir * (numeric ? parseFloat(x) - parseFloat(y) : x.localeCompare(y));
  });
  body.append(...rows);
  th.parentNode.querySelectorAll("th").forEach((h) => h.removeAttribute("aria-sort"));
  th.setAttribute("aria-sort", dir === 1 ? "ascending" : "descending");
}

function setUpTables() {
  document.querySelectorAll(".bench table.sortable").forEach((table) => {
    table.querySelectorAll("thead th").forEach((th) => {
      th.tabIndex = 0;
      th.onclick = () => sortTable(table, th);
      th.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); sortTable(table, th); } };
    });
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

// MaterialX exposes document$ (an observable of page loads); subscribing also covers instant navigation.
if (typeof document$ !== "undefined") document$.subscribe(setUpTables);
else document.addEventListener("DOMContentLoaded", setUpTables);
