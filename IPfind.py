import socket
import subprocess
from prettytable import PrettyTable
import sys
import time
import colorama
from colorama import Fore, Back, Style

def get_mac_address(ip):
    try:
        result = subprocess.check_output(["arp", "-n", ip], universal_newlines=True)
        lines = result.split("\n")
        for line in lines:
            if ip in line:
                mac_address = line.split()[2]
                print(f" -- MAC: {mac_address}")
                return mac_address
        return "-"
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Abrufen der MAC-Adresse für IP {ip}: {e}")
        return "-"

def get_device_info(ip):
    try:
        host_name, _, _ = socket.gethostbyaddr(ip)
        print(f" -- Hostname: {host_name}")
        return host_name
    except socket.herror as e:
        print(f" -- Not defined")
        return "-"

def get_device_status(ip, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.connect((ip, port))
            return True
    except (socket.timeout, socket.error) as e:
        return False

def get_operating_system(ip):
    ports_os_mapping = {
        22: "Linux",
        445: "FRITZ!OS",
        62078: "iOS?",
        5037: "Android?"
    }

    for port, os in ports_os_mapping.items():
        if get_device_status(ip, port):
            return os
    return "-"

def get_firewall_info(ip):
    if get_device_status(ip, 80):
        print(" -- Firewall")
        return "✓"
    return "-"

def is_reachable(ip):
    try:
        subprocess.check_output(["ping", "-c", "1", ip])
        print(" -- Activ")
        return True
    except subprocess.CalledProcessError as e:
        print(f" -- Inactiv")
        return False

def get_device_type(mac_address):
    oui = mac_address[:8].upper()
    device_types = {
        "F4:7F:35": "FritzBox",
        "1C:1D:86": "FritzRepeater"
    }
    return device_types.get(oui, "Unbekannt")

def check_activ(ip):
    try:
        subprocess.check_output(["ping", "-c", "1", ip])

        return True
    except subprocess.CalledProcessError as e:

        return False

def find_active_ports(ip, active):
    ports = []
    for port in range(1, 5061):  # Scannt alle Ports von 1 bis 5060
        try_number = 1
        while True:  # Endlosschleife bis der Port aktiv ist
            print(f"Scanning port: {port} / 5061                                         ", end="\r")
            if check_activ(ip):
                if get_device_status(ip, port):
                    ports.append(port)
                    print(f" -- Active port: {port}                     ")
                break  # Sobald der Port aktiv ist, breche die Schleife ab
            else:
                try_number += 1
                print(f"Port: {port} / 5061 | Host inactiv, try again... ({try_number})", end="\r")
                time.sleep(1)  # Warte eine Sekunde und versuche es erneut
    return ports

def list_devices_in_network(options):
    devices = []

    for i in range(1, 255):
        ip = f"192.168.178.{i}"
        print("---------------------------------------")
        print("Search...", i, "/ 255 |", str(round((i / 255) * 100, 2)) + "% ")

        try:
            host_name = get_device_info(ip) if 'h' in options else "-"
            if host_name != "-":
                is_active = is_reachable(ip) if 'a' in options else False
                mac_address = get_mac_address(ip) if 'm' in options else "-"
                operating_system = get_operating_system(ip) if 's' in options else "-"
                firewall_info = get_firewall_info(ip) if 'f' in options else "-"
                device_type = get_device_type(mac_address) if 't' in options else "-"
                ports = find_active_ports(ip, is_active) if 'p' in options else []
                devices.append({
                    'IP': ip,
                    'Name': host_name if 'h' in options else "-",
                    'Aktiv': '✓' if is_active else '-',
                    'MAC': mac_address,
                    'OS': operating_system,
                    'FW': firewall_info,
                    'Typ': device_type,
                    'Ports': ports,
                })
        except socket.error as e:
            print(f"Socket-Fehler für IP {ip}: {e}")
            pass

    return devices


def list_devices(parameters, options):
    devices = []

    for ip in parameters:
        try:
            host_name = get_device_info(ip) if 'h' in options else "-"
            if host_name != "-":
                is_active = is_reachable(ip) if 'a' in options else False
                mac_address = get_mac_address(ip) if 'm' in options else "-"
                operating_system = get_operating_system(ip) if 's' in options else "-"
                firewall_info = get_firewall_info(ip) if 'f' in options else "-"
                device_type = get_device_type(mac_address) if 't' in options else "-"
                ports = find_active_ports(ip, is_active) if 'p' in options else []
                devices.append({
                    'IP': ip,
                    'Name': host_name if 'h' in options else "-",
                    'Aktiv': '✓' if is_active else '-',
                    'MAC': mac_address,
                    'OS': operating_system,
                    'FW': firewall_info,
                    'Typ': device_type,
                    'Ports': ports,
                })
        except socket.error as e:
            print(f"Socket-Fehler für IP {ip}: {e}")
            pass

    return devices


def display_devices_table(devices, options):
    if devices:
        table = PrettyTable()
        field_names = ["IP"]
        if 'h' in options:
            field_names.append("Name")
        if 'a' in options:
            field_names.append("Aktiv")
        if 'm' in options:
            field_names.append("MAC")
        if 's' in options:
            field_names.append("OS")
        if 'f' in options:
            field_names.append("FW")
        if 't' in options:
            field_names.append("Typ")
        if 'p' in options:
            field_names.append("Ports")

        table.field_names = field_names
        table.align = "l"
        
        for device in devices:
            row = [device['IP']]
            if 'h' in options:
                row.append(device['Name'])
            if 'a' in options:
                row.append(device['Aktiv'])
            if 'm' in options:
                row.append(device['MAC'])
            if 's' in options:
                row.append(device['OS'])
            if 'f' in options:
                row.append(device['FW'])
            if 't' in options:
                row.append(device['Typ'])
            if 'p' in options:
                row.append(device['Ports'])
            table.add_row(row)

        print(table)
        print("Gefundene aktive Geräte:", len([device for device in devices if device.get('Aktiv') == '✓']))
    else:
        print("Keine erreichbaren Geräte gefunden.")

def separate_arguments(args):
    options = set()
    parameters = []

    for arg in args:
        if arg.startswith('-'):
            options.update(arg[1:])
        else:
            parameters.append(arg)
    
    return options, parameters

if __name__ == "__main__":
    options, parameters = separate_arguments(sys.argv[1:])
    
    if len(parameters) > 0:
        devices = list_devices(parameters, options)
    else:
        devices = list_devices_in_network(options)
    
    display_devices_table(devices, options)
