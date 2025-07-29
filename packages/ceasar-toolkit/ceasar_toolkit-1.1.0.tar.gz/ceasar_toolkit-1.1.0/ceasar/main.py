#!/usr/bin/env python3
import sys
import os
import time
import threading
import shutil
import getpass
import subprocess
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter
from colorama import init, Fore
import tempfile

# ─── Initialize colored output ─────────────────────────────────────────────────
init(autoreset=True)

# ─── ASCII banner ───────────────────────────────────────────────────────────────
BANNER = r"""
  _____                          
 / ____|                         
| |     ___  __ _ ___  __ _ _ __ 
| |    / _ \/ _` / __|/ _` | '__|
| |___|  __/ (_| \__ \ (_| | |   
 \_____\___|\__,_|___/\__,_|_|  

    Ceasar Encryptor and Decryptor
"""
width = shutil.get_terminal_size((80,20)).columns
for line in BANNER.splitlines():
    print(Fore.CYAN + line.center(width))

# ─── Spinner for long ops ──────────────────────────────────────────────────────
class Spinner:
    busy = False
    delay = 0.1
    def __init__(self, msg="Processing"):
        self.msg = msg
        self.thread = threading.Thread(target=self.spin)
        self.gen = self.spinning_cursor()
    @staticmethod
    def spinning_cursor():
        while True:
            for c in "|/-\\": yield c
    def spin(self):
        while self.busy:
            sys.stdout.write(f"\r{self.msg} {next(self.gen)}")
            sys.stdout.flush()
            time.sleep(self.delay)
    def __enter__(self):
        self.busy = True
        self.thread.start()
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.busy = False
        time.sleep(self.delay)
        sys.stdout.write("\r" + " "*(len(self.msg)+2) + "\r")

# ─── Caesar cipher ──────────────────────────────────────────────────────────────
def caesar_encode(text, shift):
    out = []
    for ch in text:
        if ch.isalpha():
            base = ord('a') if ch.islower() else ord('A')
            out.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            out.append(ch)
    return "".join(out)

def caesar_decode(text, shift):
    return caesar_encode(text, -shift)

def process_caesar(encode_mode: bool):
    path = Path(input("Enter text file path: ").strip())
    if not path.is_file():
        print(Fore.RED + "File not found.")
        return

    content = path.read_text(encoding="utf-8")
    stem, ext = path.stem, path.suffix

    if encode_mode:
        s = input("Enter shift (integer): ").strip()
        if not s.isdigit():
            print(Fore.RED + "Invalid shift.")
            return
        shift = int(s)
        out = path.with_name(f"{stem}_enc{ext}")
        header = f"Shift:{shift}\n"
        with Spinner(f"Encoding (shift={shift})"):
            time.sleep(0.5)
        out.write_text(header + caesar_encode(content, shift), encoding="utf-8")
        print(Fore.GREEN + f"Encoded → {out}")
    else:
        parts = content.split("\n", 1)
        if len(parts) < 2 or not parts[0].startswith("Shift:"):
            print(Fore.RED + "Missing Shift header.")
            return
        try:
            shift = int(parts[0].split(":",1)[1])
        except ValueError:
            print(Fore.RED + "Invalid Shift header.")
            return
        out = path.with_name(f"{stem}_dec{ext}")
        with Spinner(f"Decoding (shift={shift})"):
            time.sleep(0.5)
        out.write_text(caesar_decode(parts[1], shift), encoding="utf-8")
        print(Fore.GREEN + f"Decoded → {out}")

# ─── PDF encrypt/decrypt ─────────────────────────────────────────────────────────
def process_pdf(encrypt_mode: bool):
    path = Path(input("Enter PDF path: ").strip())
    if not path.is_file():
        print(Fore.RED + "File not found.")
        return

    pwd = getpass.getpass("Enter password: ")
    reader = PdfReader(str(path))
    writer = PdfWriter()

    with Spinner("Processing PDF"):
        time.sleep(0.5)

    if encrypt_mode:
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(pwd)
        out = path.with_name(path.stem + "_enc.pdf")
    else:
        if reader.is_encrypted:
            reader.decrypt(pwd)
        for page in reader.pages:
            writer.add_page(page)
        out = path.with_name(path.stem + "_dec.pdf")

    with open(out, "wb") as f:
        writer.write(f)
    print(Fore.GREEN + f"PDF saved → {out}")

# ─── Folder encrypt/decrypt with EncFS ───────────────────────────────────────────
# ─── Folder encrypt/decrypt with EncFS (interactive prompts) ────────────────────
def encrypt_folder_encfs():
    if shutil.which("encfs") is None:
        print(Fore.RED + "encfs not found. Install with: sudo apt install encfs")
        return

    folder = Path(input("Enter folder to encrypt: ").strip())
    if not folder.is_dir():
        print(Fore.RED + "Folder not found.")
        return

    encrypted = folder.with_name(folder.name + "_encrypted")
    mountpt   = folder.with_name(folder.name + "_mnt")
    mountpt.mkdir(exist_ok=True)

    print(Fore.YELLOW + "▶ You will now be prompted by EncFS to:")
    print("    1) confirm creation of the new encrypted directory")
    print("    2) choose & verify a passphrase for it\n")

    # Run EncFS *without* our spinner so you actually see its y/n and passphrase prompts
    subprocess.run(
        ["encfs", "--standard", str(encrypted), str(mountpt)],
        check=True
    )

    # now copy your data into the mounted view...
    with Spinner("Copying data into encrypted folder"):
        shutil.copytree(folder, mountpt, dirs_exist_ok=True)

    # unmount
    subprocess.run(["fusermount", "-u", str(mountpt)], check=True)
    mountpt.rmdir()

    print(Fore.GREEN + f"\nEncrypted folder created: {encrypted}")
    print("To access it again, run:")
    print(f"  encfs {encrypted} {mountpt}    # then enter your passphrase")

def decrypt_folder_encfs():
    if shutil.which("encfs") is None:
        print(Fore.RED + "encfs not found. Install with: sudo apt install encfs")
        return

    enc_folder = Path(input("Enter encrypted folder path: ").strip())
    if not enc_folder.is_dir():
        print(Fore.RED + "Encrypted folder not found.")
        return

    # 1. make a temp mount point
    mountpt = Path(tempfile.mkdtemp(prefix=f"{enc_folder.stem}_mnt_"))
    # 2. define the output decrypted folder
    dec_folder = enc_folder.with_name(enc_folder.stem + "_decrypted")

    print(Fore.YELLOW + "▶ You will be prompted for your EncFS passphrase now…")

    # 3. mount encrypted folder (you’ll see the passphrase prompt)
    subprocess.run(
        ["encfs", "--standard", str(enc_folder), str(mountpt)],
        check=True
    )

    # 4. copy everything out
    print("Copying decrypted data…")
    shutil.copytree(mountpt, dec_folder, dirs_exist_ok=True)

    # 5. unmount and remove temp
    subprocess.run(["fusermount", "-u", str(mountpt)], check=True)
    shutil.rmtree(mountpt)

    print(Fore.GREEN + f"Decrypted folder created at: {dec_folder}")
# ─── Interactive menu ───────────────────────────────────────────────────────────
options = [
    ("Caesar Encode Text",      lambda: process_caesar(True)),
    ("Caesar Decode Text",      lambda: process_caesar(False)),
    ("Encrypt PDF",             lambda: process_pdf(True)),
    ("Decrypt PDF",             lambda: process_pdf(False)),
    ("Encrypt Folder (EncFS)",  encrypt_folder_encfs),
    ("Mount Encrypted Folder",  decrypt_folder_encfs),
    ("Exit",                    None),
]

def menu():
      while True:
          print(Fore.GREEN + "\nSelect an option:")
          for i, (desc, _) in enumerate(options, 1):
              print(Fore.GREEN + f"  {i}. {desc}")
          choice = input("> ").strip()
          if not choice.isdigit() or not (1 <= int(choice) <= len(options)):
              print(Fore.RED + "Invalid choice.")
              continue
          idx = int(choice) - 1
          if options[idx][1] is None:
              print("Goodbye!")
              break
          options[idx][1]()

 # ─── Entrypoint ───────────────────────────────────────────────────────────
def main():
     try:
        menu()
     except KeyboardInterrupt:
         print("\nExiting.")
         sys.exit(0)

if __name__ == "__main__":
    main()