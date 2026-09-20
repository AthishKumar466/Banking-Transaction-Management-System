from bank.services import BankService
from bank.formatting import format_inr

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


def input_int(prompt: str) -> int:
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print('Please enter a valid whole number')


def main():
    print('Welcome to Mini Bank (console)')
    while True:
        print(MENU)
        cmd = input('Choose: ').strip()
        try:
            if cmd == '1':
                name = input('Account holder name: ').strip()
                init = input('Initial deposit (0 if none): ').strip() or '0'
                acct = service.create_account(name, float(init))
                print(f'Created account {acct.id} for {acct.name} with balance {format_inr(acct.balance)}')
            elif cmd == '2':
                accounts = service.list_accounts()
                if not accounts:
                    print('No accounts yet')
                for a in accounts:
                    print(f"{a.id}: {a.name} — {format_inr(a.balance)}")
            elif cmd == '3':
                aid = input_int('Account id: ')
                amt = input_float('Amount to deposit: ')
                service.deposit(aid, amt)
                print('Done')
            elif cmd == '4':
                aid = input_int('Account id: ')
                amt = input_float('Amount to withdraw: ')
                service.withdraw(aid, amt)
                print('Done')
            elif cmd == '5':
                src = input_int('From account id: ')
                dst = input_int('To account id: ')
                amt = input_float('Amount to transfer: ')
                service.transfer(src, dst, amt)
                print('Transferred')
            elif cmd == '6':
                aid = input_int('Account id: ')
                txs = service.get_transactions(aid)
                if not txs:
                    print('No transactions yet')
                for t in txs:
                    print(f"{t.created_at} | {t.type} | {format_inr(t.amount)} | cp:{t.counterparty} | {t.note}")
            elif cmd == '7':
                print('Bye')
                break
            else:
                print('Unknown command')
        except ValueError as e:
            print('Error:', e)


if __name__ == '__main__':
    main()
