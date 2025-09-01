from bank.db import init_db

if __name__ == '__main__':
    init_db('bank.db')
    print('Initialized bank.db')
