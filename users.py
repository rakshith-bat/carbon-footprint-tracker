import json
import os
import hashlib
from config import Config

class UserManager:
    def __init__(self):
        self.users = {}
        self.load_users()

    def load_users(self):
        if os.path.exists(Config.USERS_FILE):
            try:
                with open(Config.USERS_FILE, 'r') as f:
                    self.users = json.load(f)
            except:
                self.users = {}

    def save_users(self):
        with open(Config.USERS_FILE, 'w') as f:
            json.dump(self.users, f, indent=4)

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, username, password):
        if username in self.users:
            return False, "Username already exists"
        
        self.users[username] = {
            'password': self.hash_password(password),
            'joined_at': str(os.times())
        }
        self.save_users()
        return True, "Registration successful"

    def login(self, username, password):
        if username not in self.users:
            return False
        
        if self.users[username]['password'] == self.hash_password(password):
            return True
        return False

    def get_all_users(self):
        return list(self.users.keys())
