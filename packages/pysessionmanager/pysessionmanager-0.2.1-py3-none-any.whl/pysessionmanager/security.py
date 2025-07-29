#pip install pycryptodome
# Importeren van de benodigde modules
import uuid
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(input_password: str, stored_hash: str) -> bool:
    return hash_password(input_password) == stored_hash


def generate_session_id() -> str:
    return str(uuid.uuid4())



class EncryptieDecryptie:
    def __init__(self):
        self.sleutel = get_random_bytes(16)  # Genereer een willekeurige sleutel (16 bytes voor AES-128)
    
    def encrypt(self, waarde):
        """Encrypt een waarde met AES"""
        cipher = AES.new(self.sleutel, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(waarde.encode(), AES.block_size))
        return cipher.iv + ct_bytes  # Voeg IV toe voor decryptie
    
    def decrypt(self, encrypted_waarde):
        """Decrypt een waarde met AES"""
        iv = encrypted_waarde[:16]  # De eerste 16 bytes zijn de IV
        cipher = AES.new(self.sleutel, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted_waarde[16:]), AES.block_size)
        return decrypted.decode()

if __name__ == "__main__":
    # Voorbeeld van gebruik
    encryptie_algoritme = EncryptieDecryptie()
    originele_waarde = "geheimeWachtwoord"
    encrypted_waarde = encryptie_algoritme.encrypt(originele_waarde)
    decrypted_waarde = encryptie_algoritme.decrypt(encrypted_waarde)
    
    print(f"Originele waarde: {originele_waarde}")
    print(f"Encrypted waarde: {encrypted_waarde}")
    print(f"Decrypted waarde: {decrypted_waarde}")
