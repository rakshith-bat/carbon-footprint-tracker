import time

class Transaction:
    """Represents a carbon footprint / energy transaction"""
    
    TYPES = {
        "CARBON_LOG": "carbon_footprint_entry",
        "ENERGY_PURCHASE": "energy_trade",
        "GREEN_REWARD": "carbon_credit_reward"
    }

    def __init__(self, tx_type, user, data):
        self.type = tx_type
        self.user = user
        self.data = data
        self.timestamp = time.time()

    @staticmethod
    def create_carbon_log(user, co2, kwh, tag, discount):
        """Create a carbon footprint logging transaction"""
        return Transaction(
            Transaction.TYPES["CARBON_LOG"],
            user,
            {
                "co2": co2,
                "kwh": kwh,
                "tag": tag,
                "discount": discount,
                "base_price": kwh * 6,
                "final_price": round(kwh * 6 * (1 - discount), 2)
            }
        )

    @staticmethod
    def create_green_reward(user, amount, reason):
        """Create a green reward transaction"""
        return Transaction(
            Transaction.TYPES["GREEN_REWARD"],
            user,
            {
                "amount": amount,
                "reason": reason
            }
        )

    def to_dict(self):
        """Convert transaction to dictionary"""
        return {
            "type": self.type,
            "user": self.user,
            "data": self.data,
            "timestamp": self.timestamp
        }

    @staticmethod
    def from_dict(data):
        """Reconstruct transaction from dictionary"""
        tx = Transaction(data["type"], data["user"], data["data"])
        tx.timestamp = data["timestamp"]
        return tx