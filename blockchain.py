import time
from core.block import Block
from core.transaction import Transaction
from core.state import GlobalState
from consensus.pow import ProofOfWork
from storage.disk import DiskStorage
from config import Config, DIFFICULTY


print(" LOADED blockchain.py (DICT VERSION)")

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.difficulty = DIFFICULTY
        self.state = GlobalState()
        
        self.load_chain()
        self.refresh_state()

    def create_genesis_block(self):
        genesis_tx = Transaction(
            tx_type="GENESIS",
            user="SYSTEM",
            data={"message": "Genesis Block - Carbon Ledger Initialized"}
        )
        
        block = Block(
            index=0,
            transactions=[genesis_tx.to_dict()],
            prev_hash="0",
            difficulty=self.difficulty
        )
        
        ProofOfWork.mine(block)
        return block

    def refresh_state(self):
        self.state.rebuild_from_chain(self.chain)

    def get_latest_block(self):
        return self.chain[-1] if self.chain else None

    def add_transaction(self, user_id, t_type, data):
        type_mapping = {
            'emission': 'carbon_emission',
            'reward': 'carbon_credit_reward',
            'exchange': 'credit_transfer',
            'GENESIS': 'GENESIS'
        }
        
        mapped_type = type_mapping.get(t_type, t_type)
        
        tx = Transaction(
            tx_type=mapped_type,
            user=user_id,
            data=data
        )
        
        self.pending_transactions.append(tx.to_dict())
        block = self.mine_pending_transactions(user_id)
        return block

    def mine_pending_transactions(self, miner_address):
        if not self.pending_transactions:
            return None

        new_block = Block(
            index=len(self.chain),
            transactions=self.pending_transactions.copy(),
            prev_hash=self.get_latest_block().hash if self.get_latest_block() else "0",
            difficulty=self.difficulty
        )
        
        ProofOfWork.mine(new_block)
        self.chain.append(new_block)
        self.state.apply_block(new_block)
        self.pending_transactions = []
        self.save_chain()
        
        return new_block

    def generate_readable_summary(self, block):
        if hasattr(block, 'transactions'):
            transactions = block.transactions
        else:
            transactions = block.get('transactions', [])
        
        if not transactions:
            return "Empty block"
        
        tx = transactions[0] if isinstance(transactions[0], dict) else transactions[0]
        user = tx.get('user', 'Unknown')
        tx_type = tx.get('type', 'unknown')
        data = tx.get('data', {})
        
        if tx_type == 'GENESIS':
            return "The beginning of the Carbon Ledger."
        elif tx_type == 'carbon_emission':
            return f"User {user} logged activity. Net: {data.get('net')}kg CO2. Offset: {data.get('offset')}kg. Score: {data.get('score')}/100."
        elif tx_type == 'carbon_credit_reward':
            return f"User {user} earned {data.get('credits')} Green Credits for eco-friendly behavior."
        elif tx_type == 'credit_transfer':
            return f"User {user} sent {data.get('amount')} credits to {data.get('recipient')}."
        
        return f"{tx_type} transaction by {user}"

    def get_user_balance(self, user_id):
        account = self.state.get_account(user_id)
        return account.get('balance', 0.0)

    def get_user_stats(self, user_id):
        return self.state.get_account(user_id)

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            
            if current.hash != current.compute_hash():
                return False
            if current.prev_hash != previous.hash:
                return False
            if not current.hash.startswith("0" * current.difficulty):
                return False
        
        return True

    def save_chain(self):
        chain_data = [block.to_dict() for block in self.chain]
        DiskStorage.save_to_disk(Config.BLOCKCHAIN_FILE, chain_data)

    def load_chain(self):
        data = DiskStorage.load_from_disk(Config.BLOCKCHAIN_FILE)
        
        if data:
            try:
                self.chain = [Block.from_dict(b) for b in data]
            except Exception as e:
                print(f"⚠️ Error loading chain: {e}. Creating fresh genesis.")
                self.chain = [self.create_genesis_block()]
                self.save_chain()
        else:
            self.chain = [self.create_genesis_block()]
            self.save_chain()

    def get_chain_as_dicts(self):
        result = []
        
        for block in self.chain:
            block_dict = block.to_dict()
            block_dict['readable_summary'] = self.generate_readable_summary(block)
            
            transactions = block_dict.get('transactions', [])
            
            if transactions and len(transactions) > 0:
                first_tx = transactions[0]
                block_dict['user_id'] = first_tx.get('user', 'SYSTEM')
                block_dict['transaction_type'] = first_tx.get('type', 'unknown')
                block_dict['data'] = first_tx.get('data', {})
            else:
                block_dict['user_id'] = 'SYSTEM'
                block_dict['transaction_type'] = 'unknown'
                block_dict['data'] = {}
            
            result.append(block_dict)
        
        return result