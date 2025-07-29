
# Crack Pass

CrackPass is a command-line password strength analyzer that evaluates your password using real-world techniques. It estimates how long it would take to brute-force your password, checks it against common wordlists, and provides actionable suggestions to improve your password security.


## Features

- Brute Force Attack Time Estimation

- Wordlist Test

- Character Variety Analysis

- Repeated Character Detection

- Actionable Suggestions


## Run Locally

Clone the project

```bash
  git clone https://github.com/cracking-bytes/Crack-Pass.git
```

Go to the project directory

```bash
  cd CrackPass
```

Run the program

```bash
  python3 src/main.py
```


## Usage/Examples

```text
$ python3 main.py
 
   ____                        _        ____                         
  / ___|  _ __   __ _    ___  | | __   |  _ \   __ _   ___   ___  
 | |     | '__/ / _` |  / __| | |/ /   | |_) | / _` | / __/ / __|  
 | |___  | |   | (_| | | (__  |   <    |  __/ | (_| | \__ \ \__ \  
  \____| |_|    \__,_|  \___| |_|\_\   |_|     \__,_| |___/ |___/   
       

Welcome to CrackPass! Enter a password to check its strength.

Enter the password to continue: abcd1234
Found: abcd1234                                                         

Summary:
Length is okay, but you might want to increase it for better security.
Lacks variety in caharacters. Try including more uppercase letters symbols.
Good character position. No repeated patterns found.
Present in a list of commonly used passwords. Consider using a more unique password.
Password is moderate and can be cracked in a few hours. Consider strengthening it.

Thank you for using CrackPass!

```


## Tech Stack

**Language:** Python 3

**Libraries:**

- `string` – for character set operations

- `os` – for file and path handling

- `time` – for timing and estimation

- `sys` – for system-specific functions

**Dev Tools:**

- VS Code

- Git & GitHub for version control


## License

[MIT](https://choosealicense.com/licenses/mit/)


## Author

Bhavika Nagdeo (Cracking Bytes)
- [Github](https://github.com/cracking-bytes)
- [Linkedin](https://in.linkedin.com/in/bhavikanagdeo)
- [Instagram](https://www.instagram.com/cracking.bytes/)
- [Medium](https://crackingbytes.medium.com/)



## Feedback

If you have any feedback, please reach out to me at bhavikanagdeo83@gmail.com

