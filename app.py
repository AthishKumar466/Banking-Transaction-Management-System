from flask import Flask, render_template, request, redirect, url_for, flash
from bank.services import BankService

app = Flask(__name__)
app.secret_key = 'dev-secret'
service = BankService('bank.db')

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
    name = request.form.get('name')
    init = float(request.form.get('initial', 0) or 0)
    service.create_account(name, init)
    flash('Account created')
    return redirect(url_for('index'))

@app.route('/deposit', methods=['POST'])
def deposit():
    aid = int(request.form.get('account_id'))
    amt = float(request.form.get('amount'))
    service.deposit(aid, amt, note='web deposit')
    flash('Deposited')
    return redirect(url_for('account_view', account_id=aid))

@app.route('/withdraw', methods=['POST'])
def withdraw():
    aid = int(request.form.get('account_id'))
    amt = float(request.form.get('amount'))
    try:
        service.withdraw(aid, amt, note='web withdraw')
    except Exception as e:
        flash(str(e))
    return redirect(url_for('account_view', account_id=aid))

@app.route('/transfer', methods=['POST'])
def transfer():
    src = int(request.form.get('from_id'))
    dst = int(request.form.get('to_id'))
    amt = float(request.form.get('amount'))
    try:
        service.transfer(src, dst, amt, note='web transfer')
    except Exception as e:
        flash(str(e))
    return redirect(url_for('account_view', account_id=src))

if __name__ == '__main__':
    app.run(debug=True)
