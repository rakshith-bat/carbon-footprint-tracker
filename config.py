import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'cyberpunk-carbon-secret-key-2077'
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
    BLOCKCHAIN_FILE = os.path.join(DATA_DIR, 'blockchain.json')
    USERS_FILE = os.path.join(DATA_DIR, 'users.json')
    TRANSACTIONS_FILE = os.path.join(DATA_DIR, 'transactions.json')
