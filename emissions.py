# ─────────────────────────────────────────────
# EMISSION FACTORS — sourced from CEA 2023,
# MoRTH, and IPCC AR6 where applicable
# ─────────────────────────────────────────────

# India state grid emission factors (kg CO2 per kWh)
# Source: CEA CO2 Baseline Database 2023
STATE_GRID_FACTORS = {
    'Tamil Nadu':    0.82,
    'Karnataka':     0.74,
    'Maharashtra':   0.89,
    'Delhi':         0.95,
    'Gujarat':       0.91,
    'Rajasthan':     0.88,
    'Uttar Pradesh': 0.92,
    'West Bengal':   0.93,
    'Telangana':     0.90,
    'Kerala':        0.45,
    'Punjab':        0.86,
    'Haryana':       0.91,
    'Other':         0.82
}

# Average electricity tariff per state (₹/kWh) — approximate
STATE_TARIFFS = {
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

# Transport emission factors (kg CO2 per km)
# Source: MoRTH + IPCC
TRANSPORT_FACTORS = {
    # Own vehicle
    'petrol_car':   0.21,
    'diesel_car':   0.19,
    'cng_car':      0.14,
    'petrol_bike':  0.09,
    'diesel_bike':  0.08,
    'ev_car':       0.04,
    'ev_bike':      0.02,
    # Public / shared
    'metro':        0.03,
    'ac_bus':       0.06,
    'nonac_bus':    0.04,
    'auto':         0.08,
    'local_train':  0.02,
    'cab':          0.18,
}

FOOD_FACTORS = {
    'restaurant': 2.5,
    'home':       0.8
}

WASTE_FACTORS = {
    'recycled':  0.1,
    'landfill':  0.5
}

# Occasional events — spread across month, excluded from daily anomaly detection
OCCASIONAL_FACTORS = {
    'flight_domestic':      90.0,   # per flight
    'flight_international': 400.0,
    'shopping_clothing':    7.0,    # per item
    'shopping_electronics': 50.0,
    'shopping_general':     3.0
}

INDIA_STATE_BASELINES = {
    'Tamil Nadu':    8.2,
    'Karnataka':     7.9,
    'Maharashtra':   9.1,
    'Delhi':         11.4,
    'Gujarat':       10.8,
    'Rajasthan':     7.1,
    'Uttar Pradesh': 6.8,
    'West Bengal':   8.5,
    'Telangana':     9.3,
    'Kerala':        7.4,
    'Punjab':        8.8,
    'Haryana':       9.0,
    'Other':         8.5
}

INDIA_NATIONAL_AVERAGE = 8.5


def safe_float(value, default=0.0):
    if not value:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def validate_hours(value):
    val = safe_float(value)
    return max(0.0, min(24.0, val))


def calculate_daily_emissions(data, user_state='Other'):
    """
    Calculate daily emissions. Occasional events (flights, shopping)
    are returned separately and never mixed into the daily score.
    """
    total = 0.0
    breakdown = {}

    # ── Electricity (bill-based) ──────────────────────────
    monthly_bill = safe_float(data.get('monthly_bill'))
    tariff = STATE_TARIFFS.get(user_state, 7.0)
    grid_factor = STATE_GRID_FACTORS.get(user_state, 0.82)

    if monthly_bill > 0:
        monthly_kwh = monthly_bill / tariff
        daily_kwh = monthly_kwh / 30
        electricity_emission = daily_kwh * grid_factor
    else:
        electricity_emission = 0.0

    total += electricity_emission
    breakdown['electricity'] = round(electricity_emission, 2)

    # ── Transport ─────────────────────────────────────────
    transport_type = data.get('transport_type', '')
    distance = safe_float(data.get('distance'))
    t_factor = TRANSPORT_FACTORS.get(transport_type, 0.08)
    transport_emission = distance * t_factor
    total += transport_emission
    breakdown['transport'] = round(transport_emission, 2)

    # ── Food ──────────────────────────────────────────────
    home_meals = safe_float(data.get('home_meals'))
    restaurant_meals = safe_float(data.get('restaurant_meals'))
    food_emission = (home_meals * FOOD_FACTORS['home']) + \
                    (restaurant_meals * FOOD_FACTORS['restaurant'])
    total += food_emission
    breakdown['food'] = round(food_emission, 2)

    # ── Waste (optional) ──────────────────────────────────
    waste_recycled = safe_float(data.get('waste_recycled_kg'))
    waste_landfill = safe_float(data.get('waste_landfill_kg'))
    waste_emission = (waste_recycled * WASTE_FACTORS['recycled']) + \
                     (waste_landfill * WASTE_FACTORS['landfill'])
    total += waste_emission
    breakdown['waste'] = round(waste_emission, 2)

    # ── Renewables offset ─────────────────────────────────
    solar_kwh = safe_float(data.get('solar_kwh')) if data.get('has_solar') == 'yes' else 0.0
    wind_kwh = safe_float(data.get('wind_kwh')) if data.get('has_wind') == 'yes' else 0.0
    total_renewable_kwh = solar_kwh + wind_kwh
    offset = total_renewable_kwh * grid_factor

    net = max(0.0, total - offset)
    score = max(0, min(100, int(100 - (net / 15.0 * 100))))

    # ── Occasional events (flights, shopping) ─────────────
    # Stored separately, NOT added to net, NOT used in score
    occasional = {}
    flight_type = data.get('flight_type', '')
    flights = safe_float(data.get('flights_taken', 0))
    if flight_type and flights > 0:
        key = f'flight_{flight_type}'
        occasional['flights'] = round(
            flights * OCCASIONAL_FACTORS.get(key, 0), 2
        )

    shopping_type = data.get('shopping_type', '')
    shopping_items = safe_float(data.get('shopping_items', 0))
    if shopping_type and shopping_items > 0:
        key = f'shopping_{shopping_type}'
        occasional['shopping'] = round(
            shopping_items * OCCASIONAL_FACTORS.get(key, 3.0), 2
        )

    return {
        'gross_emissions':  round(total, 2),
        'renewable_offset': round(offset, 2),
        'net_emissions':    round(net, 2),
        'renewable_kwh':    round(total_renewable_kwh, 2),
        'eco_score':        score,
        'breakdown':        breakdown,
        'occasional':       occasional   # flights/shopping, separate
    }


def calculate_green_credits(net_emissions, renewable_kwh, eco_score):
    credits = 0.0
    if eco_score > 50:
        credits += (eco_score - 50) * 0.5
    credits += renewable_kwh * 0.2
    return round(credits, 2)


def get_state_baseline(state):
    return INDIA_STATE_BASELINES.get(state, INDIA_NATIONAL_AVERAGE)