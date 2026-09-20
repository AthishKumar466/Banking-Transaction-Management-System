# Mini Bank

![tests](https://github.com/AthishKumar466/Banking-Transaction-Management-System/actions/workflows/tests.yml/badge.svg)

A small banking transaction system (console + Flask web UI) backed by SQLite — account creation, deposits, withdrawals, and transfers, with a transaction ledger per account.

## Design notes worth knowing

- **Money is stored as integer cents, never floats.** `bank/services.py` converts dollars↔cents at the API boundary, but every arithmetic operation and every DB column is an integer. This avoids the classic floating-point drift bug where thousands of small deposits stop summing to a round number — see `tests/test_services.py::test_no_floating_point_drift_over_many_transactions`.
- **Balance changes are atomic, not check-then-act.** `withdraw`/`transfer` update the balance with a single conditional `UPDATE ... WHERE balance >= ?` and check the affected row count, rather than reading the balance, deciding in Python, then writing — so two concurrent withdrawals against the same account can't both read "sufficient funds" and both succeed, which would be possible with a naive SELECT-then-UPDATE.
- **A DB-level `CHECK (balance >= 0)` constraint** backs the application logic as a second line of defense.
- **Both UIs are thin.** `app.py` and `cli.py` only parse input and format output; every validation rule and every DB write lives in `bank/services.py`. Neither UI can bypass a rule the other enforces.

## Features

- Create accounts with an optional initial deposit
- Deposit / withdraw with balance and existence validation
- Transfer between accounts (atomic — both legs commit together or neither does)
- Per-account transaction ledger
- Console UI (`cli.py`) and web UI (`app.py`), sharing the same `BankService`
- Neither UI crashes on bad input — invalid account IDs / amounts are caught and reported, not left to raise

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python init_db.py          # creates bank.db
```

## Run

**Web UI:**
```bash
python app.py
```
Opens on `http://127.0.0.1:5000` by default. On macOS, port 5000 is often already taken by the **AirPlay Receiver** system service — if the page won't load, either turn that off (System Settings → General → AirDrop & Handoff) or run on another port:
```bash
PORT=5050 python app.py
```
Configuration is via environment variables (`SECRET_KEY`, `PORT`, `BANK_DB_PATH`) — see `.env.example`.

**Console UI:**
```bash
python cli.py
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

18 tests covering validation, insufficient-funds handling, transfer atomicity, the floating-point-drift regression, and a CLI-driven regression test for bad input handling. Runs on every push via GitHub Actions (`.github/workflows/tests.yml`).

## Project structure

```
.
├── app.py                 # Flask web UI
├── cli.py                 # console UI
├── init_db.py              # one-off DB setup
├── bank/
│   ├── db.py                # schema + connection helper
│   ├── models.py             # Account / Transaction dataclasses
│   └── services.py            # BankService — all business logic lives here
├── templates/                 # Jinja2 templates for the web UI
├── tests/
│   ├── test_services.py
│   └── test_cli.py
└── .github/workflows/tests.yml
```

## Known limitations

This is a learning/demo project, not production banking software:
- No authentication — anyone with access to the app can act on any account.
- No CSRF protection on the web forms.
- Single SQLite file, no migrations tooling.
- No audit trail beyond the transaction ledger (no request logging, no admin view).

## License

MIT — see [LICENSE](LICENSE).
