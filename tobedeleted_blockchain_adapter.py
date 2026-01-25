# blockchain_adapter.py
from core.blockchain import Blockchain
from core.transaction import Transaction

class BlockchainAdapter:
    def __init__(self):
        self.blockchain = Blockchain()
        self.chain = self._export_chain()

    def _export_chain(self):
        """
        Convert Zip2 Block objects → Zip1-style dicts
        """
        exported = []
        for block in self.blockchain.chain:
            for tx in block.transactions:
                exported.append({
                    "user_id": tx.user_id,
                    "transaction_type": tx.transaction_type,
                    "data": tx.data,
                    "timestamp": tx.timestamp,
                    "readable_summary": tx.readable_summary()
                })
        return exported

    def add_transaction(self, user, tx_type, data):
        tx = Transaction(user_id=user, transaction_type=tx_type, data=data)
        self.blockchain.add_transaction(tx)
        self.blockchain.mine()
        self.chain = self._export_chain()

    def get_user_balance(self, user):
        return self.blockchain.get_balance(user)

    def is_chain_valid(self):
        return self.blockchain.is_valid()
