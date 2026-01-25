import time

class ProofOfWork:
    @staticmethod
    def mine(block):
        """
        Proof of Work mining algorithm.
        Increments nonce until hash starts with required number of zeros.
        """
        target = "0" * block.difficulty
        
        print(f"⛏️  Mining block {block.index} (difficulty {block.difficulty})...")
        start_time = time.time()
        
        while True:
            block.hash = block.compute_hash()
            
            # Check if hash meets difficulty requirement
            if block.hash.startswith(target):
                elapsed = time.time() - start_time
                print(f"✅ Block {block.index} mined! Hash: {block.hash[:16]}... ({elapsed:.2f}s, {block.nonce} attempts)")
                return block
            
            # Try next nonce
            block.nonce += 1