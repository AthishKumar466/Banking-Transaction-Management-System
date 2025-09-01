from bank.services import BankService

service = BankService('bank.db')

MENU = '''
Mini Bank - Commands:
1) Create account
2) List accounts
3) Deposit
4) Withdraw
5) Transfer
6) View transactions
7) Exit
'''

def input_float(prompt: str) -> float:
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print('Please enter a valid number')

def main():
    print('Welcome to Mini Bank (console)')
    while True:
        print(MENU)
        cmd = input('Choose: ').strip()
        if cmd == '1':
            name = input('Account holder name: ').strip()
            init = input('Initial deposit (0 if none): ').strip() or '0'
            acct = service.create_account(name, float(init))
            print(f'Created account {acct.id} for {acct.name} with balance {acct.balance}')
        elif cmd == '2':
            for a in service.list_accounts():
                print(f"{a.id}: {a.name} — {a.balance}")
        elif cmd == '3':
            aid = int(input('Account id: '))
            amt = input_float('Amount to deposit: ')
            service.deposit(aid, amt)
            print('Done')
        elif cmd == '4':
            aid = int(input('Account id: '))
            amt = input_float('Amount to withdraw: ')
            try:
                service.withdraw(aid, amt)
                print('Done')
            except Exception as e:
                print('Error:', e)
        elif cmd == '5':
            src = int(input('From account id: '))
            dst = int(input('To account id: '))
            amt = input_float('Amount to transfer: ')
            try:
                service.transfer(src, dst, amt)
                print('Transferred')
            except Exception as e:
                print('Error:', e)
        elif cmd == '6':
            aid = int(input('Account id: '))
            txs = service.get_transactions(aid)
            for t in txs:
                print(f"{t.created_at} | {t.type} | {t.amount} | cp:{t.counterparty} | {t.note}")
        elif cmd == '7':
            print('Bye')
            break
        else:
            print('Unknown command')

if __name__ == '__main__':
    main()
