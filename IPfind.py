import socket
import subprocess
from prettytable import PrettyTable
import sys
import time
import colorama
from colorama import Fore, Back, Style
from rich.progress import Progress, BarColumn, TextColumn

# Colorama initialization
colorama.init()

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
    except socket.herror:
        print(f" -- Not defined")
        return "-"

def get_device_status(ip, port):
    """Überprüft, ob ein Port auf einem Gerät aktiv ist (Dummy-Funktion für das Beispiel)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.connect((ip, port))
            return True
    except (socket.timeout, socket.error):
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
        print(" -- Active")
        return True
    except subprocess.CalledProcessError:
        print(f" -- Inactive")
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
    except subprocess.CalledProcessError:
        return False

def find_active_ports(ip, progress, port_task):
    ports = []
    total_ports = 5060  # Gesamtzahl der zu scannenden Ports
    
    for port in range(1, total_ports + 1):  # Scannt alle Ports von 1 bis 5060
        print(f"Scanning port: {port} / {total_ports} for {ip}                                         ", end="\r")
        if get_device_status(ip, port):
            ports.append(port)
            print(f" -- Active port: {port}                     ")
            break  # Sobald der Port aktiv ist, breche die Schleife ab
        time.sleep(0.01)  # Simulierte Zeit für Port-Scan
        progress.advance(port_task)  # Aktualisiert die Fortschrittsanzeige für den Portscan

    return ports

def list_devices_in_network(options):
    devices = []
    total_attempts = 255  # Define total attempts
    
    with Progress(TextColumn("[progress.description]{task.description}"),
                  BarColumn(),
                  TextColumn("[progress.percentage]{task.percentage:>3.0f}%")) as progress:
        
        device_task = progress.add_task("Scanning devices...", total=total_attempts)
        port_task = progress.add_task("Scanning ports...", total=5060, visible=False)  # Unsichtbarer Port-Task
        
        for i in range(1, 256):
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
                    
                    ports = []  # Standardmäßig leer
                    if 'p' in options and is_active:  # Port-Scan nur wenn aktiv
                        progress.update(port_task, visible=True)
                        ports = find_active_ports(ip, progress, port_task)
                        progress.update(port_task, visible=False)  # Nach dem Scannen wieder unsichtbar

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
            
            progress.advance(device_task)  # Fortschrittsanzeige für den Geräte-Scan

    return devices

def list_devices(parameters, options):
    devices = []
    total_attempts = len(parameters)  # Define total attempts based on input
    
    with Progress(TextColumn("[progress.description]{task.description}"),
                  BarColumn(),
                  TextColumn("[progress.percentage]{task.percentage:>3.0f}%")) as progress:
        
        device_task = progress.add_task("Processing devices...", total=total_attempts)
        port_task = progress.add_task("Scanning ports...", total=5060, visible=False)  # Unsichtbarer Port-Task
        
        for ip in parameters:
            try:
                host_name = get_device_info(ip) if 'h' in options else "-"
                if host_name != "-":
                    is_active = is_reachable(ip) if 'a' in options else False
                    mac_address = get_mac_address(ip) if 'm' in options else "-"
                    operating_system = get_operating_system(ip) if 's' in options else "-"
                    firewall_info = get_firewall_info(ip) if 'f' in options else "-"
                    device_type = get_device_type(mac_address) if 't' in options else "-"
                    
                    ports = []  # Standardmäßig leer
                    if 'p' in options and is_active:  # Port-Scan nur wenn aktiv
                        progress.update(port_task, visible=True)
                        ports = find_active_ports(ip, progress, port_task)
                        progress.update(port_task, visible=False)  # Nach dem Scannen wieder unsichtbar

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
            
            progress.advance(device_task)  # Fortschrittsanzeige für den Geräte-Scan

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

