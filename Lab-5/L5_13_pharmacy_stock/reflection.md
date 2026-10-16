# Reflection

**Name:** Madan P  |  **SRN:** PES1UG24AM374

## 1. Which issues were the easiest to fix, and which were the hardest?

The easiest were the mechanical ones: removing the unused `os` import, renaming `printStock`, adding docstrings and fixing the blank-line and line-length errors. The tools say exactly what is wrong and the fix is obvious. The hardest were the ones that needed a decision, like the bare `except` in `dispense()`. Removing it meant working out every way the function could fail (unknown patient, drug not in stock, expired, not enough units) and deciding what each should do. The SQL injection fix was short, but I had to understand the attack and test it with `x' OR '1'='1` before and after to be sure it was closed.

## 2. Did the tools report any false positives? How did you identify them?

Not clearly. Bandit's B608 had only **Low confidence**, and in a toy in-memory database it might look harmless, but I tested it and it really leaked all patient records, so it was a true positive. Some Pylint messages, such as missing docstrings and `global-statement`, are style opinions rather than bugs, so they matter less here. They are still reasonable, and fixing them cost little. The important lesson was the opposite problem: false negatives. None of the three tools noticed that Kavya was given penicillin despite her allergy, that stock went negative, or that expired medicine was dispensed. I only found those by running the program and reading its output.

## 3. How would you integrate static analysis into a real development workflow?

I would run Flake8 and Pylint as a pre-commit hook so style and quality problems never reach the repository, and run all three tools in a CI pipeline (for example GitHub Actions) on every pull request, failing the build on any Bandit finding or if the Pylint score drops below a threshold such as 9.5. I would configure the tools in a shared config file (`.pylintrc`, `setup.cfg`) so the team uses the same rules, and use targeted `# nosec` or `# pylint: disable` comments only with a written reason. Static analysis would sit alongside unit tests and code review, not replace them.

## 4. What tangible improvements did you see in quality, readability and robustness?

The Pylint score rose from 6.90 to 10.00, Bandit went from 2 findings to 0, and Flake8 from 15 violations to 0. More importantly the program is safer and more predictable. User input can no longer alter the SQL query, failures print specific messages instead of being swallowed, files are closed properly, the shared mutable default is gone, and the allergy, stock and expiry rules now protect the patient. The code is also easier to read and test, with docstrings, consistent naming, no global rebinding, and a `main()` guard so it can be imported without running.
