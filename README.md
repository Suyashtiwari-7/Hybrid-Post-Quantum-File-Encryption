# 🔐 Hybrid PQ-Secure Vault

> A robust, command-line utility demonstrating the modern **hybrid encryption** paradigm: combining the mathematical safety of Post-Quantum (PQ) Key Encapsulation with the speed of AES-256-GCM symmetric encryption.

---

## 📖 Overview

**Hybrid PQ-Secure Vault** is an educational and highly secure cross-platform tool. It was built to demonstrate how the industry is preparing for the post-quantum era. By utilizing a **Key Encapsulation Mechanism (KEM)** to securely exchange a secret key—and then using that key for fast bulk-data encryption—the tool perfectly mimics real-world enterprise deployments of hybrid cryptography.

### ✨ Key Security Features

- **Post-Quantum Simulation (X25519 KEM):** Implements a mathematically sound elliptic-curve Diffie-Hellman Key Encapsulation Mechanism to simulate Kyber-style workflows when the heavy `liboqs` library is unavailable.
- **Robust Key Derivation:** Uses **Argon2** for password hashing and HKDF for deriving AES keys from shared secrets.
- **Per-File Random Salts:** Generates a fresh 16-byte random salt for every single file, entirely eliminating static key reuse vulnerabilities.
- **Authenticated Encryption (AAD):** Binds the custom file metadata (magic bytes, version flags, nonces, and KEM ciphertexts) as **Associated Data** to the AES-GCM cipher, ensuring immediate detection of any file tampering.
- **Memory-Safe Chunking:** Streams file data in constant 64 KB chunks, allowing the encryption of gigabyte or terabyte-scale files without crashing or exhausting system RAM.

---

## 🚀 Quick Start

### 1. Requirements
Ensure you have Python 3.8+ installed. Then install the required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Launching the Tool
**On Windows:**
Simply double-click the included `run_tool.bat` file, or run it from PowerShell:
```powershell
cd C:\Users\Lenovo\Documents\CODE\Hybrid-Post-Quantum-File-Encryption-main\Hybrid-PQ-Secure-Vault
.\run_tool.bat
```

**On Linux / macOS:**
```bash
python secure_file_tool.py
```

### 3. Usage Workflows

You will be presented with an interactive CLI menu.

**Option A: Standard Password Encryption**
1. Press `1` to **Register** a new user with a secure password.
2. Press `2` to **Encrypt** a file using your credentials.
3. Press `3` to **Decrypt** the file back to its original state.

**Option B: Post-Quantum Public/Private Key Encryption**
1. Press `4` to **Generate** a new Public/Private key pair (e.g., `pub.key` and `priv.key`).
2. Press `5` to **Encrypt** a file using the Public Key (can be done by anyone).
3. Press `6` to **Decrypt** the file using the Private Key (can only be done by you).

---

## 🔐 Cryptographic Architecture

### The File Header (Version 2 Format)
Every encrypted file produced by this tool contains a strict binary header that dictates how the ciphertext should be processed. The entire header is passed to AES-GCM as **AAD (Additional Authenticated Data)**.

```text
+--------------------+-------------------+--------------------+-------------------+-----------+
| MAGIC (4 bytes)    | VERSION (1 byte)  | FLAGS (1 byte)      | SALT_LEN (2 BE)   | SALT …   |
+--------------------+-------------------+--------------------+-------------------+-----------+
| KEM_CT_LEN (2 BE)  | KEM_CT …           | NONCE (12 bytes)   | PAYLOAD …         | GCM TAG (16) |
+--------------------+-------------------+--------------------+-------------------+-----------+
```
- **FLAGS bit 0:** If set to `1`, the file was encrypted using the PQ flow and the `KEM_CT` (Key Encapsulation Ciphertext) field is populated.

---

## 📂 Repository Structure

```text
Hybrid-PQ-Secure-Vault/
├── secure_file_tool.py      # Core application containing all cryptographic logic
├── run_tool.bat             # Windows launcher to handle UTF-8 terminal encoding
├── requirements.txt         # Python dependency list
├── user_db.json             # Local database storing usernames and Argon2 verifiers
├── *.key / *.enc            # Output directory for generated keys and encrypted vaults
└── README.md                # Project documentation
```

---

## 🎯 Educational Value & Future Enhancements

This project serves as an excellent portfolio piece demonstrating a deep understanding of modern cryptography, memory management, and secure software engineering principles.

**Future roadmap possibilities:**
- Integration of the official `liboqs` Python wrapper for true NIST Kyber512 post-quantum security.
- Addition of RSA or ECDSA digital signatures for verifiable end-to-end file authenticity.
- Development of a lightweight graphical user interface (GUI) using Tkinter or PyQt.

