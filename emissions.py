# Emission Constants (kg CO2 per unit)
EMISSION_FACTORS = {
    'transport': {
        'car': 0.21,      # per km
        'public': 0.08,   # per km
        'ev': 0.04,       # per km
        'bike': 0.0       # per km
    },
    'electricity': {
        'grid': 0.82      # per kWh
    },
    'food': {
        'restaurant': 2.5, # per meal
        'home': 0.8        # per meal
    },
    'water': {
        'processed': 0.0003 # per liter
    }
}

# Usage Constants (kWh per hour)
USAGE_FACTORS = {
    'ac': 1.5,
    'screen': 0.15,
    'tv': 0.1,
    'lighting': 0.06
}

def safe_float(value, default=0.0):
    """Safely convert string to float, handling empty strings and None"""
    if not value:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def validate_hours(value):
    """Ensure hours are between 0 and 24"""
    val = safe_float(value)
    return max(0.0, min(24.0, val))

def calculate_daily_emissions(data):
    """
    Calculate total daily emissions based on user input data.
    Returns detailed breakdown.
    """
    total_emissions = 0.0
    breakdown = {}
    
    # Transport
    transport_mode = data.get('transport_mode', 'public')
    distance = safe_float(data.get('distance'))
    factor = EMISSION_FACTORS['transport'].get(transport_mode, 0.08)
    transport_emission = distance * factor
    total_emissions += transport_emission
    breakdown['transport'] = round(transport_emission, 2)
    
    # Electricity & Usage (Strict Validation)
    ac_hours = validate_hours(data.get('ac_hours'))
    screen_hours = validate_hours(data.get('screen_hours'))
    tv_hours = validate_hours(data.get('tv_hours'))
    lighting_hours = validate_hours(data.get('lighting_hours'))
    
    total_kwh_usage = (ac_hours * USAGE_FACTORS['ac']) + \
                      (screen_hours * USAGE_FACTORS['screen']) + \
                      (tv_hours * USAGE_FACTORS['tv']) + \
                      (lighting_hours * USAGE_FACTORS['lighting'])
    
    electricity_emission = total_kwh_usage * EMISSION_FACTORS['electricity']['grid']
    total_emissions += electricity_emission
    breakdown['electricity'] = round(electricity_emission, 2)
    
    # Food & Water
    home_meals = safe_float(data.get('home_meals'))
    restaurant_meals = safe_float(data.get('restaurant_meals'))
    water_liters = safe_float(data.get('water_liters'))
    
    food_emission = (home_meals * EMISSION_FACTORS['food']['home']) + \
                    (restaurant_meals * EMISSION_FACTORS['food']['restaurant'])
    water_emission = water_liters * EMISSION_FACTORS['water']['processed']
    
    total_emissions += food_emission + water_emission
    breakdown['food_water'] = round(food_emission + water_emission, 2)
    
    # Renewables Reduction (Direct kWh input)
    # Logic: 1 kWh of renewable energy avoids 1 kWh of grid electricity (0.82 kg CO2)
    solar_kwh = safe_float(data.get('solar_kwh')) if data.get('has_solar') == 'yes' else 0.0
    wind_kwh = safe_float(data.get('wind_kwh')) if data.get('has_wind') == 'yes' else 0.0
    biogas_kwh = safe_float(data.get('biogas_kwh')) if data.get('has_biogas') == 'yes' else 0.0
    
    total_renewable_kwh = solar_kwh + wind_kwh + biogas_kwh
    offset = total_renewable_kwh * EMISSION_FACTORS['electricity']['grid']
    
    # Net emissions
    net_emissions = max(0, total_emissions - offset)
    
    # Eco Score (0-100)
    # Baseline: 20kg is "bad" (0 score), 0kg is "perfect" (100 score)
    # Formula: 100 - (net / 20 * 100). Clamped 0-100.
    # If net is negative (net producer), score > 100? No, clamp at 100.
    # Actually, let's make it a bit more lenient. Average is ~10-15.
    score = max(0, min(100, 100 - (net_emissions / 15.0 * 100)))
    
    return {
        'gross_emissions': round(total_emissions, 2),
        'renewable_offset': round(offset, 2),
        'net_emissions': round(net_emissions, 2),
        'renewable_kwh': round(total_renewable_kwh, 2),
        'eco_score': int(score),
        'breakdown': breakdown
    }

def calculate_green_credits(net_emissions, renewable_kwh, eco_score):
    """
    Convert reductions and renewable generation into Green Credits.
    """
    credits = 0
    
    # Base credits on Eco Score
    if eco_score > 50:
        credits += (eco_score - 50) * 0.5
        
    # Bonus for renewable generation (1 credit per 5 kWh generated)
    credits += renewable_kwh * 0.2
    
    return round(credits, 2)
