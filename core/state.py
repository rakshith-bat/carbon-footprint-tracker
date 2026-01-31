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
        # Note: block.transactions might be list of dicts or objects
        transactions = block.transactions if hasattr(block, 'transactions') else block.get('transactions', [])
        
        for tx in transactions:
            user = tx.get("user")
            tx_type = tx.get("type")
            data = tx.get("data", {})

            if not user or user == "SYSTEM":
                continue

            account = self.get_account(user)

            # 1. Logic for Carbon Logging
            if tx_type == "carbon_emission":
                # We round to 2 decimals to keep the leaderboard clean
                account["total_co2"] = round(account["total_co2"] + data.get("net", 0), 2)
                
                score = data.get("score", 0)
                if score >= 70:
                    account["reputation"] = min(100, account["reputation"] + 2)
                elif score < 40:
                    account["reputation"] = max(0, account["reputation"] - 5)

            # 2. Logic for Rewards
            elif tx_type == "carbon_credit_reward":
                # Ensure the balance stays at 2 decimal places
                account["balance"] = round(account["balance"] + data.get("credits", 0), 2)

            # 3. Logic for Peer-to-Peer Energy/Credit Exchange
            elif tx_type == "credit_transfer":
                amount = data.get("amount", 0)
                recipient_name = data.get("recipient")
                
                if recipient_name and account["balance"] >= amount:
                    account["balance"] = round(account["balance"] - amount, 2)
                    recipient_account = self.get_account(recipient_name)
                    recipient_account["balance"] = round(recipient_account["balance"] + amount, 2)

    def rebuild_from_chain(self, chain):
        """Reset and replay the entire history to get current state"""
        self.accounts = {}
        for block in chain:
            self.apply_block(block)