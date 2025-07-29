# Privhat

```
    ____  ____  _____    __   __  _____  ______
   / __ \/ __ \/  _/ |  / /  / / / /   |/_  __/
  / /_/ / /_/ // / | | / /  / /_/ / /| | / /   
 / ____/ _, _// /  | |/ /  / __  / ___ |/ /    
/_/   /_/ |_/___/  |___/  /_/ /_/_/  |_/_/     
                                               
```

Privhat is a lightweight **command-line cryptography tool** written in Python that supports key user management, encryption, decryption, signing, and signature verification with multiple algorithms like RSA, ECC, and ElGamal.

---

## Features

- Create and delete users with keypairs (RSA, ECC, ElGamal)
- Import public keys from JSON files or directly via parameters
- Encrypt messages/files using user public keys or direct keys
- Decrypt messages/files using private keys
- Sign messages and verify signatures (planned features)
- Clean CLI interface with intuitive commands
- Organized storage for keys, messages, and users
- Easily ignore sensitive ciphertext and plaintext files in `.gitignore`

---

## Installation

1. Clone this repository:

```bash
git clone https://github.com/yourusername/privhat.git
cd privhat
````

2. (Optional) Create and activate a Python virtual environment:

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```
---

## 🛠️ Usage

Run the CLI tool using Python:

```bash
python privhat.py [command] [options]
```

### 📋 Commands

#### 👤 Create User

Create a new user and generate a key pair:

```bash
python privhat.py create-user <username> --alg rsa|ecc|elgamal
```

#### ❌ Delete User

Delete an existing user and their stored keys:

```bash
python privhat.py delete-user <username>
```

#### 📥 Import Public Key

Import an RSA public key manually:

```bash
python privhat.py import-pubkey <username> --e <int> --n <int>
```
---

### 🔐 Encrypt

```bash
python privhat.py encrypt [OPTIONS]
```

#### Options:

| Option                      | Description                                  | 
| --------------------------- | -------------------------------------------- | 
| `--to <username>`           | Encrypt using a registered user's public key |     
| `--pubkey-file <path>`      | Encrypt using a public key file (JSON)       |      
| `--text <string>`           | Plaintext input to encrypt                   |    
| `--in <file>`               | Input plaintext file                         |      
| `--out <file>`              | Output ciphertext file                       |          
| `--pubkey-e <value> --pubkey-n <value>` | Encrypt using raw RSA public key components |       
| `--alg <rsa \| ecc \| elgamal>` | Algorithm to use                          |       


#### ✅ Encrypt Examples

**1. Encrypt Text to a User (stored public key)**

```bash
python privhat.py encrypt --to alice --text "Hello Alice" --out hello.enc --alg rsa
```

**2. Encrypt a File to a User**

```bash
python privhat.py encrypt --to alice --in notes.txt --out notes.enc --alg rsa
```

**3. Encrypt Text with a Public Key File**

```bash
python privhat.py encrypt --pubkey-file keys/bob_pubkey.json --text "Secret message" --out msg.enc --alg rsa
```

**4. Encrypt File with a Public Key File**

```bash
python privhat.py encrypt --pubkey-file keys/bob_pubkey.json --in doc.txt --out doc.enc --alg rsa
```

**5. Encrypt Text and Output to Stdout**

```bash
python privhat.py encrypt --to alice --text "Just display this" --alg rsa
```

**6. Encrypt Text Using Raw Public Key Components**

```bash
python privhat.py encrypt --pubkey-e 65537 --pubkey-n 123456789123456789123456789 --text "Hello from raw key" --out out.enc --alg rsa
```
---

### 🔓 Decrypt

```bash
python privhat.py decrypt [OPTIONS]
```

#### Options:

| Option              | Description                                 |
| ------------------- | ------------------------------------------- |
| `--user <username>` | Registered user to use for decryption       |
| `--in <file>`       | Encrypted file input                        |
| `--cipher <string>` | Encrypted ciphertext string (Base64 or hex) |
| `--out <file>`      | Output plaintext file                       |



#### ✅ Decrypt Examples

**1. Decrypt File and Save Output**

```bash
python privhat.py decrypt --user alice --in hello.enc --out hello.txt
```

**2. Decrypt Ciphertext Hex String**

```bash
python privhat.py decrypt --user iloveglass2 --cipher "12345...."
```

---

### 🔁 Summary Matrix


| Use Case                            | Encrypt Command                      | Decrypt Command                                       |
| ----------------------------------- | ------------------------------------ | ----------------------------------------------------- |
| Encrypt text to user                | `--to <user> --text <text>`          | `--user <user> --cipher <hex>`              |
| Encrypt file to user                | `--to <user> --in <file>`            | `--user <user> --in <file>`                           |
| Encrypt text with key file          | `--pubkey-file <file> --text <text>` | *N/A*                                       |
| Encrypt file with key file          | `--pubkey-file <file> --in <file>`   | *N/A*                                       |
| Decrypt file to stdout              | *N/A*                                | `--user <user> --in <file>`                           |
| Decrypt ciphertext string to stdout | *N/A*                                | `--user <user> --cipher <hex>`              |
| Decrypt ciphertext string to file   | *N/A*                                | `--user <user> --cipher <hex> --out <file>` |



---

### ✍️ Sign

```
python privhat.py sign [OPTIONS]
```

#### Options:

| Option                 | Description                                     |
| ---------------------- | ----------------------------------------------- |
| `--user <username>`    | Username whose private key will be used to sign |
| `--in <file>`          | File containing message to sign                 |
| `--text <string>`      | Plaintext message to sign directly              |
| `--out <file>`         | Output file to save the signature (optional)    |
| `--alg <rsa \| ecdsa>` | Algorithm to use for signing (`rsa` or `ecdsa`) |

#### ✅ Sign Examples

**1. Sign Text Message and Save Signature**

```bash
python privhat.py sign --user alice --text "This is a signed message." --out sig.txt --alg rsa
```

**2. Sign File and Save Signature**

```bash
python privhat.py sign --user bob --in important.txt --out important.sig --alg rsa
```

**3. Sign Text Message and Output to Stdout**

```bash
python privhat.py sign --user alice --text "Ephemeral signature" --alg rsa
```

---

### ✅ Verify

```bash
python privhat.py verify [OPTIONS]
```

#### Options:

| Option                 | Description                                             |
| ---------------------- | ------------------------------------------------------- |
| `--from <username>`    | Username whose public key will be used for verification |
| `--in <file>`          | Input file containing the original message              |
| `--text <string>`      | Message to verify directly as string                    |
| `--sig <file>`         | Signature file path                                     |
| `--cipher <string>`    | Signature directly as string (e.g. from stdout)         |
| `--alg <rsa \| ecdsa>` | Algorithm used for signature (`rsa` or `ecdsa`)         |

#### ✅ Verify Examples

**1. Verify Text and Signature File**

```bash
python privhat.py verify --from alice --text "This is a signed message." --sig sig.txt --alg rsa
```

**2. Verify File and Signature File**

```bash
python privhat.py verify --from bob --in important.txt --sig important.sig --alg rsa
```

**3. Verify Text and Signature String**

```bash
python privhat.py verify --from alice --text "Hello world" --cipher "abc123def456..." --alg rsa
```

**4. Verify File with Inline Signature String**

```bash
python privhat.py verify --from bob --in statement.txt --cipher "abcd1234..." --alg rsa
```

---

### 🔁 Summary Matrix

| Use Case                   | Sign Command                   | Verify Command                                        |
| -------------------------- | ------------------------------ | ----------------------------------------------------- |
| Sign text to stdout        | `--text <string>`              | *N/A*                                                 |
| Sign text and save to file | `--text <string> --out <file>` | `--text <string> --sig <file>` or `--cipher <string>` |
| Sign file and save to file | `--in <file> --out <file>`     | `--in <file> --sig <file>` or `--cipher <string>`     |
| Verify text with signature | *N/A*                          | `--text <string> --sig <file>` or `--cipher <string>` |
| Verify file with signature | *N/A*                          | `--in <file> --sig <file>` or `--cipher <string>`     |

---

## Directory Structure

```
privhat/
│
├── privhat.py                  # Main CLI entry point
├── crypto_engine.py        # Core crypto operations
├── user_manager.py         # User and key management
├── storage/
│   ├── users.json          # Registered users
│   ├── keys/               # Private/public keys
│   └── messages/           # Ciphertext/plaintext files (add to .gitignore)
├── requirements.txt
└── README.md
```

---

## Notes

* Current implementation supports RSA fully; ECC and ElGamal are in progress.

---