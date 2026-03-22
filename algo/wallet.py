import os
from algosdk import account, mnemonic
from dotenv import load_dotenv

load_dotenv()

def generate_user_wallet():
    """Creates a fresh Algorand keypair for a new user."""
    private_key, address = account.generate_account()
    mn = mnemonic.from_private_key(private_key)
    return address, mn

def get_treasury():
    """Returns the project treasury address and private key."""
    mn = os.getenv("ALGO_TREASURY_MNEMONIC")
    address = os.getenv("ALGO_TREASURY_ADDRESS")
    private_key = mnemonic.to_private_key(mn)
    return address, private_key

def get_algod_client():
    """Returns a connection to Algorand TestNet."""
    from algosdk.v2client import algod
    return algod.AlgodClient("", "https://testnet-api.algonode.cloud")