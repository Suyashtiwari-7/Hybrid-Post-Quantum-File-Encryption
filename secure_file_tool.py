#!/usr/bin/env python3
"""
Menu-driven Secure File Encryption Tool (educational)
- Password-based AES-GCM using Argon2 for KDF
- Optional hooks for post-quantum (Kyber) if liboqs is installed
- Uses cryptography.hazmat for streaming AES-GCM to handle large files efficiently
"""
from pathlib import Path
import struct, secrets, json, sys, os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from argon2.low_level import hash_secret_raw, Type
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives import serialization

# Post-quantum cryptography availability - checked lazily to avoid auto-install
OQS_AVAILABLE = None  # None = unchecked, True = available, False = unavailable
oqs = None

CHUNK_SIZE = 64 * 1024  # 64 KB chunks for memory efficiency

class SimulatedKyber:
    """
    Secure X25519 KEM simulation for demonstration purposes.
    Replaces the broken hash-based simulation with a mathematically secure
    Elliptic Curve KEM, mimicking a true Post-Quantum workflow.
    """
    
    def __init__(self, algorithm="Kyber512"):
        self.algorithm = algorithm
    
    def generate_keypair(self):
        priv = X25519PrivateKey.generate()
        pub = priv.public_key()
        pub_bytes = pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        priv_bytes = priv.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        return pub_bytes, priv_bytes
    
    def encap(self, public_key_bytes):
        receiver_pub = X25519PublicKey.from_public_bytes(public_key_bytes)
        ephemeral_priv = X25519PrivateKey.generate()
        ephemeral_pub_bytes = ephemeral_priv.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        shared_secret = ephemeral_priv.exchange(receiver_pub)
        return ephemeral_pub_bytes, shared_secret
    
    def decap(self, ciphertext_bytes, private_key_bytes):
        priv = X25519PrivateKey.from_private_bytes(private_key_bytes)
        ephemeral_pub = X25519PublicKey.from_public_bytes(ciphertext_bytes)
        shared_secret = priv.exchange(ephemeral_pub)
        return shared_secret

class KeyEncapsulation:
    """Wrapper class that mimics liboqs KeyEncapsulation API"""
    def __init__(self, algorithm):
        self.kyber = SimulatedKyber(algorithm)
    
    def generate_keypair(self):
        return self.kyber.generate_keypair()
    
    def encap(self, public_key):
        return self.kyber.encap(public_key)
    
    def decap(self, ciphertext, private_key):
        return self.kyber.decap(ciphertext, private_key)

def check_pq_availability():
    global OQS_AVAILABLE, oqs
    if OQS_AVAILABLE is not None:
        return OQS_AVAILABLE
    
    # First try real liboqs
    try:
        import subprocess
        import os
        
        # Look for liboqs in common locations
        possible_paths = [
            "/usr/lib/liboqs.so",
            "/usr/local/lib/liboqs.so", 
            "/opt/liboqs/lib/liboqs.so",
            "/usr/lib/x86_64-linux-gnu/liboqs.so"
        ]
        
        liboqs_found = any(os.path.exists(path) for path in possible_paths)
        
        if liboqs_found:
            import oqs.oqs as oqs_module
            oqs = oqs_module
            OQS_AVAILABLE = True
            print("🎉 Real liboqs library detected!")
            return True
    except Exception:
        pass
    
    # Fall back to simulation
    print("📚 Using secure X25519 KEM simulation")
    print("   (Shows complete post-quantum workflow safely)")
    OQS_AVAILABLE = True
    return True

USER_DB = Path("user_db.json")
MAGIC = b"SFET"
VERSION = 2

def save_db(db):
    USER_DB.write_text(json.dumps(db, indent=2))

def load_db():
    if USER_DB.exists():
        try:
            return json.loads(USER_DB.read_text())
        except json.JSONDecodeError:
            return {}
    return {}

def derive_key_from_password(password: str, salt: bytes, key_len: int = 32) -> bytes:
    return hash_secret_raw(
        password.encode("utf-8"),
        salt,
        time_cost=3,
        memory_cost=64 * 1024,
        parallelism=2,
        hash_len=key_len,
        type=Type.ID,
    )

def register_user(username: str, password: str):
    db = load_db()
    if username in db:
        print("User already exists.")
        return
    salt = secrets.token_bytes(16)
    verifier = derive_key_from_password(password, salt, key_len=32)
    db[username] = {"salt": salt.hex(), "verifier": verifier.hex()}
    save_db(db)
    print(f"Registered user '{username}'.")

def verify_user(username: str, password: str) -> bool:
    db = load_db()
    if username not in db:
        return False
    salt = bytes.fromhex(db[username]["salt"])
    expect = bytes.fromhex(db[username]["verifier"])
    got = derive_key_from_password(password, salt, key_len=len(expect))
    return got == expect

def pack_header(salt: bytes, kem_ct: bytes, nonce: bytes, pq_used: bool):
    flags = 1 if pq_used else 0
    parts = [
        MAGIC,
        struct.pack("B", VERSION),
        struct.pack("B", flags),
        struct.pack(">H", len(salt)),
        salt,
        struct.pack(">H", len(kem_ct)),
        kem_ct,
        nonce
    ]
    return b"".join(parts)

def unpack_header(f):
    start_pos = f.tell()
    magic = f.read(4)
    if magic != MAGIC:
        raise ValueError("Bad file format or corrupted file.")
    version = struct.unpack("B", f.read(1))[0]
    flags = struct.unpack("B", f.read(1))[0]
    pq_used = bool(flags & 1)
    
    salt_len = struct.unpack(">H", f.read(2))[0]
    salt = f.read(salt_len) if salt_len else b""
    
    kem_len = struct.unpack(">H", f.read(2))[0]
    kem_ct = f.read(kem_len) if kem_len else b""
    
    nonce = f.read(12)
    
    end_pos = f.tell()
    
    # Re-read to return exact header bytes for AAD
    f.seek(start_pos)
    hdr_bytes = f.read(end_pos - start_pos)
    
    return {
        "version": version,
        "pq_used": pq_used,
        "salt": salt,
        "kem_ct": kem_ct,
        "nonce": nonce,
    }, hdr_bytes

def encrypt_with_password(username, password, infile, outfile):
    if not verify_user(username, password):
        print("Authentication failed.")
        return
        
    inpath = Path(infile)
    if not inpath.exists():
        print(f"❌ Error: Input file '{infile}' not found.")
        return

    try:
        # Generate fresh file salt for AES key derivation (fixes static key reuse)
        file_salt = secrets.token_bytes(16)
        key = derive_key_from_password(password, file_salt, key_len=32)
        nonce = secrets.token_bytes(12)
        
        hdr_bytes = pack_header(file_salt, b"", nonce, False)
        
        encryptor = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
        encryptor.authenticate_additional_data(hdr_bytes)
        
        with open(inpath, 'rb') as fin, open(outfile, 'wb') as fout:
            fout.write(hdr_bytes)
            while True:
                chunk = fin.read(CHUNK_SIZE)
                if not chunk:
                    break
                fout.write(encryptor.update(chunk))
            fout.write(encryptor.finalize())
            fout.write(encryptor.tag)
            
        print(f"✅ Encrypted '{outfile}'.")
    except Exception as e:
        print(f"❌ Encryption error: {e}")

def decrypt_with_password(username, password, infile, outfile):
    if not verify_user(username, password):
        print("Authentication failed.")
        return
        
    inpath = Path(infile)
    if not inpath.exists():
        print(f"❌ Error: Input file '{infile}' not found.")
        return

    try:
        file_size = inpath.stat().st_size
        with open(inpath, 'rb') as fin, open(outfile, 'wb') as fout:
            meta, hdr_bytes = unpack_header(fin)
            if meta["pq_used"]:
                print("File uses post-quantum mode; use pq decrypt if supported.")
                return
                
            key = derive_key_from_password(password, meta["salt"], key_len=32)
            
            # Read tag from the end of the file
            fin.seek(-16, os.SEEK_END)
            tag = fin.read(16)
            
            fin.seek(len(hdr_bytes), os.SEEK_SET) # Return to start of ciphertext
            
            decryptor = Cipher(algorithms.AES(key), modes.GCM(meta["nonce"], tag)).decryptor()
            decryptor.authenticate_additional_data(hdr_bytes)
            
            bytes_to_read = file_size - len(hdr_bytes) - 16
            while bytes_to_read > 0:
                chunk_size = min(CHUNK_SIZE, bytes_to_read)
                chunk = fin.read(chunk_size)
                fout.write(decryptor.update(chunk))
                bytes_to_read -= chunk_size
                
            decryptor.finalize() # Validates tag
            
        print(f"✅ Decrypted to '{outfile}'.")
    except ValueError as ve:
        print(f"❌ Decryption error: {ve}")
    except Exception as e:
        print(f"❌ Decryption failed. Incorrect password or tampered file.")

def pq_generate_keypair(priv_out, pub_out, alg="Kyber512"):
    print("\n🔍 Checking post-quantum cryptography availability...")
    if not check_pq_availability():
        print("\n🔒 Post-quantum cryptography simulation failed.")
        return
    
    try:
        print(f"🚀 Generating {alg} keypair...")
        if oqs:  # Real liboqs available
            kem = oqs.KeyEncapsulation(alg)
        else:  # Use secure simulation
            kem = KeyEncapsulation(alg)
        
        pub, priv = kem.generate_keypair()
        Path(pub_out).write_bytes(pub)
        Path(priv_out).write_bytes(priv)
        print(f"✅ PQ keypair generated using {alg}.")
        print(f"🔑 Private key saved to: {priv_out}")
        print(f"🔑 Public key saved to: {pub_out}")
    except Exception as e:
        print(f"❌ Error generating PQ keypair: {e}")

def pq_encrypt_with_pubkey(pubfile, infile, outfile, alg="Kyber512"):
    if not check_pq_availability():
        print("\n🔒 Post-quantum cryptography simulation failed.")
        return
        
    inpath = Path(infile)
    pubpath = Path(pubfile)
    if not inpath.exists() or not pubpath.exists():
        print("❌ Error: Input file or public key not found.")
        return
        
    try:
        print(f"🔐 Encrypting with {alg}...")
        if oqs:  # Real liboqs available
            kem = oqs.KeyEncapsulation(alg)
        else:  # Use secure simulation
            kem = KeyEncapsulation(alg)
        
        pub = pubpath.read_bytes()
        kem_ct, ss = kem.encap(pub)
        
        key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"sfet-pq").derive(ss)
        nonce = secrets.token_bytes(12)
        
        hdr_bytes = pack_header(b"", kem_ct, nonce, True)
        
        encryptor = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
        encryptor.authenticate_additional_data(hdr_bytes)
        
        with open(inpath, 'rb') as fin, open(outfile, 'wb') as fout:
            fout.write(hdr_bytes)
            while True:
                chunk = fin.read(CHUNK_SIZE)
                if not chunk:
                    break
                fout.write(encryptor.update(chunk))
            fout.write(encryptor.finalize())
            fout.write(encryptor.tag)
            
        print(f"✅ PQ encrypted to '{outfile}' using {alg}.")
    except Exception as e:
        print(f"❌ Error during PQ encryption: {e}")

def pq_decrypt_with_privkey(privfile, infile, outfile, alg="Kyber512"):
    if not check_pq_availability():
        print("\n🔒 Post-quantum cryptography simulation failed.")
        return
        
    inpath = Path(infile)
    privpath = Path(privfile)
    if not inpath.exists() or not privpath.exists():
        print("❌ Error: Input file or private key not found.")
        return
        
    try:
        print(f"🔓 Decrypting with {alg}...")
        file_size = inpath.stat().st_size
        
        with open(inpath, 'rb') as fin, open(outfile, 'wb') as fout:
            meta, hdr_bytes = unpack_header(fin)
            if not meta["pq_used"]:
                print("File not PQ-encrypted.")
                return
            
            priv = privpath.read_bytes()
            if oqs:  # Real liboqs available
                kem = oqs.KeyEncapsulation(alg)
            else:  # Use secure simulation
                kem = KeyEncapsulation(alg)
            
            ss = kem.decap(meta["kem_ct"], priv)
            key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"sfet-pq").derive(ss)
            
            # Read tag from end
            fin.seek(-16, os.SEEK_END)
            tag = fin.read(16)
            
            fin.seek(len(hdr_bytes), os.SEEK_SET) # Return to start of ciphertext
            
            decryptor = Cipher(algorithms.AES(key), modes.GCM(meta["nonce"], tag)).decryptor()
            decryptor.authenticate_additional_data(hdr_bytes)
            
            bytes_to_read = file_size - len(hdr_bytes) - 16
            while bytes_to_read > 0:
                chunk_size = min(CHUNK_SIZE, bytes_to_read)
                chunk = fin.read(chunk_size)
                fout.write(decryptor.update(chunk))
                bytes_to_read -= chunk_size
                
            decryptor.finalize()
            
        print(f"✅ PQ decrypted to '{outfile}' using {alg}.")
    except ValueError as ve:
        print(f"❌ Decryption error: {ve}")
    except Exception as e:
        print(f"❌ PQ decryption failed. Incorrect key or tampered file.")

def show_users():
    print("\n👥 REGISTERED USERS DATABASE")
    print("=" * 40)
    db = load_db()
    if not db:
        print("❌ No users registered.")
        print("💡 Use option 1 to register a new user.")
    else:
        print(f"✅ Found {len(db)} registered user(s):")
        print()
        for username, data in db.items():
            print(f"👤 User: {username}")
            print(f"   🔑 Auth Salt: {data['salt'][:16]}...")
            print(f"   🔐 Verifier: {data['verifier'][:16]}...")
            print()
    print("=" * 40)

def menu():
    print("\n" + "="*50)
    print("🔒 SECURE FILE ENCRYPTION TOOL 🔒")
    print("="*50)
    print("📁 Standard Encryption (Available):")
    print("1) Register a user")
    print("2) Encrypt a file with password")
    print("3) Decrypt a file with password")
    print("\n🚀 Post-Quantum Encryption (Kyber):")
    print("4) Post-quantum: Generate Kyber keys")
    print("5) Post-quantum: Encrypt file with Kyber")
    print("6) Post-quantum: Decrypt file with Kyber")
    print("\n🔧 Debug:")
    print("7) Show registered users")
    print("0) Exit")
    print("="*50)

def main():
    while True:
        menu()
        choice = input("Choose an option: ").strip()
        if choice == "1":
            u = input("Username: ").strip()
            p = input("Password: ").strip()
            register_user(u,p)
        elif choice == "2":
            u = input("Username: ").strip()
            p = input("Password: ").strip()
            inf = input("Input file path: ").strip()
            outf = input("Output file path: ").strip()
            encrypt_with_password(u,p,inf,outf)
        elif choice == "3":
            u = input("Username: ").strip()
            p = input("Password: ").strip()
            inf = input("Input encrypted file: ").strip()
            outf = input("Output file path: ").strip()
            decrypt_with_password(u,p,inf,outf)
        elif choice == "4":
            priv = input("Private key file path (save): ").strip()
            pub = input("Public key file path (save): ").strip()
            pq_generate_keypair(priv,pub)
        elif choice == "5":
            pub = input("Public key file path: ").strip()
            inf = input("Input file path: ").strip()
            outf = input("Output file path: ").strip()
            pq_encrypt_with_pubkey(pub,inf,outf)
        elif choice == "6":
            priv = input("Private key file path: ").strip()
            inf = input("Input file path: ").strip()
            outf = input("Output file path: ").strip()
            pq_decrypt_with_privkey(priv,inf,outf)
        elif choice == "7":
            show_users()
        elif choice == "0":
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()
