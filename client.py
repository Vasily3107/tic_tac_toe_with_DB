# client

from os import system
def cls(): system('cls')
def wait(): input('\nPress "Enter" to continue...')

system('')
GREEN, YELLOW, RED, BLUE = (0, 255, 0), (255, 255, 0), (255, 0, 0), (66, 66, 233)
def rgb_txt(txt, r, g, b):
    color = f"\u001b[38;2;{r};{g};{b}m"
    reset = "\u001b[0m"
    return f"{color}{txt}{reset}"

import socket

IP = "127.0.0.1"
PORT = 12345

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((IP, PORT))

print('waiting for other player')
table, sign = client.recv(1024).decode().split('|')
table = eval(table)
server_message = 'move' if sign == 'x' else 'wait'
cls()

print('Game instructions: \n',
      ' - WASD or ARROW KEYS : select tile',
      ' - ENTER or E         : confirm selection \n',
      f'YOUR SIGN: {sign}', sep="\n")
wait()
cls()

currently_selected = [1, 1]

def change_selection(key):
    global currently_selected
    y, x = currently_selected
    match key:
        case 'w' | 'up':
            if y == 0: return
            currently_selected[0] -= 1
        case 's' | 'down':
            if y == 2: return
            currently_selected[0] += 1
        case 'a' | 'left':
            if x == 0: return
            currently_selected[1] -= 1
        case 'd' | 'right':
            if x == 2: return
            currently_selected[1] += 1

def render_table():
    global table
    for y, row in enumerate(table):
        for x, i in enumerate(row):
            if [y, x] == currently_selected:

                if 'wait' in server_message:
                    print(rgb_txt(f">{i}<", *YELLOW), end="")
                    continue

                elif i == '_':
                    print(rgb_txt(f">{i}<", *GREEN), end="")

                else:
                    print(rgb_txt(f">{i}<", *RED), end="")

            else:
                if i == sign:
                    print(rgb_txt(f" {i} ", *BLUE), end="")
                else:
                    print(f" {i} ", end="")

        print()

def print_server_msg():
    global server_message
    print()
    match server_message:
        case 'wait':
            print(rgb_txt('Waiting for opponent to move...', *YELLOW))
        case 'move':
            print(rgb_txt('Make your move', *GREEN))
        case _:
            print()

def keyboard_events(key):
    match key:
        case ("up" | "down" | "left" | "right" |
              "w"  | "s"    | "a"    | "d"):
            change_selection(key)

        case "enter" | "e":
            global table, server_message, currently_selected

            y, x = currently_selected
            if table[y][x] != '_' or server_message == 'wait': return

            client.send(str(currently_selected).encode())
            table, server_message = client.recv(1024).decode().split('|')
            if table == 'win': win(server_message)
            table = eval(table)

def win(winner):
    cls()
    print(f'{winner} is the winner!')
    client.close()
    exit(0)

def tie():
    cls()
    print('Tie, no one won')
    client.close()
    exit(0)

from keyboard import read_key
from time     import sleep
while True:
    cls()

    render_table()
    print_server_msg()

    match server_message:
        case 'move':
            keyboard_events(read_key())
        case 'wait':
            try:
                table, server_message = client.recv(1024).decode().split('|')
                if table == 'win'  : win(server_message)
                elif table == 'tie': tie()
                table = eval(table)
            except:
                cls()
                print("Other player left the game")
                client.close()
                exit(-1)

    sleep(0.1)