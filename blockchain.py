import hashlib
import json
import time
import os
from config import Config

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.load_chain()
        
        if not self.chain:
            self.create_block(previous_hash='0', user_id='SYSTEM', transaction_type='GENESIS', data={'message': 'Genesis Block'})

    def create_block(self, user_id, transaction_type, data, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'user_id': user_id,
            'transaction_type': transaction_type,
            'data': data,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
            'nonce': 0,
            'readable_summary': self.generate_readable_summary(user_id, transaction_type, data)
        }
        
        block = self.proof_of_green(block)
        self.chain.append(block)
        self.save_chain()
        return block

    def generate_readable_summary(self, user_id, t_type, data):
        if t_type == 'GENESIS':
            return "The beginning of the Carbon Ledger."
        elif t_type == 'emission':
            return f"User {user_id} logged activity. Net: {data.get('net')}kg CO2. Offset: {data.get('offset')}kg. Score: {data.get('score')}/100."
        elif t_type == 'reward':
            return f"User {user_id} earned {data.get('credits')} Green Credits for eco-friendly behavior."
        elif t_type == 'exchange':
            return f"User {user_id} sent {data.get('amount')} credits to {data.get('recipient')}."
        return "Unknown transaction type."

    def proof_of_green(self, block):
        block['nonce'] = 0
        computed_hash = self.hash(block)
        while not computed_hash.startswith('0'):
            block['nonce'] += 1
            computed_hash = self.hash(block)
        block['hash'] = computed_hash
        return block

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            previous_block = self.chain[i-1]
            current_block = self.chain[i]
            if current_block['previous_hash'] != self.hash(previous_block):
                return False
            if not self.hash(current_block).startswith('0'):
                return False
        return True

    def save_chain(self):
        with open(Config.BLOCKCHAIN_FILE, 'w') as f:
            json.dump(self.chain, f, indent=4)

    def load_chain(self):
        if os.path.exists(Config.BLOCKCHAIN_FILE):
            try:
                with open(Config.BLOCKCHAIN_FILE, 'r') as f:
                    self.chain = json.load(f)
            except (json.JSONDecodeError, ValueError):
                self.chain = []
        else:
            self.chain = []

    def add_transaction(self, user_id, t_type, data):
        return self.create_block(user_id, t_type, data)

    def get_user_balance(self, user_id):
        balance = 0.0
        for block in self.chain:
            t_type = block['transaction_type']
            data = block['data']
            if t_type == 'reward' and block['user_id'] == user_id:
                balance += float(data.get('credits', 0))
            elif t_type == 'exchange':
                if block['user_id'] == user_id:
                    balance -= float(data.get('amount', 0))
                if data.get('recipient') == user_id:
                    balance += float(data.get('amount', 0))
        return round(balance, 2)
