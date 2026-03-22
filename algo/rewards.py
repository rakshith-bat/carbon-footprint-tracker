from algosdk.transaction import AssetTransferTxn, wait_for_confirmation
from algo.wallet import get_treasury, get_algod_client
from algo.token import get_asset_id
from algosdk.transaction import AssetTransferTxn, PaymentTxn, wait_for_confirmation
import json

def opt_in_user(user_address, user_private_key):
    """User must opt-in to receive GRC tokens. Called once on registration."""
    client = get_algod_client()
    asset_id = get_asset_id()
    if not asset_id:
        return None

    params = client.suggested_params()
    txn = AssetTransferTxn(
        sender=user_address,
        sp=params,
        receiver=user_address,
        amt=0,
        index=asset_id
    )
    signed = txn.sign(user_private_key)
    tx_id = client.send_transaction(signed)
    wait_for_confirmation(client, tx_id, 4)
    return tx_id

def send_green_credits(user_address, amount_credits):
    """Treasury sends GRC tokens to a user. Auto opts-in if needed."""
    client = get_algod_client()
    asset_id = get_asset_id()
    treasury_address, treasury_key = get_treasury()

    if not asset_id:
        print("No asset ID found.")
        return None

    # Check if user is opted in, if not — do it from treasury
    try:
        info = client.account_info(user_address)
        opted_in = any(a['asset-id'] == asset_id for a in info.get('assets', []))
    except:
        opted_in = False

    if not opted_in:
        params = client.suggested_params()
        # Treasury funds the opt-in on behalf of the user
        opt_txn = AssetTransferTxn(
            sender=user_address,
            sp=params,
            receiver=user_address,
            amt=0,
            index=asset_id
        )
        # Can't sign as user from treasury — so treasury sends a tiny ALGO
        # to cover fees, then user opts in via a payment note trick.
        # Simpler: treasury does a clawback-style workaround.
        # REAL fix: treasury signs opt-in using user's stored key
        from algo.wallet import get_algod_client as _c
        from algosdk.transaction import AssetTransferTxn as ATxn
        from users import UserManager
        um = UserManager()
        # Find username by address
        user_pk = None
        for uname in um.get_all_users():
            if um.get_algo_address(uname) == user_address:
                user_pk = um.get_algo_private_key(uname)
                break
        if user_pk:
            params = client.suggested_params()
            optin_txn = AssetTransferTxn(
                sender=user_address,
                sp=params,
                receiver=user_address,
                amt=0,
                index=asset_id
            )
            signed_optin = optin_txn.sign(user_pk)
            tx_id = client.send_transaction(signed_optin)
            wait_for_confirmation(client, tx_id, 4)
            print(f"Auto opted-in {user_address}")

    # Now send the tokens
    amount_units = int(amount_credits * 100)
    params = client.suggested_params()
    txn = AssetTransferTxn(
        sender=treasury_address,
        sp=params,
        receiver=user_address,
        amt=amount_units,
        index=asset_id
    )
    signed = txn.sign(treasury_key)
    tx_id = client.send_transaction(signed)
    wait_for_confirmation(client, tx_id, 4)
    print(f"Sent {amount_credits} GRC to {user_address} | TxID: {tx_id}")
    return tx_id

    def fund_new_wallet(user_address):
    """Send a tiny amount of ALGO to a new user wallet to cover future fees."""
    client = get_algod_client()
    treasury_address, treasury_key = get_treasury()
    params = client.suggested_params()

    txn = PaymentTxn(
        sender=treasury_address,
        sp=params,
        receiver=user_address,
        amt=500_000,  # 0.5 ALGO — enough for ~500 transactions
    )
    signed = txn.sign(treasury_key)
    tx_id = client.send_transaction(signed)
    wait_for_confirmation(client, tx_id, 4)
    print(f"Funded new wallet {user_address} with 0.5 ALGO | TxID: {tx_id}")
    return tx_id
def fund_new_wallet(user_address):
    """Send a tiny amount of ALGO to a new user wallet to cover future fees."""
    client = get_algod_client()
    treasury_address, treasury_key = get_treasury()
    params = client.suggested_params()

    txn = PaymentTxn(
        sender=treasury_address,
        sp=params,
        receiver=user_address,
        amt=500_000,  # 0.5 ALGO — enough for ~500 transactions
    )
    signed = txn.sign(treasury_key)
    tx_id = client.send_transaction(signed)
    wait_for_confirmation(client, tx_id, 4)
    print(f"Funded new wallet {user_address} with 0.5 ALGO | TxID: {tx_id}")
    return tx_id
    
def get_user_token_balance(user_address):
    """Returns the user's GRC balance from the actual chain."""
    client = get_algod_client()
    asset_id = get_asset_id()
    if not asset_id:
        return 0
    try:
        info = client.account_info(user_address)
        for asset in info.get("assets", []):
            if asset["asset-id"] == asset_id:
                return asset["amount"] / 100  # convert back to credits
        return 0
    except:
        return 0