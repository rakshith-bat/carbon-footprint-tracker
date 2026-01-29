import time

class GlobalState:
    def __init__(self):
        self.accounts = {}

    # ----------------------------------
    # Helpers
    # ----------------------------------
    def ensure_account(self, user_id):
        if user_id not in self.accounts:
            self.accounts[user_id] = {
                "balance": 0.0,
                "total_emissions": 0.0,
                "eco_score_sum": 0,
                "emission_count": 0,
                "created_at": time.time()
            }

    def get_account(self, user_id):
        self.ensure_account(user_id)
        return self.accounts[user_id]

    # ----------------------------------
    # Core logic
    # ----------------------------------
    def apply_block(self, block):
        for tx in block.transactions:
            tx_type = tx.get("type")
            user = tx.get("user")
            data = tx.get("data", {})

            if not user:
                continue

            # ---------- EMISSION ----------
            if tx_type == "carbon_emission":
                self.ensure_account(user)
                net = float(data.get("net", 0))
                score = int(data.get("score", 0))

                self.accounts[user]["total_emissions"] += net
                self.accounts[user]["eco_score_sum"] += score
                self.accounts[user]["emission_count"] += 1

            # ---------- REWARD ----------
            elif tx_type == "carbon_credit_reward":
                credits = float(data.get("credits", 0))
                self.ensure_account(user)
                self.accounts[user]["balance"] += credits

            # ---------- TRANSFER ----------
            elif tx_type == "credit_transfer":
                sender = user
                recipient = data.get("recipient")
                amount = float(data.get("amount", 0))

                if not recipient:
                    continue

                self.ensure_account(sender)
                self.ensure_account(recipient)

                self.accounts[sender]["balance"] -= amount
                self.accounts[recipient]["balance"] += amount

            # ---------- GENESIS ----------
            elif tx_type == "GENESIS":
                pass

    # ----------------------------------
    # 🔥 THIS WAS THE MISSING PIECE
    # ----------------------------------
    def rebuild_from_chain(self, chain):
        self.accounts = {}
        for block in chain:
            self.apply_block(block)
