from flask import Flask, render_template, request
from blockchain import EnergyChain
import time
import os

app = Flask(__name__)
bc = EnergyChain()

# -------------------------
# Carbon calculation functions
# -------------------------
def calculate_gross_co2(data):
    """
    Calculates CO2 from 7 user activity factors
    """
    co2 = 0
    # Transport
    co2 += data["distance_km"] * 0.21  # per km, approximate for Bangalore

    # Screen and electricity usage
    co2 += data["screen_hours"] * 0.02
    co2 += data["ac_hours"] * 1.5
    co2 += data["light_hours"] * 0.06
    co2 += data["tv_hours"] * 0.1

    # Meals
    co2 += data["home_meals"] * 0.5    # kg CO2 per home-cooked meal
    co2 += data["resto_meals"] * 2.5   # kg CO2 per restaurant meal (includes energy & transport)

    # Water
    co2 += data["water_liters"] * 0.0003  # only processed water counts

    return round(co2, 2)


def calculate_renewable_offset(renew):
    """
    Calculates CO2 offset from renewable capacity
    """
    total_kwh = 0

    if renew["solar_used"]:
        total_kwh += renew["solar_kw"] * 5  # avg sunlight hours/day

    if renew["wind_used"]:
        total_kwh += renew["wind_kw"] * 8  # avg wind operation

    if renew["biogas_used"]:
        total_kwh += renew["biogas_kwh"]

    offset = total_kwh * 0.82  # 1 kWh ≈ 0.82 kg CO2
    return round(offset, 2), round(total_kwh, 2)


# -------------------------
# Human-readable ledger
# -------------------------
def write_audit_ledger(user, activity, renew, gross, offset, net):
    with open("activity_ledger.txt", "a") as f:
        f.write("\n" + "-"*50 + "\n")
        f.write(f"Time       : {time.ctime()}\n")
        f.write(f"User       : {user}\n")
        f.write(f"Travel     : {activity['distance_km']} km ({activity['transport']})\n")
        f.write(f"AC Hours   : {activity['ac_hours']}\n")
        f.write(f"Screen     : {activity['screen_hours']}\n")
        f.write(f"Meals      : Home={activity['home_meals']} Resto={activity['resto_meals']}\n")
        f.write(f"Water      : {activity['water_liters']} L\n")

        f.write("\n--- Renewable ---\n")
        f.write(f"Solar Used : {renew['solar_used']} ({renew['solar_kw']} kW)\n")
        f.write(f"Wind Used  : {renew['wind_used']} ({renew['wind_kw']} kW)\n")
        f.write(f"Biogas Used: {renew['biogas_used']} ({renew['biogas_kwh']} kWh)\n")

        f.write("\n--- Result ---\n")
        f.write(f"Gross CO2  : {gross} kg\n")
        f.write(f"Offset     : {offset} kg\n")
        f.write(f"Net CO2    : {net} kg\n")
        f.write("-"*50 + "\n")


# -------------------------
# Routes
# -------------------------
@app.route("/")
def home():
    return render_template("index.html", title="Carbon Tracker")


@app.route("/submit", methods=["POST"])
def submit():
    data = request.form

    # User activity
    activity_data = {
        "distance_km": float(data.get("distance_km", 0)),
        "transport": data.get("transport"),
        "screen_hours": float(data.get("screen_hours", 0)),
        "ac_hours": float(data.get("ac_hours", 0)),
        "light_hours": float(data.get("light_hours", 0)),
        "tv_hours": float(data.get("tv_hours", 0)),
        "home_meals": float(data.get("home_meals", 0)),
        "resto_meals": float(data.get("resto_meals", 0)),
        "water_liters": float(data.get("processed_water_liters", 0))  # fixed
    }

    # Renewable info
    renew_data = {
        "solar_used": data.get("solar_used") == "yes",
        "wind_used": data.get("wind_used") == "yes",
        "biogas_used": data.get("biogas_used") == "yes",
        "solar_kw": float(data.get("solar_kw") or 0),   # safe fix
        "wind_kw": float(data.get("wind_kw") or 0),     # safe fix
        "biogas_kwh": float(data.get("biogas_kwh") or 0) # safe fix
    }

    gross = calculate_gross_co2(activity_data)
    offset, kwh = calculate_renewable_offset(renew_data)
    net = max(gross - offset, 0)

    # Write ledger
    write_audit_ledger(data.get("user_id", "U1"), activity_data, renew_data, gross, offset, net)

    # Update blockchain
    bc.buy_energy(data.get("user_id", "U1"), net, kwh)

    return render_template("result.html", gross=gross, offset=offset, net=net)


# -------------------------
# Test route
# -------------------------
@app.route("/test", methods=["GET"])
def test_run():
    # Sample dummy data
    activity_data = {
        "distance_km": 10,
        "transport": "car",
        "screen_hours": 3,
        "ac_hours": 2,
        "light_hours": 5,
        "tv_hours": 2,
        "home_meals": 2,
        "resto_meals": 1,
        "processed_water_liters": 5
    }

    renew_data = {
        "solar_used": True,
        "wind_used": False,
        "biogas_used": True,
        "solar_kw": 2.0,
        "wind_kw": 0,
        "biogas_kwh": 3.0
    }

    gross = calculate_gross_co2(activity_data)
    offset, kwh = calculate_renewable_offset(renew_data)
    net = max(gross - offset, 0)

    # Write ledger (optional for test)
    write_audit_ledger("TestUser", activity_data, renew_data, gross, offset, net)

    # Blockchain update
    bc.buy_energy("TestUser", net, kwh)

    return {
        "gross_co2": gross,
        "renewable_offset": offset,
        "net_co2": net,
        "ledger_file": "activity_ledger.txt",
        "blockchain_length": len(bc.chain)
    }


# -------------------------
# Run app
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
