import json, os, uuid, datetime
import time

# Cache so we don't fetch on every page load
_price_cache = {'data': None, 'fetched_at': 0}
CACHE_SECONDS = 3600  # 1 hour


CONTRACTS_FILE = "data/contracts.json"
GRC_TO_INR = 12.5  # fictional display only

def load_contracts():
    if not os.path.exists(CONTRACTS_FILE):
        return {}
    try:
        with open(CONTRACTS_FILE) as f:
            return json.load(f)
    except:
        return {}

def save_contracts(data):
    with open(CONTRACTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def post_contract(vendor_username, energy_type, quantity, price_grc, duration_months, description):
    contracts = load_contracts()
    contract_id = str(uuid.uuid4())[:8]
    contracts[contract_id] = {
        'id':             contract_id,
        'vendor':         vendor_username,
        'energy_type':    energy_type,
        'quantity':       quantity,
        'price_grc':      price_grc,
        'price_inr':      round(price_grc * GRC_TO_INR, 2),
        'duration_months': duration_months,
        'description':    description,
        'posted_at':      datetime.date.today().isoformat(),
        'status':         'open'
    }
    save_contracts(contracts)
    return contract_id

def get_open_contracts():
    contracts = load_contracts()
    return [c for c in contracts.values() if c.get('status') == 'open']

def get_vendor_contracts(vendor_username):
    contracts = load_contracts()
    return [c for c in contracts.values() if c.get('vendor') == vendor_username]

def close_contract(contract_id):
    contracts = load_contracts()
    if contract_id in contracts:
        contracts[contract_id]['status'] = 'closed'
        save_contracts(contracts)

def delete_contract(contract_id, vendor_username):
    contracts = load_contracts()
    if contract_id in contracts and contracts[contract_id]['vendor'] == vendor_username:
        del contracts[contract_id]
        save_contracts(contracts)
FALLBACK_PRICES = {
    'petrol_per_litre':  94.77,
    'diesel_per_litre':  87.67,
    'crude_per_barrel':  110.96,
    'electricity_per_kwh': 7.0,
    'source': 'fallback',
    'as_of': 'Mar 2026'
}

# State-wise electricity rates (CEA 2024)
STATE_ELECTRICITY_RATES = {
    'Tamil Nadu':    6.5,
    'Karnataka':     7.2,
    'Maharashtra':   8.5,
    'Delhi':         7.0,
    'Gujarat':       5.8,
    'Rajasthan':     6.9,
    'Uttar Pradesh': 6.2,
    'West Bengal':   7.5,
    'Telangana':     7.8,
    'Kerala':        4.5,
    'Punjab':        7.1,
    'Haryana':       7.3,
    'Other':         7.0
}

def get_market_prices():
    """Fetch live prices or return cached/fallback."""
    global _price_cache
    now = time.time()

    if _price_cache['data'] and (now - _price_cache['fetched_at']) < CACHE_SECONDS:
        return _price_cache['data']

    try:
        import requests
        resp = requests.get(
            'https://www.goodreturns.in/petrol-price.html',
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=5
        )
        text = resp.text

        # Parse petrol price
        import re
        petrol_match = re.search(r'₹\s*([\d.]+).*?petrol', text[:3000], re.IGNORECASE)
        petrol = float(petrol_match.group(1)) if petrol_match else FALLBACK_PRICES['petrol_per_litre']

        diesel_match = re.search(r'₹\s*([\d.]+).*?diesel', text[:3000], re.IGNORECASE)
        diesel = float(diesel_match.group(1)) if diesel_match else FALLBACK_PRICES['diesel_per_litre']

        data = {
            'petrol_per_litre':    petrol,
            'diesel_per_litre':    diesel,
            'crude_per_barrel':    110.96,  # hardcoded — crude needs paid API
            'electricity_per_kwh': 7.0,
            'source': 'live',
            'as_of': 'today'
        }
        _price_cache = {'data': data, 'fetched_at': now}
        return data

    except:
        return FALLBACK_PRICES


def get_contract_comparison(contract, user_state='Other'):
    """
    Compare vendor contract price against real market rates.
    Returns dict with comparison info.
    """
    prices = get_market_prices()
    energy_type = contract.get('energy_type', '')
    price_grc = contract.get('price_grc', 0)
    quantity = contract.get('quantity', 1)
    price_inr = contract.get('price_inr', 0)

    market_price = None
    unit = ''
    market_label = ''

    if energy_type == 'petrol':
        market_price = prices['petrol_per_litre'] * quantity
        unit = '₹/litre'
        market_label = f"₹{prices['petrol_per_litre']}/litre (live)"
    elif energy_type == 'diesel':
        market_price = prices['diesel_per_litre'] * quantity
        unit = '₹/litre'
        market_label = f"₹{prices['diesel_per_litre']}/litre (live)"
    elif energy_type == 'kwh_block':
        state_rate = STATE_ELECTRICITY_RATES.get(user_state, 7.0)
        market_price = state_rate * quantity
        unit = '₹/kWh'
        market_label = f"₹{state_rate}/kWh ({user_state} grid rate)"

    if market_price:
        diff_pct = round(((price_inr - market_price) / market_price) * 100, 1)
        if diff_pct > 10:
            verdict = 'expensive'
        elif diff_pct < -10:
            verdict = 'cheap'
        else:
            verdict = 'fair'
    else:
        diff_pct = None
        verdict = 'unknown'
        market_label = 'No reference available'

    return {
        'market_price':  round(market_price, 2) if market_price else None,
        'market_label':  market_label,
        'vendor_inr':    price_inr,
        'diff_pct':      diff_pct,
        'verdict':       verdict,
        'prices_source': prices.get('source', 'fallback')
    }