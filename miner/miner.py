import time
from consensus.pow import ProofOfWork

class Miner:
    def __init__(self, blockchain, node, miner_address):
        self.blockchain = blockchain
        self.node = node
        self.miner_address = miner_address
        self.is_mining = False

    def start_mining(self):
        self.is_mining = True
        threading.Thread(target=self.mine_loop, daemon=True).start()

    def mine_loop(self):
        while self.is_mining:
            if len(self.blockchain.pending_transactions) > 0:
                print("⚒️  Pending transactions found! Starting mining...")
                new_block = self.blockchain.mine_pending_transactions(self.miner_address)
                
                if new_block:
                    # Broadcast the discovery to the network
                    self.node.broadcast("NEW_BLOCK", new_block.to_dict())
            time.sleep(2) # Poll every 2 seconds