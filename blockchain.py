import hashlib
import time

# -------------------------
# Block definition
# -------------------------
class Block:
    def __init__(self, idx, user, co2, kwh, prev_hash):
        self.index = idx
        self.timestamp = time.ctime()
        self.user = user
        self.co2 = co2          # net CO2 after offset
        self.kwh = kwh          # renewable energy used
        self.prev_hash = prev_hash
        self.hash = self.calc_hash()

    def calc_hash(self):
        data = f"{self.index}{self.timestamp}{self.user}{self.co2}{self.kwh}{self.prev_hash}"
        return hashlib.sha256(data.encode()).hexdigest()


# -------------------------
# Blockchain definition
# -------------------------
class EnergyChain:
    def __init__(self):
        self.chain = [self.genesis()]

    def genesis(self):
        return Block(0, "SYSTEM", 0, 0, "0")

    def buy_energy(self, user, co2, kwh):
        """
        Add a new block for a user purchase / emission record
        """
        prev_block = self.chain[-1]
        block = Block(
            idx=len(self.chain),
            user=user,
            co2=co2,
            kwh=kwh,
            prev_hash=prev_block.hash
        )
        self.chain.append(block)
        # Optionally return the block
        return block
