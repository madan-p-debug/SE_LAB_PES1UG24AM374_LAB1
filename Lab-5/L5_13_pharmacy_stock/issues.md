# Lab 5: Static Code Analysis — Issue Report

**Name:** Madan P  |  **SRN:** PES1UG24AM374  |  **Repo:** L5_13_pharmacy_stock  |  **File:** `pharmacy_system.py`

Line numbers refer to the **original** file. "Tool" shows which analyser reported the issue; *Manual* means I found it by running the program and none of the tools flagged it.

## Issue table

| # | Issue | Type | Severity | Tool | Line(s) | Description | Fix Approach |
|---|-------|------|----------|------|---------|-------------|--------------|
| 1 | SQL injection | Security | **Medium** | Bandit B608 (also Pylint C0209) | 21 | Query built with `%` string formatting. Input `x' OR '1'='1` returned **all three patients** (ids and allergies). | Parameterised query: `WHERE name = ?` with `cur.execute(query, (name,))`. The same input now returns `[]`. |
| 2 | Silent `try / except / pass` when loading stock | Security / Bug | Low | Bandit B110, Pylint W0702, Flake8 E722 | 56-59 | Bare `except` + `pass` hid every error (missing file, corrupt JSON, permissions) so the program carried on with bad data. | Catch only `FileNotFoundError` and `json.JSONDecodeError`, print a clear message, and leave stock unchanged. |
| 3 | Bare `except` in `dispense()` | Bug | High (hides failures) | Pylint W0702, Flake8 E722 | 38-39 | Swallowed every error: unknown patient (`IndexError`), drug not in stock (`KeyError`), bad dates. Caller only saw `False` with no reason. | Removed the blanket `try`. Each failure case is checked explicitly and prints a specific message (unknown patient, drug not in stock, expired, insufficient stock). |
| 4 | Mutable default argument | Bug | Medium | Pylint W0102 | 24 | `batch_log=[]` is created once and shared by every call, so the log grows across unrelated calls. | `batch_log=None`, create a new list inside the function when it is `None`. |
| 5 | Allergy check wrong | Logic bug (patient safety) | **High** | *Manual* | 32 | `drug in patient[1]` is a case-sensitive substring test. `"Penicillin" in "penicillin"` is `False`, so **Kavya (allergic to penicillin) was given Penicillin** (`True`). Substring matching could also give false matches. | Compare normalised values: `drug.lower() == allergy.lower()`. Kavya is now blocked for `Penicillin` and `PENICILLIN`. |
| 6 | Stock can go negative / negative stock accepted | Logic bug | High | *Manual* | 35, 72 | Arjun was dispensed 30 Amoxicillin from 20 in stock, leaving **-10 units**. `add_stock("Ibuprofen", -15, ...)` created a stock of -15. | `add_stock` raises `ValueError` for `units <= 0`; `dispense` refuses when `units <= 0` or stock is insufficient. |
| 7 | Expired medicine can be dispensed | Logic bug (patient safety) | High | *Manual* | 35 | Amoxicillin (expiry 2025-12-31) was dispensed even though it is expired. | `dispense` parses the expiry date and refuses expired drugs. |
| 8 | New batch overwrites expiry date | Logic bug | Medium | *Manual* | 25 | Adding stock replaced the expiry of existing units with the new batch's date, hiding that older units expire sooner. | Keep the earlier of the two expiry dates (`min(expiry, current["expiry"])`). |
| 9 | File not closed safely, no encoding | Code quality | Medium | Pylint R1732, W1514 | 50-52, 57 | `open()` / `close()` by hand leaks the handle if `write` fails; `json.load(open(file))` never closes at all; no `encoding`. | `with open(..., encoding="utf-8")` and `json.dump(...)` directly. |
| 10 | Global statement | Code quality | Low | Pylint W0603 | 55 | `global stock` rebinds module state inside `load_stock`. | Update the dict in place (`stock.clear(); stock.update(loaded)`). |
| 11 | Unused import | Code quality | Low | Pylint W0611, Flake8 F401 | 3 | `import os` is never used. | Removed. |
| 12 | Non-snake_case function name | Style | Low | Pylint C0103 | 61 | `printStock` breaks PEP 8 naming. | Renamed to `print_stock`. |
| 13 | Missing docstrings | Style | Low | Pylint C0114, C0116 | 1, 11, 19, 24, 29, 41, 49, 54, 61, 66 | Module and all 9 functions undocumented. | Added module and function docstrings. |
| 14 | Line too long | Style | Low | Pylint C0301, Flake8 E501 | 25, 36 | 90 and 112 characters. | Wrapped lines to 79 characters. |
| 15 | Blank-line formatting | Style | Low | Flake8 E302, E305 | 11, 19, 24, 29, 41, 49, 54, 61, 66, 83 | Only one blank line between top-level definitions. | Two blank lines around every top-level function. |
| 16 | `main()` runs on import | Design | Low | *Manual* | 83 | Importing the module executed the whole demo, so it can't be imported or tested. | `if __name__ == "__main__": main()`. |

## Tool results before and after

| Tool | Before | After |
|------|--------|-------|
| Pylint | **6.90 / 10** (22 messages) | **10.00 / 10** |
| Bandit | 1 Medium, 1 Low | **0 issues** |
| Flake8 | 15 violations | **0 violations** |

Reports are in `reports/before/` and `reports/after/`.

## Commits

| Commit | Tool | Changes |
|--------|------|---------|
| 1 | Bandit | Issues 1-2 (+ baseline reports) |
| 2 | Pylint | Issues 3-13 and 16, including the logic bugs 5-8 |
| 3 | Flake8 | Issues 14-15 (+ final reports) |

## Behaviour change in the demo output

With today's date, the sample Amoxicillin batch (expiry 2025-12-31) is expired, so the demo now correctly refuses to dispense it. Kavya/Penicillin and Meena/ibuprofen are blocked by the allergy check, and Ghost is reported as an unknown patient. `expiring_soon()` still lists already-expired stock.
