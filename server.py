# server

import pyodbc

server = 'localhost\SQLEXPRESS'  
database = 'test_db'
dsn = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'

from time import localtime
def get_time():
    YYYY, MM, DD, h, m, s, *_ = localtime()
    return f"{h:0>2}:{m:0>2}:{s:0>2} {DD:0>2}/{MM:0>2}/{YYYY}"

import socket

IP = "127.0.0.1"
PORT = 12345

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((IP, PORT))
server.listen(2)

X, O = "x", "o"

class Table:
    table = [["_" for _ in range(3)] for _ in range(3)]
    local_logs = []

    @classmethod
    def get_global_logs(cls):
        try:
            conn = pyodbc.connect(dsn)
            cursor = conn.cursor()

            cursor.execute(f"SELECT * FROM moves")
            rows = cursor.fetchall()

            logs = []
            for row in rows:
                logs.append(f'TIME: {row[0]:25} SIGN: {row[1]:10} COORDS: {row[2]:15} INFO: {row[3] or "N/A"}')

            cursor.close()
            conn.close()
            return logs

        except:
            return None

    @classmethod
    def save_local_logs(cls):
        try:
            conn = pyodbc.connect(dsn)
            cursor = conn.cursor()

            insert_query = f"INSERT INTO moves ([time], [sign], coords, [info]) VALUES (?, ?, ?, ?)"
            values = cls.local_logs

            cursor.executemany(insert_query, values)
            conn.commit()

            cursor.close()
            conn.close()
            return True

        except Exception as e:
            print(f"LOCAL LOG SAVING ERROR: {e}")
            return False

    @classmethod
    def move(cls, y, x, sign):
        cls.table[y][x] = sign
        log = tuple([get_time(), sign, f'YX({y}:{x})', ''])
        cls.local_logs.append(log)
        print(f'TIME: {log[0]:25} SIGN: {log[1]:10} COORDS: {log[2]:15} INFO: {log[3] or "N/A"}')

    @classmethod
    def check_win(cls) -> str | bool:
        tmp_table = cls.table

        tie_check = ''

        for i in tmp_table:
            tie_check += ''.join(i)
            if "".join(i) == X*3: return X
            if "".join(i) == O*3: return O

        if '_' not in tie_check: return 'TIE'

        tmp_table = list(zip(*tmp_table))

        for i in tmp_table:
            if "".join(i) == X*3: return X
            if "".join(i) == O*3: return O

        diag1 = "".join([tmp_table[0][0], tmp_table[1][1], tmp_table[2][2]])
        diag2 = "".join([tmp_table[0][2], tmp_table[1][1], tmp_table[2][0]])

        if diag1 == X*3 or diag2 == X*3: return X
        if diag1 == O*3 or diag2 == O*3: return O

        return False

class Player:
    def __init__(self, sign: str, conn, addr):
        self.sign = sign
        self.is_waiting = False if sign == X else True

        self.conn = conn
        self.addr = addr

    def move(self):
        y, x = eval(self.conn.recv(1024).decode())
        Table.move(y, x, self.sign)
        self.conn.send(f"{str(Table.table)}|wait".encode())
        self.is_waiting = True

    def move_on_next_iteration(self):
        self.conn.send(f'{str(Table.table)}|move'.encode())
        self.is_waiting = False

from random import randint
rand_signs = [X, O] if randint(0, 1) else [O, X]

try:
    p1 = Player(rand_signs[0], *server.accept())
    p2 = Player(rand_signs[1], *server.accept())

    p1.conn.send(f'{str(Table.table)}|{p1.sign}'.encode())
    p2.conn.send(f'{str(Table.table)}|{p2.sign}'.encode())

    Table.local_logs.append(tuple([get_time(), 'N/A', 'N/A', 'game start']))

    for i in Table.get_global_logs():
        print(i)

    while True:
        if p2.is_waiting:
            p1.move()
            if Table.check_win(): break
            p2.move_on_next_iteration()
        else:
            p2.move()
            if Table.check_win(): break
            p1.move_on_next_iteration()

    result = Table.check_win()
    if result != 'TIE':
        p1.conn.send(f'win|{result}'.encode())
        p2.conn.send(f'win|{result}'.encode())
        Table.local_logs.append(tuple([get_time(), 'N/A', 'N/A', f'game end: {result} won']))

    else:
        p1.conn.send('tie|'.encode())
        p2.conn.send('tie|'.encode())
        Table.local_logs.append(tuple([get_time(), 'N/A', 'N/A', 'game end: tie']))

except ConnectionResetError:
    Table.local_logs.append(tuple([get_time(), 'N/A', 'N/A', 'game end: early end - one of the players left the game']))
    print("\n\n\t ERROR: one of the players left the game")

except Exception as e:
    print(f"\n\n\t Unpredicted exception: {e}")

finally:
    p1.conn.close()
    p2.conn.close()

    Table.save_local_logs()

    server.close()

    print("\n\n\t ALL CONNECTIONS AND SERVER WERE CLOSED \n\n")