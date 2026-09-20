import builtins

import cli
from bank.db import init_db


def test_cli_survives_invalid_input_and_service_errors_without_crashing(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    init_db('bank.db')

    inputs = iter([
        '1', 'Alice', '100',   # create account -> balance 100
        '3', 'abc', '1', '50',  # deposit: bad account id first (must reprompt, not crash), then valid
        '4', '1', '999',        # withdraw more than balance -> caught error, not a crash
        '7',                     # exit
    ])
    monkeypatch.setattr(builtins, 'input', lambda prompt='': next(inputs))

    cli.main()  # would raise and fail the test if any of the above crashed the loop

    out = capsys.readouterr().out
    assert 'Created account 1 for Alice with balance 100.0' in out
    assert 'Please enter a valid whole number' in out  # the bad account id was caught, not fatal
    assert 'Done' in out  # the deposit after re-entering a valid id succeeded
    assert 'Error: Insufficient funds' in out  # withdraw failure surfaced, didn't crash the CLI
    assert 'Bye' in out
