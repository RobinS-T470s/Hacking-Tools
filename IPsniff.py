from scapy.all import sniff
from scapy.layers.inet import IP, TCP, UDP
import sys
from datetime import datetime
import socket
import colorama
from colorama import Fore, Back, Style

# Initialisiere colorama
colorama.init()

# Definiere die globale Variable für die zu überwachende IP-Adresse
TARGET_IP = None

def packet_callback(packet):
    if IP in packet:
        ip_src = packet[IP].src
        ip_dst = packet[IP].dst
        mode = None  # Initialisiere die mode-Variable
        
        if ip_src == TARGET_IP:
            mode = "Send    -- "
        elif ip_dst == TARGET_IP:
            mode = "Receive -- "
        
        if mode:  # Überprüfen, ob mode gesetzt wurde
            if TCP in packet:
                port_src = packet[TCP].sport
                port_dst = packet[TCP].dport
                protocol = "TCP"
                payload = bytes(packet[TCP].payload) if packet[TCP].payload else b''
            elif UDP in packet:
                port_src = packet[UDP].sport
                port_dst = packet[UDP].dport
                protocol = "UDP"
                payload = bytes(packet[UDP].payload) if packet[UDP].payload else b''
            else:
                port_src = None
                port_dst = None
                protocol = "Other"
                payload = b''
            
            local_ip = get_local_ip()
            
            # Format für die überwachte IP-Adresse immer in Rot und die eigene IP-Adresse in Gelb
            formatted_src_ip = Fore.RED + ip_src + Style.RESET_ALL if ip_src == TARGET_IP else (
                Back.YELLOW + ip_src + Style.RESET_ALL if ip_src == local_ip else ip_src
            )
            formatted_dst_ip = Fore.RED + ip_dst + Style.RESET_ALL if ip_dst == TARGET_IP else (
                Back.YELLOW + ip_dst + Style.RESET_ALL if ip_dst == local_ip else ip_dst
            )

            # Konsistente Formatierung für Send und Receive
            formatted_output = (
                f"[{datetime.now().hour}:{datetime.now().minute}:{datetime.now().second}] -- {Style.RESET_ALL}"
                f"{mode} {protocol} Packet: "
                f"{formatted_src_ip}:{port_src} -> "
                f"{formatted_dst_ip}:{port_dst}"
            )

            # Nutze `.decode('utf-8', errors='ignore')` um den Payload zu decodieren, falls es sich um Text handelt.
            payload_decoded = payload.decode('utf-8', errors='ignore')

            print(formatted_output)
            print(payload_decoded)
            print("------------------------------------------------------------------")

def get_local_ip():
    try:
        # Ein UDP-Socket erstellen und eine Verbindung zu einem nicht existierenden Server aufbauen
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        local_ip = s.getsockname()[0]
    except Exception as e:
        local_ip = "Unable to get IP address: " + str(e)
    finally:
        s.close()
    return local_ip

def main():
    global TARGET_IP
    if len(sys.argv) > 1:
        TARGET_IP = sys.argv[1]
        print(f"Starting packet capture for IP {TARGET_IP}...")
        sniff(prn=packet_callback, store=0)
    else:
        print("Usage: python3 IPsniff.py <TARGET_IP>")

if __name__ == "__main__":
    main()

# Beende die Verwendung von colorama
colorama.deinit()

