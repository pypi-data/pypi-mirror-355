import base64
import binascii
import numpy as np
import matplotlib.pyplot as plt
from colorama import Fore, Style, init
import sys

init(autoreset=True)  # Initialize colorama

def encode_text(text, encoding='base64'):
    if encoding == 'base64':
        return base64.b64encode(text.encode('utf-8'))
    elif encoding == 'hex':
        return binascii.hexlify(text.encode('utf-8'))
    elif encoding == 'utf-8':
        return text.encode('utf-8')
    else:
        raise ValueError(f"Unknown encoding: {encoding}")

def byte_distribution(byte_data):
    dist = np.zeros(256, dtype=int)
    for b in byte_data:
        dist[b] += 1
    return dist

def display_colored_bytes(byte_data):
    print(Fore.YELLOW + "Byte visualization:")
    for i, b in enumerate(byte_data):
        color = get_color_for_byte(b)
        print(color + f"{b:02X}", end=' ')
        if (i + 1) % 16 == 0:
            print()
    print(Style.RESET_ALL)

def get_color_for_byte(b):
    if b < 32:
        return Fore.BLUE
    elif 32 <= b < 64:
        return Fore.CYAN
    elif 64 <= b < 96:
        return Fore.GREEN
    elif 96 <= b < 128:
        return Fore.YELLOW
    elif 128 <= b < 192:
        return Fore.MAGENTA
    elif 192 <= b <= 255:
        return Fore.RED
    return Fore.WHITE

def plot_distribution(dist, encoding_name):
    indices = np.arange(256)
    plt.figure(figsize=(14, 5))
    plt.bar(indices, dist, color='skyblue')
    plt.title(f"Byte Distribution - {encoding_name}")
    plt.xlabel("Byte Value (0-255)")
    plt.ylabel("Frequency")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

def analyze_encoding(text, encoding):
    print(Fore.GREEN + f"\nEncoding with {encoding.upper()}...\n")
    encoded = encode_text(text, encoding)
    dist = byte_distribution(encoded)
    display_colored_bytes(encoded)
    plot_distribution(dist, encoding)

def get_user_text():
    print(Fore.CYAN + "Enter the text you want to analyze:")
    return input("> ")

def get_user_encoding():
    print(Fore.CYAN + "\nChoose encoding:")
    print("1. Base64")
    print("2. Hex")
    print("3. UTF-8")
    choice = input("> ")
    if choice == '1':
        return 'base64'
    elif choice == '2':
        return 'hex'
    elif choice == '3':
        return 'utf-8'
    else:
        print(Fore.RED + "Invalid choice. Defaulting to UTF-8.")
        return 'utf-8'

def main():
    if len(sys.argv) > 2:
        text = sys.argv[1]
        encoding = sys.argv[2]
    else:
        text = get_user_text()
        encoding = get_user_encoding()
    analyze_encoding(text, encoding)

# Utility function for testing
def test_all_encodings():
    sample = "Hello PyPI and encoding world! 🌍🔐"
    for enc in ['base64', 'hex', 'utf-8']:
        print(Fore.MAGENTA + f"\n=== Testing {enc.upper()} ===")
        encoded = encode_text(sample, enc)
        display_colored_bytes(encoded)
        dist = byte_distribution(encoded)
        print(Fore.GREEN + f"Total bytes: {len(encoded)}")
        plot_distribution(dist, enc)

test_all_encodings()
