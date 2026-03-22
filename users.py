import json
import os
import hashlib
from config import Config
from algo.wallet import generate_user_wallet
from algosdk import mnemonic as algo_mnemonic


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
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        with open(Config.USERS_FILE, 'w') as f:
            json.dump(self.users, f, indent=4)

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, username, password, city='Other', monthly_goal=300.0, user_type='consumer'):
        if username in self.users:
            return False, "Username already exists"
        algo_address, algo_mn = generate_user_wallet()
        self.users[username] = {
            'password':        self.hash_password(password),
            'joined_at':       str(os.times()),
            'city':            city,
            'monthly_goal':    monthly_goal,
            'streak':          0,
            'last_entry_date': None,
            'algo_address':    algo_address,
            'algo_mnemonic':   algo_mn,
            'user_type':       user_type,
            }
        self.save_users()
        return True, "Registration successful"

    def login(self, username, password):
        if username not in self.users:
            return False
        return self.users[username]['password'] == self.hash_password(password)

    def get_user(self, username):
        return self.users.get(username, {})

    def update_user(self, username, fields: dict):
        if username in self.users:
            self.users[username].update(fields)
            self.save_users()

    def update_streak(self, username, today_str, below_average):
        user = self.users.get(username, {})
        last = user.get('last_entry_date')
        streak = user.get('streak', 0)
        if last == today_str:
            return streak
        if below_average:
            streak += 1
        else:
            streak = 0
        self.update_user(username, {
            'streak': streak,
            'last_entry_date': today_str
        })
        return streak

    def get_algo_address(self, username):
        return self.users.get(username, {}).get('algo_address')

    def get_algo_private_key(self, username):
        mn = self.users.get(username, {}).get('algo_mnemonic')
        if mn:
            return algo_mnemonic.to_private_key(mn)
        return None

    def get_all_users(self):
        return list(self.users.keys())