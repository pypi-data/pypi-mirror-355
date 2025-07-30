import os
import shlex
import subprocess
import time
import json
import base64
import hmac
from pathlib import Path
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend

# === Hardcoded demo keys (for real use, prompt or use key mgmt) ===
HARDCODED_PASS = "sharekey"
HARDCODED_SALT = b"\x10" * 16  # Fixed salt

# === Derive AES key from passphrase + salt ===
def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

# === Encrypt file ===
def encrypt_file(filename: str):
    try:
        if not os.path.exists(filename):
            print(f"\033[91m[!] File not found: {filename}\033[0m")
            return

        with open(filename, 'rb') as f:
            data = f.read()

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        original_name = os.path.basename(filename)

        metadata = {
            "timestamp": timestamp,
            "filename": original_name
        }
        meta_bytes = json.dumps(metadata).encode()
        meta_len = len(meta_bytes).to_bytes(4, "big")

        key = derive_key(HARDCODED_PASS, HARDCODED_SALT)
        nonce = os.urandom(12)
        aesgcm = AESGCM(key)

        payload = meta_len + meta_bytes + data
        encrypted = aesgcm.encrypt(nonce, payload, None)

        # Obfuscate filename with HMAC
        digest = hmac.new(key, (original_name + timestamp).encode(), digestmod="sha256").digest()
        b64name = base64.urlsafe_b64encode(digest[:12]).decode().rstrip("=")
        out_file = f"{b64name}.enc"

        with open(out_file, 'wb') as f:
            f.write(HARDCODED_SALT + nonce + encrypted)

        try:
            subprocess.run(['shred', '--remove', '--zero', filename], check=True)
            print(f"\033[93m[-] Original file securely deleted.\033[0m")
        except Exception as e:
            print(f"\033[91m[!] Could not securely delete {filename}: {e}\033[0m")

        print(f"\033[92m[+] Encrypted to {out_file}\033[0m")
        print(f"\033[96m[*] Original filename: hidden in metadata\033[0m")
        print(f"\033[96m[*] Timestamp: {timestamp}\033[0m")

    except Exception as e:
        print(f"\033[91m[!] Encryption failed: {repr(e)}\033[0m")

# === Decrypt file ===
def decrypt_file(filename: str):
    try:
        with open(filename, 'rb') as f:
            raw = f.read()

        if len(raw) < 28:
            raise ValueError("File too short to contain salt and nonce.")

        salt = raw[:16]
        nonce = raw[16:28]
        ciphertext = raw[28:]
        key = derive_key(HARDCODED_PASS, salt)
        aesgcm = AESGCM(key)

        decrypted = aesgcm.decrypt(nonce, ciphertext, None)

        meta_len = int.from_bytes(decrypted[:4], "big")
        if meta_len > len(decrypted):
            raise ValueError("Corrupted metadata length.")

        meta_bytes = decrypted[4:4 + meta_len]
        metadata = json.loads(meta_bytes.decode())
        original_data = decrypted[4 + meta_len:]

        out_file = metadata['filename']
        if os.path.exists(out_file):
            out_file = f"{out_file}.dec"

        with open(out_file, 'wb') as f:
            f.write(original_data)

        print(f"\033[92m[+] Decrypted to {out_file}\033[0m")
        print(f"\033[96m[*] Original timestamp: {metadata['timestamp']}\033[0m")
        print(f"\033[96m[*] Original filename restored.\033[0m")

    except Exception as e:
        print(f"\033[91m[!] Decryption failed: {repr(e)}\033[0m")

# === Help Menu ===
def help_menu():
    print("""
\033[94mAvailable Commands:\033[0m
  create <filename>     Create and open file in nano
  encrypt <filename>    Encrypt file and hide filename
  decrypt <filename>    Decrypt file and restore name
  show <filename>       View file in nano
  help                  Show this menu
  exit                  Exit the console
""")

# === Command Console ===
def run_console():
    print("\033[92mSecureShare Console v0.3 — Filename Encryption Edition\033[0m")
    print("Type 'help' for commands.\n")

    while True:
        try:
            line = input("secureshare > ").strip()
            if not line:
                continue
            parts = shlex.split(line)
            cmd = parts[0]

            if cmd == "exit":
                print("Exiting SecureShare.")
                break
            elif cmd == "help":
                help_menu()
            elif cmd == "create" and len(parts) > 1:
                fname = parts[1]
                Path(fname).touch()
                subprocess.call(["nano", fname])
                print(f"\033[96m[+] Created and opened {fname}\033[0m")
            elif cmd == "encrypt" and len(parts) > 1:
                encrypt_file(parts[1])
            elif cmd == "decrypt" and len(parts) > 1:
                decrypt_file(parts[1])
            elif cmd == "show" and len(parts) > 1:
                subprocess.call(["nano", parts[1]])
            else:
                print(f"\033[91m[!] Unknown or incomplete command: {cmd}\033[0m")
        except KeyboardInterrupt:
            print("\nUse 'exit' to quit.")
        except Exception as e:
            print(f"\033[91m[!] Error: {repr(e)}\033[0m")

# === Entry point ===
if __name__ == "__main__":
    run_console()
