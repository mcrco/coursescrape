from getpass import getpass
from cryptography.fernet import Fernet

key = Fernet.generate_key()
print(f"Encryption key: {key.decode()}")

cipher = Fernet(key)
password = getpass()
encrypted_password = cipher.encrypt(password.encode())

# write to .env
data = {}
with open(".env", "r") as f:
    for line in f.readlines():
        tokens = line.split("=")
        data[tokens[0]] = tokens[1].strip()

data["DECRYPT_KEY"] = key.decode()
data["PASSWORD"] = encrypted_password.decode()

with open(".env", "w") as f:
    for k, v in data.items():
        print(f"{k}={v}\n", file=f, end="")

print("Password encrypted and saved to .env")
