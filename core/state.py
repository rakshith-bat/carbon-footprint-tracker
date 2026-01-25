class GlobalState:
    def __init__(self):
        # Maps user names to their current status
        self.accounts = {} 

    def get_account(self, user):
        """Initialize account if it doesn't exist"""
        if user not in self.accounts:
            self.accounts[user] = {
                "balance": 0.0,       # Carbon Credits
                "total_co2": 0.0,     # Total emissions logged
                "total_kwh": 0.0,     # Total energy used
                "green_points": 0,    # Number of Green tags earned
                "reputation": 50.0    # Starts at 50, goes up or down
            }
        return self.accounts[user]

    def apply_block(self, block):
        """Scan a block and update the global state based on transactions"""
        for tx in block.transactions:
            user = tx.get("user")
            tx_type = tx.get("type")
            data = tx.get("data", {})

            if not user or user == "SYSTEM":
                continue

            account = self.get_account(user)

            # Logic for Carbon Logging Transactions
            if tx_type == "carbon_footprint_entry":
                account["total_co2"] += data.get("co2", 0)
                account["total_kwh"] += data.get("kwh", 0)
                
                if data.get("tag") == "GREEN":
                    account["green_points"] += 1
                    account["reputation"] = min(100, account["reputation"] + 2)
                elif data.get("tag") == "RED":
                    account["reputation"] = max(0, account["reputation"] - 5)

            # Logic for Reward Transactions
            elif tx_type == "carbon_credit_reward":
                account["balance"] += data.get("amount", 0)

    def rebuild_from_chain(self, chain):
        """Wipe state and re-process the entire chain to ensure accuracy"""
        self.accounts = {}
        for block in chain:
            self.apply_block(block)