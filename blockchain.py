import time
from core.block import Block
from core.transaction import Transaction
from core.state import GlobalState
from consensus.pow import ProofOfWork
from storage.disk import DiskStorage
from config import Config, DIFFICULTY

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.difficulty = DIFFICULTY
        self.state = GlobalState()  # Tracks balances/stats automatically
        
        # Load existing chain or create genesis
        self.load_chain()
        
        # Build state from loaded chain
        self.refresh_state()

    def create_genesis_block(self):
        """Create the first block in the chain"""
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
        
        # Mine the genesis block
        ProofOfWork.mine(block)
        return block

    def refresh_state(self):
        """Rebuild state from chain history"""
        self.state.rebuild_from_chain(self.chain)

    def get_latest_block(self):
        """Return most recent block"""
        return self.chain[-1] if self.chain else None

    def add_transaction(self, user_id, t_type, data):
        """Add transaction and auto-mine block"""
        # Map old transaction types to new format
        type_mapping = {
            'emission': 'carbon_emission',
            'reward': 'carbon_credit_reward',
            'exchange': 'credit_transfer',
            'GENESIS': 'GENESIS'
        }
        
        mapped_type = type_mapping.get(t_type, t_type)
        
        # Create transaction object
        tx = Transaction(
            tx_type=mapped_type,
            user=user_id,
            data=data
        )
        
        self.pending_transactions.append(tx.to_dict())
        
        # Auto-mine block (for simplicity in web app)
        block = self.mine_pending_transactions(user_id)
        return block

    def mine_pending_transactions(self, miner_address):
        """Mine new block with pending transactions"""
        if not self.pending_transactions:
            return None

        # Create new block
        new_block = Block(
            index=len(self.chain),
            transactions=self.pending_transactions.copy(),
            prev_hash=self.get_latest_block().hash if self.get_latest_block() else "0",
            difficulty=self.difficulty
        )
        
        # Mine it with PoW
        ProofOfWork.mine(new_block)
        
        # Add to chain
        self.chain.append(new_block)
        
        # Update state immediately
        self.state.apply_block(new_block)
        
        # Clear pending pool
        self.pending_transactions = []
        
        # Save to disk
        self.save_chain()
        
        return new_block

    def generate_readable_summary(self, block):
        """Generate human-readable summary for a block"""
        if not block.transactions:
            return "Empty block"
        
        tx = block.transactions[0]  # First transaction
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
        """Get user balance from state (O(1) instead of O(n))"""
        account = self.state.get_account(user_id)
        return account.get('balance', 0.0)

    def get_user_stats(self, user_id):
        """Get comprehensive user stats"""
        return self.state.get_account(user_id)

    def is_chain_valid(self):
        """Validate entire blockchain"""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            
            # Check hash integrity
            if current.hash != current.compute_hash():
                return False
            
            # Check linkage
            if current.prev_hash != previous.hash:
                return False
            
            # Check PoW
            if not current.hash.startswith("0" * current.difficulty):
                return False
        
        return True

    def save_chain(self):
        """Save chain to disk"""
        chain_data = [block.to_dict() for block in self.chain]
        DiskStorage.save_to_disk(Config.BLOCKCHAIN_FILE, chain_data)

    def load_chain(self):
        """Load chain from disk"""
        data = DiskStorage.load_from_disk(Config.BLOCKCHAIN_FILE)
        
        if data:
            try:
                self.chain = [Block.from_dict(b) for b in data]
            except Exception as e:
                print(f"⚠️ Error loading chain: {e}. Creating fresh genesis.")
                self.chain = [self.create_genesis_block()]
                self.save_chain()
        else:
            # No existing chain, create genesis
            self.chain = [self.create_genesis_block()]
            self.save_chain()

    # COMPATIBILITY METHODS for old Flask routes
    def get_chain_as_dicts(self):
        """Return chain as list of dicts (for templates)"""
        result = []
        for block in self.chain:
            block_dict = block.to_dict()
            block_dict['readable_summary'] = self.generate_readable_summary(block)
            block_dict['user_id'] = block.transactions[0].get('user', 'SYSTEM') if block.transactions else 'SYSTEM'
            block_dict['transaction_type'] = block.transactions[0].get('type', 'unknown') if block.transactions else 'unknown'
            block_dict['data'] = block.transactions[0].get('data', {}) if block.transactions else {}
            result.append(block_dict)
        return result