import hashlib

def encrypt_password(password):

    return hashlib.md5(password.encode()).hexdigest()

class Password:
    def __init__(self, password):
        self.password = encrypt_password(password)

    def set_password(self, encrypted_password):
        self.password = encrypted_password