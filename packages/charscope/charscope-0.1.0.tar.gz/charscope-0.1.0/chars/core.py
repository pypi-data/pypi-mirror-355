import numpy as np
import matplotlib.pyplot as plt
from colorama import Fore, Style, init
import pyfiglet
from collections import Counter
import unicodedata
import string

init(autoreset=True)

def print_banner():
    banner = pyfiglet.figlet_format("CharScope")
    print(Fore.CYAN + banner)

def is_ascii(c):
    return ord(c) < 128

def analyze_text(text: str):
    print(Fore.YELLOW + f"\nAnalyzing text: {repr(text)}\n")
    
    ascii_chars = [c for c in text if is_ascii(c)]
    utf8_chars = [c for c in text if not is_ascii(c)]
    encoded = text.encode("utf-8")

    print(Fore.GREEN + f"Total characters: {len(text)}")
    print(Fore.LIGHTGREEN_EX + f"ASCII characters: {len(ascii_chars)}")
    print(Fore.MAGENTA + f"UTF-8 (non-ASCII) characters: {len(utf8_chars)}")
    print(Fore.BLUE + f"UTF-8 encoded byte size: {len(encoded)} bytes")

    entropy_val = entropy(text)
    print(Fore.LIGHTWHITE_EX + f"Entropy: {entropy_val:.4f} bits/char")

    display_char_table(text)
    plot_char_distribution(text)
    plot_ascii_utf8_ratio(len(ascii_chars), len(utf8_chars))

def entropy(text: str):
    total = len(text)
    if total == 0:
        return 0.0
    freq = Counter(text)
    probabilities = [count / total for count in freq.values()]
    ent = -sum(p * np.log2(p) for p in probabilities)
    return ent

def display_char_table(text: str):
    print(Fore.CYAN + "\nCharacter Info Table:")
    print(Fore.YELLOW + f"{'Char':^8} {'Code':^8} {'Name':^30} {'Type':^10}")
    print(Fore.YELLOW + "-" * 60)
    
    for c in sorted(set(text)):
        code = ord(c)
        name = unicodedata.name(c, "UNKNOWN")
        char_type = "ASCII" if is_ascii(c) else "UTF-8"
        color = Fore.GREEN if char_type == "ASCII" else Fore.MAGENTA
        print(color + f"{repr(c):^8} {code:^8} {name[:30]:30} {char_type:^10}")

def plot_char_distribution(text: str):
    if not text:
        print(Fore.RED + "Empty text — no histogram to show.")
        return

    char_vals = np.array([ord(c) for c in text])
    plt.figure(figsize=(10, 5))
    plt.hist(char_vals, bins=range(min(char_vals), max(char_vals) + 1), 
             color='deepskyblue', edgecolor='black')
    plt.title("Character Code Point Distribution")
    plt.xlabel("Unicode Code Point")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def plot_ascii_utf8_ratio(ascii_count: int, utf8_count: int):
    labels = ['ASCII', 'UTF-8']
    sizes = [ascii_count, utf8_count]
    colors = ['limegreen', 'violet']
    
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
            startangle=90, textprops={'fontsize': 12})
    plt.title("Character Encoding Ratio")
    plt.axis('equal')
    plt.tight_layout()
    plt.show()

def filter_printable(text: str):
    return ''.join(c for c in text if c in string.printable)

def unique_bytes(text: str):
    encoded = text.encode("utf-8")
    unique = set(encoded)
    print(Fore.LIGHTBLUE_EX + f"\nUnique bytes in UTF-8: {len(unique)}")
    print(Fore.LIGHTBLUE_EX + f"Byte values: {sorted(unique)}")

def ascii_percentage(text: str):
    if not text:
        return 0.0
    ascii_chars = [c for c in text if is_ascii(c)]
    return len(ascii_chars) / len(text) * 100

def summary(text: str):
    print(Fore.CYAN + "\n=== SUMMARY ===")
    print(Fore.WHITE + f"Printable only : {filter_printable(text)}")
    print(Fore.WHITE + f"ASCII %        : {ascii_percentage(text):.2f}%")
    unique_bytes(text)

def licence():
        print(Fore.YELLOW + "\n=== LICENSE ===")
        print(Fore.BLUE + """\n MIT License

Copyright (c) © 2025 Eden Simamora

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE. """)         

if __name__ == "__main__":
    print_banner()
    sample_text = "Hello 世界! Python 🐍 ASCII & UTF-8 ❤️🧠"
    analyze_text(sample_text)
    summary(sample_text)
