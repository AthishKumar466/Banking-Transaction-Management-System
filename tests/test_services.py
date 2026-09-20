import os
import tempfile

import pytest

from bank.db import init_db
from bank.services import BankService


@pytest.fixture
def service():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    os.remove(path)  # init_db creates it fresh
    init_db(path)
    svc = BankService(path)
    yield svc
    os.remove(path)


def test_create_account_sets_initial_balance(service):
    acc = service.create_account('Alice', 100)
    assert acc.balance == 100
    assert acc.name == 'Alice'


def test_create_account_rejects_blank_name(service):
    with pytest.raises(ValueError):
        service.create_account('   ', 0)


def test_create_account_rejects_negative_initial_deposit(service):
    with pytest.raises(ValueError):
        service.create_account('Alice', -5)


def test_deposit_increases_balance(service):
    acc = service.create_account('Alice', 0)
    service.deposit(acc.id, 50)
    assert service.get_account(acc.id).balance == 50


def test_deposit_rejects_nonpositive_amount(service):
    acc = service.create_account('Alice', 10)
    with pytest.raises(ValueError):
        service.deposit(acc.id, 0)
    with pytest.raises(ValueError):
        service.deposit(acc.id, -5)


def test_deposit_rejects_nonexistent_account(service):
    with pytest.raises(ValueError):
        service.deposit(9999, 10)


def test_withdraw_decreases_balance(service):
    acc = service.create_account('Alice', 100)
    service.withdraw(acc.id, 40)
    assert service.get_account(acc.id).balance == 60


def test_withdraw_rejects_insufficient_funds(service):
    acc = service.create_account('Alice', 10)
    with pytest.raises(ValueError, match='Insufficient funds'):
        service.withdraw(acc.id, 20)
    # balance must be unchanged after a failed withdrawal
    assert service.get_account(acc.id).balance == 10


def test_withdraw_rejects_nonexistent_account(service):
    with pytest.raises(ValueError, match='Account not found'):
        service.withdraw(9999, 10)


def test_transfer_moves_money_between_accounts(service):
    a = service.create_account('Alice', 100)
    b = service.create_account('Bob', 20)
    service.transfer(a.id, b.id, 30)
    assert service.get_account(a.id).balance == 70
    assert service.get_account(b.id).balance == 50


def test_transfer_rejects_insufficient_funds_and_leaves_balances_unchanged(service):
    a = service.create_account('Alice', 10)
    b = service.create_account('Bob', 20)
    with pytest.raises(ValueError, match='Insufficient funds'):
        service.transfer(a.id, b.id, 50)
    assert service.get_account(a.id).balance == 10
    assert service.get_account(b.id).balance == 20


def test_transfer_rejects_same_account(service):
    a = service.create_account('Alice', 100)
    with pytest.raises(ValueError):
        service.transfer(a.id, a.id, 10)


def test_transfer_rejects_missing_destination(service):
    a = service.create_account('Alice', 100)
    with pytest.raises(ValueError, match='Destination account not found'):
        service.transfer(a.id, 9999, 10)


def test_no_floating_point_drift_over_many_transactions(service):
    acc = service.create_account('Alice', 0)
    for _ in range(1000):
        service.deposit(acc.id, 0.10)
    # 1000 deposits of 10 cents should be exactly 100.00, not
    # 99.99999999999 or similar -- this is what storing cents as integers
    # instead of dollars as floats buys you.
    assert service.get_account(acc.id).balance == 100.0


def test_transaction_log_records_deposits_and_withdrawals(service):
    acc = service.create_account('Alice', 100)
    service.deposit(acc.id, 20)
    service.withdraw(acc.id, 30)
    txs = service.get_transactions(acc.id)
    types = [t.type for t in txs]
    assert types == ['withdraw', 'deposit', 'deposit']  # most recent first, plus initial deposit


def test_transfer_records_both_legs(service):
    a = service.create_account('Alice', 100)
    b = service.create_account('Bob', 0)
    service.transfer(a.id, b.id, 25)

    a_txs = service.get_transactions(a.id)
    b_txs = service.get_transactions(b.id)

    assert a_txs[0].type == 'transfer-out'
    assert a_txs[0].amount == -25
    assert a_txs[0].counterparty == b.id

    assert b_txs[0].type == 'transfer-in'
    assert b_txs[0].amount == 25
    assert b_txs[0].counterparty == a.id
