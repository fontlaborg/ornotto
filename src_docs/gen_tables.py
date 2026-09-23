#!/usr/bin/env python3
# this_file: src_docs/gen_tables.py
"""Render the benchmark data in src_docs/data/*.json as HTML table snippets in src_docs/md/tables/.

Chapters include them with `--8<-- "tables/<name>.html"`. Every table is sortable (md/js/tables.js):
numeric cells carry `data-sort` so "62/67" and "1,234" sort as numbers, and empty cells, meaning "not
measured", sort last. Tables marked filterable get a text box that hides rows not matching what you type.
"""

from __future__ import annotations

import html
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "md" / "tables"
QUANT_ORDER = [
    "iq1",
    "q1",
    "q2",
    "iq2",
    "q3",
    "iq3",
    "q4",
    "iq4",
    "q5",
    "q6",
    "q8",
    "int8",
    "w8",
    "fp16",
    "f16",
    "bf16",
    "fp32",
]
TASKS = 67


def load(name: str):
    return json.loads((DATA / f"{name}.json").read_text())


def cell(value, sort=None, cls: str = "") -> str:
    attrs = f' data-sort="{sort}"' if sort is not None else ""
    attrs += f' class="{cls}"' if cls else ""
    return f"<td{attrs}>{html.escape(str(value))}</td>"


def num(value, digits: int = 0, suffix: str = "") -> str:
    if value is None:
        return '<td class="num"></td>'
    text = f"{value:,.{digits}f}{suffix}"
    return cell(text, value, "num")


def score(value: int, total: int = TASKS) -> str:
    return cell(f"{value}/{total}", value, "num score")


def table(
    name: str,
    headers: list[str],
    rows: list[str],
    caption: str = "",
    filterable: bool = False,
    sorted_by: str | None = None,
) -> None:
    """Write one table. `sorted_by` names the column the rows are already sorted by, high to low."""
    if not caption and len(rows) >= 15:
        caption = "Click a column header to sort."
    head = "".join(
        f'<th aria-sort="descending">{html.escape(h)}</th>'
        if h == sorted_by
        else f"<th>{html.escape(h)}</th>"
        for h in headers
    )
    body = "\n".join(f"<tr>{r}</tr>" for r in rows)
    box = (
        (
            f'<input class="table-filter" type="search" placeholder="Filter {len(rows)} rows" '
            f'aria-label="Filter the table" data-table="{name}">\n'
        )
        if filterable
        else ""
    )
    cap = f"<caption>{html.escape(caption)}</caption>" if caption else ""
    text = (
        f'<div class="bench" markdown="0">\n{box}<table class="sortable" id="{name}">{cap}'
        f"<thead><tr>{head}</tr></thead>\n<tbody>\n{body}\n</tbody></table>\n</div>\n"
    )
    (OUT / f"{name}.html").write_text(text)


def classifier_rows(rows: list[dict]) -> list[str]:
    out = []
    for r in rows:
        out.append(
            "".join(
                [
                    cell(r["method"], cls="method"),
                    cell(r["engine"]),
                    cell(r["model"]),
                    cell(r["family"]),
                    cell(r["quant"]),
                    num(r["gb"], 2),
                    num(r["ms"], 1),
                    score(r["translated"]),
                    score(r["direct"]),
                    score(r["translated_en"], 28),
                    score(r["translated_other"], 39),
                    score(r["direct_other"], 39),
                    num(r["load_ms"]),
                ]
            )
        )
    return out


CLASSIFIER_HEADERS = [
    "Method",
    "Engine",
    "Model",
    "Family",
    "Quant",
    "GB",
    "ms/query",
    "Translated",
    "Direct",
    "English",
    "Other, translated",
    "Other, direct",
    "Load ms",
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = load("classifiers")

    table(
        "classifiers",
        CLASSIFIER_HEADERS,
        classifier_rows(rows),
        filterable=True,
        caption="All 208 methods, best first. Click a header to sort; empty cells were not measured.",
        sorted_by="Translated",
    )
    top = sorted(rows, key=lambda r: (-r["translated"], -r["direct"], r["ms"]))[:15]
    table(
        "top",
        CLASSIFIER_HEADERS[1:9],
        [
            "".join(
                [
                    cell(r["engine"]),
                    cell(r["model"]),
                    cell(r["family"]),
                    cell(r["quant"]),
                    num(r["gb"], 2),
                    num(r["ms"], 1),
                    score(r["translated"]),
                    score(r["direct"]),
                ]
            )
            for r in top
        ],
        caption="The 15 best methods by translated score, then direct score, then speed. Click to sort.",
        sorted_by="Translated",
    )

    # One model, many engines: the decider-0.8b and decider-2b rows side by side.
    same = [
        r
        for r in rows
        if r["model"]
        in (
            "decider-0.8b",
            "decider-0.8b-dreamblooms",
            "decider-2b",
            "decider-2b-dreamblooms",
            "decider-35b-a3b",
            "decider-4b",
        )
    ]
    same.sort(key=lambda r: (r["model"], r["quant"], r["ms"]))
    table(
        "engines-same-model",
        ["Model", "Quant", "Engine", "ms/query", "Translated", "Direct"],
        [
            "".join(
                [
                    cell(r["model"]),
                    cell(r["quant"]),
                    cell(r["engine"]),
                    num(r["ms"], 1),
                    score(r["translated"]),
                    score(r["direct"]),
                ]
            )
            for r in same
        ],
        filterable=True,
    )

    # Families by kind: the best row of each model.
    best: dict[str, dict] = {}
    for r in rows:
        if r["model"] not in best or (r["translated"], -r["ms"]) > (
            best[r["model"]]["translated"],
            -best[r["model"]]["ms"],
        ):
            best[r["model"]] = r
    fam = sorted(best.values(), key=lambda r: (r["family"], -r["translated"], r["ms"]))
    table(
        "families",
        ["Family", "Model", "Engine", "GB", "ms/query", "Translated", "Direct", "Best method"],
        [
            "".join(
                [
                    cell(r["family"]),
                    cell(r["model"]),
                    cell(r["engine"]),
                    num(r["gb"], 2),
                    num(r["ms"], 1),
                    score(r["translated"]),
                    score(r["direct"]),
                    cell(r["method"], cls="method"),
                ]
            )
            for r in fam
        ],
        filterable=True,
    )

    # Quantization sweeps: models with four or more quantizations on one engine, as a model x quant grid.
    grid: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)
    for r in rows:
        if r["quant"]:
            grid[(r["model"], r["engine"])][r["quant"]] = r
    sweeps = {k: v for k, v in grid.items() if len(v) >= 4}
    quants = [q for q in QUANT_ORDER if any(q in v for v in sweeps.values())]
    sweep_rows = []
    for (model, engine), by_q in sorted(sweeps.items()):
        cells = [cell(model), cell(engine)]
        for q in quants:
            r = by_q.get(q)
            cells.append(
                cell(f"{r['translated']} · {r['ms']:.0f} ms", r["translated"], "num")
                if r
                else '<td class="num"></td>'
            )
        sweep_rows.append("".join(cells))
    table(
        "quant-sweeps",
        ["Model", "Engine", *quants],
        sweep_rows,
        filterable=True,
        caption="Translated score out of 67 and mean ms per query, per quantization",
    )

    queries = load("queries")
    hard = sorted(queries, key=lambda q: q["translated_share"])
    table(
        "queries",
        ["Query", "Lang", "Task", "Right, translated", "Right, direct", "jev"],
        [
            "".join(
                [
                    cell(q["query"], cls="query"),
                    cell(q["lang"]),
                    cell(q["task"]),
                    num(q["translated_share"] * 100, 0, " %"),
                    num(q["direct_share"] * 100, 0, " %"),
                    cell(q["jev_translated"] or ""),
                ]
            )
            for q in hard
        ],
        filterable=True,
    )

    table(
        "translator",
        ["Query", "Lang", "English", "ms"],
        [
            "".join(
                [
                    cell(t["query"], cls="query"),
                    cell(t["lang"]),
                    cell(t["english"], cls="query"),
                    num(t["ms"], 0),
                ]
            )
            for t in load("translator")
        ],
        filterable=True,
    )
    table(
        "detectors",
        ["Detector", "Correct", "Mean µs", "Calls/s"],
        [
            "".join(
                [cell(d["detector"]), score(d["correct"]), num(d["mean_us"], 1), num(d["calls_per_s"], 0)]
            )
            for d in load("detectors")
        ],
    )

    cascade = load("cascade")
    for mode in ("translated", "direct"):
        c = cascade[mode]
        table(
            f"cascade-{mode}",
            ["Gate: top probability below", "Fallbacks", "Correct", "Mean ms"],
            [
                "".join(
                    [
                        num(s["threshold"], 2),
                        cell(f"{s['fallbacks']}/{c['n']}", s["fallbacks"], "num"),
                        score(s["correct"]),
                        num(s["ms"], 1),
                    ]
                )
                for s in c["sweep"]
            ],
        )
        buckets = [
            ("<0.6", "below 0.6"),
            ("0.6-0.8", "0.6 to 0.8"),
            ("0.8-0.95", "0.8 to 0.95"),
            (">=0.95", "0.95 and up"),
        ]
        table(
            f"calibration-{mode}",
            ["Top probability", "Answers", "Right", "Share right"],
            [
                "".join(
                    [
                        cell(label),
                        num(c["calibration"][k][0]),
                        num(c["calibration"][k][1]),
                        num(100 * c["calibration"][k][1] / c["calibration"][k][0], 0, " %"),
                    ]
                )
                for k, label in buckets
                if k in c["calibration"]
            ],
        )
    print(f"wrote {len(list(OUT.glob('*.html')))} tables to {OUT}")


if __name__ == "__main__":
    main()
