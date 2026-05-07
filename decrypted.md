# 🔐 Hybrid Post-Quantum File Encryption (Kyber512 + AES-256)
This repository contains the implementation of a hybrid post-quantum file encryption system that combines:
- 🚀 Kyber512 (Post-Quantum KEM) – secure quantum-resistant key encapsulation
- ⚡ AES-256 – high-speed symmetric encryption for large files
This project is a command-line file encryption tool that demonstrates hybrid encryption using modern symmetric cryptography and a post-quantum–style key exchange workflow. The project is intended for educational and experimental purposes, showing how post-quantum key encapsulation can be combined with symmetric encryption for secure file storage. This is NOT production-ready software.
(📄 ArXiv link will be added after publication)


## ✨ Features
- 🔒 AES-256-GCM for secure file encryption and authentication
- ⚙️ Argon2 for password-based key derivation
- 📁 Hybrid encryption design (KEM → shared secret → AES key)
- 📊 Kyber512 support via liboqs (if available)
- 🧩 Simulated Kyber fallback when liboqs is not installed
- 🆓 Research scripts comparing RSA vs Kyber performance

## 📂 Project Structure
```bash
FileEncryption_Post-quantum_Cryptography/
│
├── src/
│   ├── encrypt.py
│   ├── decrypt.py
│   └── benchmark.py
│
├── samples/
│   ├── sample.txt
│   ├── sample.enc
│   └── sample_dec.txt
│
├── requirements.txt
├── README.md
└── LICENSE
```

## Always Used:
- AES-256-GCM  : file encryption
- HKDF (SHA-256): key derivation
- Argon2       : password hashing
- Python cryptography library

## Conditionally Used:
- Kyber512 (real post-quantum KEM)
 * Only used if liboqs is installed on the system

## Simulated (Fallback):
- Kyber-style key encapsulation
  * Used when liboqs is unavailable
  * Hash-based simulation
  * NOT real post-quantum security

## WARNING:
This project does NOT guarantee real post-quantum security by default. It demonstrates post-quantum workflows only.


## 🛠 Installation
1️⃣ Clone the repository:
git clone https://github.com/Suyashtiwari-7/FileEncryption_Post-quantum_Cryptography
cd FileEncryption_Post-quantum_Cryptography


🛠️ How It Works (High Level)

1. User authenticates using a password
2. A cryptographic key is derived using Argon2
3. For file encryption:
   - Kyber (real or simulated) generates a shared secret
   - Shared secret is expanded using HKDF
   - File is encrypted using AES-256-GCM
4. Encrypted data is stored in a custom binary format


2️⃣ Install Python dependencies:
```bash
pip install -r requirements.txt
```

3️⃣ Install liboqs (required for Kyber512) (Ubuntu / Linux):
```bash
sudo apt update
sudo apt install libssl-dev cmake
git clone https://github.com/open-quantum-safe/liboqs.git
cd liboqs
mkdir build && cd build
cmake .. && make -j
sudo make install
```

## 🔧 Usage
🔒 Encrypt a file:
```
python src/encrypt.py --input secret.txt --output secret.enc
```

🔓 Decrypt a file:
```bash
python src/decrypt.py --input secret.enc --output secret_decrypted.txt
```

📊 Run benchmarks:
python src/benchmark.py

## 📈 Benchmark Environment (Used in Paper)
- 💻 CPU: Intel Core i7
- 🧠 RAM: 16 GB
- 🐧 OS: Ubuntu 22.04
- 📦 Libraries: PyCryptodome, PQClean/liboqs
- 📁 Tested file sizes: 1MB, 100MB, 1GB

## 📁 Sample Files Included
The samples/ directory contains:
- sample.txt – example file
- sample.enc – encrypted output
- sample_dec.txt – decrypted file

## 🧪 Reproducibility
Environment:
Python 3.10+
Ubuntu 22.04+
liboqs latest stable build
Benchmarking includes:
- ⏱ Key generation time
- 🔐 Encryption/decryption time
- 💾 Memory usage
- 📊 Scalability on large files





## 👤 Author
Suyash Jagdish Tiwari
📧 Email: suyashjtiwari@outlook.com
