import os

from flask import Flask, render_template, request, redirect, url_for, flash
from bank.services import BankService
from bank.formatting import format_inr

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
app.jinja_env.filters['inr'] = format_inr
service = BankService(os.environ.get('BANK_DB_PATH', 'bank.db'))


def _parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@app.route('/')
def index():
    accounts = service.list_accounts()
    return render_template('index.html', accounts=accounts)


@app.route('/account/<int:account_id>')
def account_view(account_id):
    acc = service.get_account(account_id)
    if not acc:
        flash('Account not found')
        return redirect(url_for('index'))
    txs = service.get_transactions(account_id, limit=200)
    return render_template('account.html', account=acc, transactions=txs)


@app.route('/create', methods=['POST'])
def create():
    try:
        name = request.form.get('name', '')
        init = float(request.form.get('initial', 0) or 0)
        service.create_account(name, init)
        flash('Account created')
    except (ValueError, TypeError) as e:
        flash(f'Could not create account: {e}')
    return redirect(url_for('index'))


@app.route('/deposit', methods=['POST'])
def deposit():
    aid = _parse_int(request.form.get('account_id'))
    if aid is None:
        flash('Invalid account')
        return redirect(url_for('index'))
    try:
        amt = float(request.form.get('amount'))
        service.deposit(aid, amt, note='web deposit')
        flash('Deposited')
    except (ValueError, TypeError) as e:
        flash(f'Could not deposit: {e}')
    return redirect(url_for('account_view', account_id=aid))


@app.route('/withdraw', methods=['POST'])
def withdraw():
    aid = _parse_int(request.form.get('account_id'))
    if aid is None:
        flash('Invalid account')
        return redirect(url_for('index'))
    try:
        amt = float(request.form.get('amount'))
        service.withdraw(aid, amt, note='web withdraw')
        flash('Withdrawn')
    except (ValueError, TypeError) as e:
        flash(f'Could not withdraw: {e}')
    return redirect(url_for('account_view', account_id=aid))


@app.route('/transfer', methods=['POST'])
def transfer():
    src = _parse_int(request.form.get('from_id'))
    if src is None:
        flash('Invalid source account')
        return redirect(url_for('index'))
    try:
        dst = int(request.form.get('to_id'))
        amt = float(request.form.get('amount'))
        service.transfer(src, dst, amt, note='web transfer')
        flash('Transferred')
    except (ValueError, TypeError) as e:
        flash(f'Could not transfer: {e}')
    return redirect(url_for('account_view', account_id=src))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(port=port, debug=True)
