import os
import base64
import hmac
import getpass
import shlex
import zlib
import json
from argon2.low_level import hash_secret_raw, Type
from datetime import datetime, timezone
import secrets

# ======= ASCII Art Banner =======
def banner():
    print(r"""
 ███████╗██╗  ██╗███████╗███████╗███████╗██████╗
 ██╔════╝██║  ██║██╔════╝██╔════╝██╔════╝██╔══██╗
 ███████╗███████║█████╗  █████╗  █████╗  ██████╔╝
 ╚════██║██╔══██║██╔══╝  ██╔══╝  ██╔══╝  ██╔══██╗
 ███████║██║  ██║██║     ██║     ███████╗██║  ██║
 ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝     ╚══════╝╚═╝  ╚═╝
         Zero's Hash Encryption Secure Protocol
                 Version 2.0 (Z-HESP2)
    """)

# ======= Modern KDF (Argon2id) =======
def derive_key(password: str, salt: bytes, length: int = 32) -> bytes:
    return hash_secret_raw(
        password.encode(),
        salt,
        time_cost=3,
        memory_cost=65536,
        parallelism=2,
        hash_len=length,
        type=Type.ID
    )

# ======= Encryption =======
def encrypt(message: str, password: str, metadata: dict = None) -> str:
    salt = os.urandom(16)
    key = derive_key(password, salt)

    compressed = zlib.compress(message.encode())

    if metadata is None:
        metadata = {}
    metadata['timestamp'] = datetime.now(timezone.utc).isoformat()

    meta_blob = json.dumps(metadata).encode()
    meta_blob_enc = zlib.compress(meta_blob)
    meta_len = len(meta_blob_enc).to_bytes(4, 'big')

    full_payload = meta_len + meta_blob_enc + compressed

    h = hmac.new(key, full_payload, digestmod='sha256')
    mac = h.digest()

    blob = salt + mac + full_payload
    return "ZH2:" + base64.urlsafe_b64encode(blob).decode()

# ======= Decryption =======
def decrypt(token: str, password: str) -> str:
    try:
        if not token.startswith("ZH2:"):
            return "[!] Invalid ZHESP2 header."

        raw = base64.urlsafe_b64decode(token[4:])
        salt, mac, payload = raw[:16], raw[16:48], raw[48:]
        key = derive_key(password, salt)

        h = hmac.new(key, payload, digestmod='sha256')
        if not hmac.compare_digest(mac, h.digest()):
            return "[!] Authentication failed or wrong password."

        meta_len = int.from_bytes(payload[:4], 'big')
        meta_blob = zlib.decompress(payload[4:4 + meta_len])
        metadata = json.loads(meta_blob.decode())

        compressed_data = payload[4 + meta_len:]
        plaintext = zlib.decompress(compressed_data).decode()

        return f"[+] Metadata: {metadata}\n[+] Decrypted: {plaintext}"

    except Exception as e:
        return f"[!] Decryption error: {str(e)}"

# ======= Generate Key (genkey) =======
def generate_key(length: int = 32) -> str:
    key = secrets.token_urlsafe(length)
    print(f"[+] Generated Key ({length} chars):\n{key}\n")
    return key

# ======= CLI Entry Point =======
def main():
    banner()
    print("Z-HESP 2.0 Ready. Type 'encrypt', 'decrypt', 'genkey', or 'exit'.")
    while True:
        try:
            cmd = input("zhesp2 > ").strip()
            if not cmd:
                continue
            args = shlex.split(cmd)
            if args[0] in ['exit', 'quit']:
                break
            elif args[0] == 'encrypt':
                msg = ' '.join(args[1:])
                pwd = getpass.getpass("Passphrase: ")
                print(encrypt(msg, pwd))
            elif args[0] == 'decrypt':
                cipher = args[1]
                pwd = getpass.getpass("Passphrase: ")
                print(decrypt(cipher, pwd))
            elif args[0] == 'genkey':
                generate_key()
            else:
                print("Unknown command.")
        except (KeyboardInterrupt, EOFError):
            print("\n[!] Exiting Z-HESP.")
            break

if __name__ == '__main__':
    main()
