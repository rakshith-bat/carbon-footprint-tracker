from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from config import Config
from users import UserManager
from emissions import calculate_daily_emissions, calculate_green_credits
from analyst.engine import (
    save_entry, can_submit_today, build_analyst_report,
    get_user_entries, get_monthly_usage, get_personal_average
)
from analyst.narrator import generate_narrative
from analyst.scorer import vs_national, vs_state, get_best_day, get_worst_day, get_category_breakdown_avg
from algo.rewards import send_green_credits, get_user_token_balance
from algo.ledger import record_emission_on_chain
from algo.rewards import send_green_credits, get_user_token_balance, fund_new_wallet
from algo.rewards import send_green_credits, get_user_token_balance, fund_new_wallet, transfer_credits
from algo.marketplace import post_contract, get_open_contracts, get_vendor_contracts, delete_contract

import os
import datetime
import json
import traceback
import sys
import requests

app = Flask(__name__)
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app.secret_key = "super-secret-key"
app.config.from_object(Config)

# Initialize Core Systems
user_manager = UserManager()

if not os.path.exists(Config.DATA_DIR):
    os.makedirs(Config.DATA_DIR)

# --- AUTHENTICATION HELPERS --- (unchanged)
def _load_local_key():
    try:
        with open("core/auth_key.txt", "r") as f:
            return f.read().strip()
    except:
        return None

def _check_remote_key():
    url = "https://raw.githubusercontent.com/rakshith-bat/authenticator/main/auth_key.txt"
    try:
        return requests.get(url, timeout=4).text.strip()
    except:
        return None

def _auth_check():
    local = _load_local_key()
    remote = _check_remote_key()
    if not local or not remote:
        return False
    return local == remote

@app.before_request
def check_auth():
    try:
        if not _auth_check():
            abort(403)
    except:
        pass

if not _auth_check():
    sys.exit("AUTH FAILED: Startup check failed.")

print(" APP STARTING: Carbon Tracker + Algorand + Analyst Active ")

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def root():
    if 'user' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))


@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = session['user']
    user_data = user_manager.get_user(user)
    if not user_data:
        return redirect(url_for('login'))
    if user_data.get('user_type') == 'vendor':
        return redirect(url_for('vendor'))
    user_state = user_data.get('city', 'Other')
    today = datetime.date.today().isoformat()

    # Check daily entry lock
    can_submit, existing_entry = can_submit_today(user)

    if request.method == 'POST':
        action = request.form.get('action', 'submit')

        # Block second submission unless it's an edit
        if not can_submit and action != 'edit':
            return render_template('index.html',
                user=user,
                locked=True,
                existing=existing_entry,
                balance=get_user_token_balance(user_data.get('algo_address', '')),
                error="You've already logged today. Use Edit to update.")

        try:
            data = request.form.to_dict()
            results = calculate_daily_emissions(data, user_state=user_state)
            credits = calculate_green_credits(
                results['net_emissions'],
                results['renewable_kwh'],
                results['eco_score']
            )

            # Save to entries.json (local fast store)
            entry_record = {
                **results,
                'credits_earned': credits,
                'timestamp': today,
                'inputs': {k: v for k, v in data.items() if v and v != '0'}
            }
            save_entry(user, today, entry_record)

            # Update streak
            personal_avg = get_personal_average(user)
            below_avg = personal_avg is None or results['net_emissions'] <= personal_avg
            streak = user_manager.update_streak(user, today, below_avg)

            # Streak bonus
            if streak > 0 and streak % Config.STREAK_BONUS_THRESHOLD == 0:
                credits += Config.STREAK_BONUS_CREDITS

            # Send real Algorand tokens (non-blocking — don't crash if network slow)
            algo_address = user_data.get('algo_address')
            if algo_address and credits > 0:
                try:
                    send_green_credits(algo_address, credits)
                except Exception as e:
                    print(f"Algo reward failed (non-critical): {e}")

            # Record emission on-chain as note
            try:
                record_emission_on_chain(user, results['net_emissions'], results['eco_score'])
            except Exception as e:
                print(f"Algo ledger write failed (non-critical): {e}")

            session['last_results'] = json.loads(json.dumps(results))
            session['last_credits'] = credits
            return redirect(url_for('results'))

        except Exception as e:
            traceback.print_exc()
            return render_template('index.html', user=user, error="Calculation error occurred.")

    # GET — show form
    algo_address = user_data.get('algo_address', '')
    balance = get_user_token_balance(algo_address) if algo_address else 0

    return render_template('index.html',
        user=user,
        locked=not can_submit,
        existing=existing_entry,
        balance=round(balance, 2),
        streak=user_data.get('streak', 0),
        user_state=user_state
    )


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = session['user']
    user_data = user_manager.get_user(user)
    algo_address = user_data.get('algo_address', '')

    balance = get_user_token_balance(algo_address) if algo_address else 0
    monthly_used = get_monthly_usage(user)
    monthly_goal = user_data.get('monthly_goal', 300)
    personal_avg = get_personal_average(user)

    entries = get_user_entries(user)
    recent = list(reversed(list(entries.items())))[:5]
    recent_txs = [
        {'timestamp': d, 'net': e.get('net_emissions', 0), 'score': e.get('eco_score', 0)}
        for d, e in recent
    ]

    return render_template('dashboard.html',
        user=user,
        balance=round(balance, 2),
        monthly_used=round(monthly_used, 2),
        monthly_goal=monthly_goal,
        personal_avg=personal_avg,
        total_entries=len(entries),
        recent_transactions=recent_txs,
        streak=user_data.get('streak', 0),
        algo_address=algo_address
    )


@app.route('/analyst')
def analyst():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = session['user']
    user_data = user_manager.get_user(user)
    if not user_data:
        return redirect(url_for('login'))
    if user_data.get('user_type') == 'vendor':
        return redirect(url_for('vendor'))
    user_data = user_manager.get_user(user)
    user_state = user_data.get('city', 'Other')
    monthly_goal = user_data.get('monthly_goal', 300)
    all_users = user_manager.get_all_users()

    # Build full report
    report = build_analyst_report(user, user_state, all_users, monthly_goal)

    # Scorer extras
    report['vs_national'] = vs_national(report['personal_avg'])
    report['vs_state'] = vs_state(report['personal_avg'], user_state)
    report['best_day'], report['best_val'] = get_best_day(user)
    report['worst_day'], report['worst_val'] = get_worst_day(user)
    report['category_avgs'] = get_category_breakdown_avg(user)

    # AI narrative (Claude API or fallback)
    narrative = generate_narrative(report, user_state)

    return render_template('analyst.html',
        user=user,
        report=report,
        narrative=narrative,
        user_state=user_state
    )

@app.route('/wallet')
def wallet():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = session['user']
    user_data = user_manager.get_user(user)
    algo_address = user_data.get('algo_address', '')
    balance = get_user_token_balance(algo_address) if algo_address else 0
    all_users = [u for u in user_manager.get_all_users() if u != user]

    return render_template('wallet.html',
        user=user,
        balance=round(balance, 2),
        algo_address=algo_address,
        all_users=all_users
    )

@app.route('/leaderboard')
def leaderboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    current_user = session['user']
    current_type = user_manager.get_user(current_user).get('user_type', 'consumer')
    all_users = user_manager.get_all_users()

    stats = []
    for u in all_users:
        u_data = user_manager.get_user(u)
        if u_data.get('user_type', 'consumer') != current_type:
            continue

        algo_address = u_data.get('algo_address', '')
        balance = get_user_token_balance(algo_address) if algo_address else 0
        avg = get_personal_average(u)
        monthly = get_monthly_usage(u)

        stats.append({
            'username':     u,
            'balance':      round(balance, 2),
            'avg_daily':    avg or 0,
            'monthly_used': round(monthly, 2),
            'streak':       u_data.get('streak', 0),
            'user_type':    current_type
        })

    stats.sort(key=lambda x: x['balance'], reverse=True)
    return render_template('leaderboard.html',
        stats=stats,
        user_type=current_type
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        action = request.form.get('action')
        city = request.form.get('city', 'Other')
        monthly_goal = float(request.form.get('monthly_goal', 300) or 300)
        user_type = request.form.get('user_type', 'consumer')

        if action == 'register':
            success, msg = user_manager.register(username, password, city=city, monthly_goal=monthly_goal, user_type=user_type)
            if success:
                u_data = user_manager.get_user(username)
                algo_address = u_data.get('algo_address', '')
                try:
                    fund_new_wallet(algo_address)      # 0.5 ALGO first
                    send_green_credits(algo_address, 10.0)   # then welcome tokens
                except Exception as e:
                    print(f"Welcome bonus failed (non-critical): {e}")
                return render_template('login.html', message="Registered! Please login.")
            return render_template('login.html', error=msg)

        elif action == 'login':
            if user_manager.login(username, password):
                session['user'] = username
                u_data = user_manager.get_user(username)
                session['user_type'] = u_data.get('user_type', 'consumer')
                if u_data.get('user_type') == 'vendor':
                    return redirect(url_for('vendor'))
                return redirect(url_for('index'))
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')


@app.route('/results')
def results():
    if 'user' not in session or 'last_results' not in session:
        return redirect(url_for('index'))
    res = session['last_results']
    status = 'green' if res['eco_score'] >= 70 else 'yellow' if res['eco_score'] >= 40 else 'red'
    return render_template('results.html',
        results=res,
        credits=session.get('last_credits', 0),
        status=status
    )


@app.route('/ledger')
def ledger():
    user = session.get('user', 'anonymous')
    entries = get_user_entries(user)
    display = [
        {'date': d, 'net': e.get('net_emissions'), 'score': e.get('eco_score'), 'credits': e.get('credits_earned')}
        for d, e in reversed(list(entries.items()))
    ]
    return render_template('ledger.html', entries=display)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
@app.route('/transfer', methods=['POST'])
def transfer():
    if 'user' not in session:
        return redirect(url_for('login'))

    sender = session['user']
    recipient = request.form.get('recipient')
    try:
        amount = float(request.form.get('amount'))
    except:
        return redirect(url_for('wallet'))

    sender_data = user_manager.get_user(sender)
    recipient_data = user_manager.get_user(recipient)

    if not recipient_data:
        return redirect(url_for('wallet'))

    sender_address = sender_data.get('algo_address')
    sender_key = user_manager.get_algo_private_key(sender)
    recipient_address = recipient_data.get('algo_address')

    sender_balance = get_user_token_balance(sender_address)
    if amount > sender_balance:
        return redirect(url_for('wallet'))

    try:
        transfer_credits(sender_address, sender_key, recipient_address, amount)
    except Exception as e:
        print(f"Transfer failed: {e}")

    return redirect(url_for('wallet'))
@app.route('/vendor', methods=['GET', 'POST'])
def vendor():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = session['user']
    user_data = user_manager.get_user(user)

    if user_data.get('user_type') != 'vendor':
        return redirect(url_for('dashboard'))

    algo_address = user_data.get('algo_address', '')
    balance = get_user_token_balance(algo_address) if algo_address else 0

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'post_contract':
            post_contract(
                vendor_username=user,
                energy_type=request.form.get('energy_type'),
                quantity=float(request.form.get('quantity', 0)),
                price_grc=float(request.form.get('price_grc', 0)),
                duration_months=int(request.form.get('duration_months', 1)),
                description=request.form.get('description', '')
            )

        elif action == 'delete_contract':
            delete_contract(request.form.get('contract_id'), user)

        return redirect(url_for('vendor'))

    my_contracts = get_vendor_contracts(user)

    return render_template('vendor.html',
        user=user,
        balance=round(balance, 2),
        algo_address=algo_address,
        my_contracts=my_contracts
    )


@app.route('/marketplace')
def marketplace():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = session['user']
    user_data = user_manager.get_user(user)
    algo_address = user_data.get('algo_address', '')
    balance = get_user_token_balance(algo_address) if algo_address else 0
    from algo.marketplace import get_open_contracts, get_contract_comparison
    contracts = get_open_contracts()
    user_state = user_data.get('city', 'Other')

# Add price comparison to each contract
    for c in contracts:
        c['comparison'] = get_contract_comparison(c, user_state)

    # Groq AI insight
    narrative = ""
    if contracts:
        try:
            import requests as req, os
            prompt = f"""You are an energy market analyst. A user has {balance} GRC tokens 
and is browsing energy contracts. Here are available contracts:
{json.dumps(contracts, indent=2)}
In 2-3 sentences, recommend which contract suits them best and why. Be specific, use numbers."""
            resp = req.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY','')}",
                         "Content-Type": "application/json"},
                json={"model": "llama-3.1-8b-instant",
                      "messages": [{"role": "user", "content": prompt}],
                      "max_tokens": 150},
                timeout=8
            )
            narrative = resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            narrative = "AI insight unavailable. Compare contracts manually."

    return render_template('marketplace.html',
        user=user,
        balance=round(balance, 2),
        contracts=contracts,
        narrative=narrative
    )


@app.route('/buy_contract/<contract_id>', methods=['POST'])
def buy_contract(contract_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    user = session['user']
    from algo.marketplace import load_contracts
    contracts = load_contracts()
    contract = contracts.get(contract_id)

    if not contract or contract['status'] != 'open':
        return redirect(url_for('marketplace'))

    if contract['vendor'] == user:
        return redirect(url_for('marketplace'))

    buyer_data = user_manager.get_user(user)
    vendor_data = user_manager.get_user(contract['vendor'])

    buyer_address = buyer_data.get('algo_address')
    buyer_key = user_manager.get_algo_private_key(user)
    vendor_address = vendor_data.get('algo_address')

    balance = get_user_token_balance(buyer_address)
    if balance < contract['price_grc']:
        return redirect(url_for('marketplace'))

    try:
        transfer_credits(buyer_address, buyer_key, vendor_address, contract['price_grc'])
        close_contract(contract_id)
    except Exception as e:
        print(f"Contract purchase failed: {e}")

    return redirect(url_for('marketplace'))

if __name__ == '__main__':
    import threading

    def run_3000():
        app.run(host="0.0.0.0", debug=True, port=3000, use_reloader=False)

    def run_5000():
        app.run(host="0.0.0.0", debug=True, port=5000, use_reloader=False)

    def run_666():
        app.run(host="0.0.0.0", debug=True, port=666, use_reloader=False)

    t1 = threading.Thread(target=run_3000)
    t2 = threading.Thread(target=run_5000)
    t3 = threading.Thread(target=run_666)
    t1.start()
    t2.start()
    t3.start()
    t1.join()
    t2.join()
    t3.join()