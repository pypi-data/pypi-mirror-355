import string
import sys
import os
import time


# ASCII color codes
CYAN = "\033[96m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
BOLD = "\033[1m"
RESET = "\033[0m"


def main():

    """Run the CrackPass password strength checker."""

    # Very bold cyan heading
    print(BOLD + CYAN + r''' 
      ____                        _        ____                         
     / ___|  _ __   __ _    ___  | | __   |  _ \   __ _   ___   ___  
    | |     | '__/ / _` |  / __| | |/ /   | |_) | / _` | / __/ / __|  
    | |___  | |   | (_| | | (__  |   <    |  __/ | (_| | \__ \ \__ \  
     \____| |_|    \__,_|  \___| |_|\_\   |_|     \__,_| |___/ |___/   
        
    ''' + RESET)

    # Welcome message and usage tip
    print(BOLD + CYAN + "Welcome to CrackPass! Enter a password to check its strength.\n" + RESET)

    # Enter password prompt in red, handle empty input
    while True:
        pas = input(BOLD + RED + 'Enter the password to continue: ' + RESET)
        if pas.strip() == "":
            print(RED + "Password cannot be empty. Please enter a valid password.\n" + RESET)
        else:
            break

    sug = []

    #length

    pasl = len(pas)

    if pasl < 8:
        sug.append(0)
    elif pasl <= 12:
        sug.append(1)
    elif pasl > 12:
        sug.append(2)

    #char variety

    up = sum(a.isupper() for a in pas)
    low = sum(a.islower() for a in pas)
    num = sum(a.isdigit() for a in pas)
    sym = sum(c in string.punctuation for c in pas)

    pasp = pasl//4

    if up < pasp:
        u = " uppercase letters"
        if 3 not in sug:
            sug.append(3)
    else:
        u = ""

    if low < pasp:
        l = " lowercase letters"
        if 3 not in sug:
            sug.append(3)
    else:
        l = ""

    if num < pasp:
        n = " numbers"
        if 3 not in sug:
            sug.append(3)
    else:
        n = ""

    if sym < pasp:
        s = " symbols."
        if 3 not in sug:
            sug.append(3)
    else:
        s = "."

    if 3 not in sug:
        sug.append(4)

    #char position

    rep = False

    for i in range(0, pasl-2):
        if pas[i] == pas[i+1] == pas[i+2]:
            sug.append(5)
            rep = True
            break
    if not rep:
        sug.append(6)

    #wordlists

    script_dir = os.path.dirname(os.path.abspath(__file__))
    wordlists_dir = os.path.join(script_dir, "wordlists")

    wl = [
        os.path.join(wordlists_dir, "indian-passwords.txt"),
        os.path.join(wordlists_dir, "indian-passwords-length8-20.txt"),
        os.path.join(wordlists_dir, "rockyou_aa"),
        os.path.join(wordlists_dir, "rockyou_ab"),
        os.path.join(wordlists_dir, "rockyou_ac")
    ]

    found = False
    current_word = ""

    # Wordlist test in yellow
    for path in wl:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as file:
                for line in file:
                    word = line.strip()
                    print(f"\r{YELLOW}Looking in wordlists: {word[:50]:<50}{RESET}", end="", flush=True)
                    if word == pas:
                        found = True
                        break
            if found:
                break
        except FileNotFoundError:
            continue

    print("\r" + " " * 70, end="\r")

    if found:
        print(RED + f"Found: {pas}" + RESET)
        sug.append(7)
    else:
        sug.append(8)

    #brute force time est

    charset = 0
    if up > 0:
        charset += 26
    if low > 0:
        charset += 26
    if num > 0:
        charset += 10
    if sym > 0:
        charset += len(string.punctuation)

    combinations = (charset)**pasl
    gps = 11312000  

    sec = combinations / gps
    min = sec/60
    hr = min/60
    days = hr/24

    if min < 1:
        sug.append(9)
    elif hr > 1:
        sug.append(10)
    elif days > 370:
        sug.append(11)

    #suggestions

    suggestions = [
        #length
        "Length is too short. Consider using at least 8 or more than 12 characters.",
        "Length is okay, but you might want to increase it for better security.",
        "Length is absolutely fine. You can use it as is.",

        #char variety
        "Lacks variety in characters. Try including more",
        "Has a good variety of characters.",

        #char position
        "Try to avoid using characters in repeated positions, like 'aaaa' or '1111'.",
        "Good character position. No repeated patterns found.",
        
        #wordlist
        "Present in a list of commonly used passwords. Consider using a more unique password.",
        "Not present in a list of commonly used passwords. Good choice!",

        #brute force time estimation
        "Password is weak and can be cracked in less than a minute. Consider using a stronger password.",
        "Password is moderate and can be cracked in a few hours. Consider strengthening it.",
        "Password is strong and would take years to crack. Good choice!",
    ]

    # Summary
    print("\n" + BOLD + CYAN + "Summary:" + RESET)

    for ind in sug:
        if ind == 3:
            print(suggestions[ind]+u+l+n+s)
        else:
            print(suggestions[ind])

    print(BOLD + CYAN + "\nThank you for using CrackPass!" + RESET)
