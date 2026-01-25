import json
import os

class DiskStorage:
    """
    Handles all persistent data storage for the blockchain.
    Centralizing this prevents data corruption and makes it easy
    to change storage formats (e.g., from JSON to SQL) later.
    """

    @staticmethod
    def save_to_disk(filename, data):
        """Write Python data to a JSON file"""
        try:
            # We use indent=2 to make the ledger human-readable
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Storage Error (Save): {e}")
            return False

    @staticmethod
    def load_from_disk(filename):
        """Read data from a JSON file and return a Python object"""
        if not os.path.exists(filename):
            return None
            
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"❌ Storage Error (Load): {e}")
            return None

    @staticmethod
    def delete_ledger(filename):
        """Utility to wipe the chain (useful for testing)"""
        if os.path.exists(filename):
            os.remove(filename)
            print(f"🗑️  Ledger {filename} has been wiped.")