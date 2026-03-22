from algosdk.transaction import PaymentTxn, wait_for_confirmation
from algo.wallet import get_treasury, get_algod_client
import json, base64

def record_emission_on_chain(user_id, net_emissions, eco_score):
    """
    Writes a tiny payment tx to self with emission data in the note field.
    This makes the carbon record immutable and publicly verifiable on TestNet.
    """
    client = get_algod_client()
    address, private_key = get_treasury()
    params = client.suggested_params()

    note_data = {
        "user": user_id,
        "net_kg": round(net_emissions, 2),
        "score": eco_score,
        "type": "carbon_emission"
    }
    note_bytes = json.dumps(note_data).encode()

    txn = PaymentTxn(
        sender=address,
        sp=params,
        receiver=address,
        amt=0,           # 0 ALGO, just writing the note
        note=note_bytes
    )
    signed = txn.sign(private_key)
    tx_id = client.send_transaction(signed)
    wait_for_confirmation(client, tx_id, 4)
    print(f"Emission recorded on-chain | TxID: {tx_id}")
    return tx_id