from algosdk.transaction import AssetConfigTxn, wait_for_confirmation
from algo.wallet import get_treasury, get_algod_client
import json, os
from dotenv import load_dotenv

load_dotenv()

ASSET_ID_FILE = "data/asset_id.json"

def create_green_credit_token():
    """Creates the GreenCredit ASA on Algorand TestNet. Run once."""
    if os.path.exists(ASSET_ID_FILE):
        with open(ASSET_ID_FILE) as f:
            data = json.load(f)
            print(f"Token already exists. Asset ID: {data['asset_id']}")
            return data['asset_id']

    client = get_algod_client()
    address, private_key = get_treasury()
    params = client.suggested_params()

    txn = AssetConfigTxn(
        sender=address,
        sp=params,
        total=10_000_000,       # 10 million tokens max supply
        decimals=2,
        default_frozen=False,
        unit_name="GRC",
        asset_name="GreenCredit",
        manager=address,
        reserve=address,
        freeze=address,
        clawback=address,
        url="https://github.com/rakshith-bat/carbon-footprint-tracker",
        strict_empty_address_check=False
    )

    signed = txn.sign(private_key)
    tx_id = client.send_transaction(signed)
    result = wait_for_confirmation(client, tx_id, 4)
    asset_id = result["asset-index"]

    os.makedirs("data", exist_ok=True)
    with open(ASSET_ID_FILE, "w") as f:
        json.dump({"asset_id": asset_id}, f)

    print(f"GreenCredit token created! Asset ID: {asset_id}")
    return asset_id

def get_asset_id():
    if not os.path.exists(ASSET_ID_FILE):
        return None
    with open(ASSET_ID_FILE) as f:
        return json.load(f)["asset_id"]