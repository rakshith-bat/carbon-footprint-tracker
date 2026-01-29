from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from config import Config
from users import UserManager
from emissions import calculate_daily_emissions, calculate_green_credits
from blockchain import Blockchain

import os
import datetime
import json
import traceback
import sys
import requests
import time
from threading import Thread
from werkzeug.serving import make_server

# --- Auth Utilities ---
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

if not _auth_check():
    print("Startup check failed. Exiting.")
    sys.exit("AUTH FAILED")

# --- Flask Setup ---
app = Flask(__name__)
app.secret_key = "super-secret-key"
app.config.from_object(Config)

@app.before_request
def check_auth_before_request():
    if not _auth_check():
        abort(403)

# --- Core Instances ---
user_manager = UserManager()
blockchain = Blockchain()

if not os.path.exists(Config.DATA_DIR):
    os.makedirs(Config.DATA_DIR)

print(" USING REAL blockchain INSTANCE ")

# --- Routes ---
@app.route('/')
def root():
    return redirect(url_for('index')) if 'user' in session else redirect(url_for('login'))

@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = session['user']
    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            # Validate hours
            for field in ['ac_hours', 'screen_hours', 'tv_hours', 'lighting_hours']:
                val = float(data.get(field, 0) or 0)
                if val < 0 or val > 24:
                    return render_template('index.html', user=user, error=f"{field} must be 0-24")
            
            results = calculate_daily_emissions(data)
            # normalize net key for template
            results['net'] = results['net_emissions']

            credits = calculate_green_credits(results['net_emissions'], results['renewable_kwh'], results['eco_score'])
            
            tx_data = {
                'inputs': {k: v for k, v in data.items() if v and v != '0'},
                'breakdown': results['breakdown'],
                'gross': results['gross_emissions'],
                'offset': results['renewable_offset'],
                'net': results['net_emissions'],
                'score': results['eco_score']
            }
            
            # Add emission tx
            blockchain.add_transaction(user, 'emission', tx_data)
            
            # Add credits tx
            if credits > 0:
                blockchain.add_transaction(user, 'reward', {'credits': credits, 'reason': 'Eco-Score Reward'})
                
            session['last_results'] = json.loads(json.dumps(results))
            session['last_credits'] = credits
            
            return redirect(url_for('results'))
        except Exception as e:
            print(f"Error processing submission: {e}")
            traceback.print_exc()
            return render_template('index.html', user=user, error="Error processing data.")
    
    return render_template('index.html', user=user, balance=blockchain.get_user_balance(user))

@app.route('/results')
def results():
    if 'user' not in session or 'last_results' not in session:
        return redirect(url_for('index'))
    results = session['last_results']
    credits = session.get('last_credits', 0)
    status = 'green' if results['eco_score'] >= 70 else 'yellow' if results['eco_score'] >= 40 else 'red'
    return render_template('result.html', results=results, credits=credits, status=status)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = session['user']
    balance = blockchain.get_user_balance(user)
    
    total_emissions = 0
    tx_count = 0
    recent_txs = []
    
    for block in reversed(blockchain.chain):
        block_dict = block.to_dict() if hasattr(block, 'to_dict') else block
        for tx in block_dict.get("user_transactions", []):
            if tx["user_id"] == user:
                tx_count += 1
                if tx["transaction_type"] == "carbon_emission":
                    total_emissions += tx["data"].get("net", 0)

                if len(recent_txs) < 5:
                    ts = datetime.datetime.fromtimestamp(block_dict['timestamp']).strftime('%Y-%m-%d %H:%M')
                    recent_txs.append({'timestamp': ts, 'summary': block_dict.get('readable_summary', 'Transaction')})
    
    return render_template('dashboard.html',
                           user=user,
                           balance=balance,
                           total_emissions=round(total_emissions, 2),
                           transaction_count=tx_count,
                           recent_transactions=recent_txs)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        action = request.form.get('action')
        if action == 'register':
            success, msg = user_manager.register(username, password)
            if success:
                blockchain.add_transaction(username, 'reward', {'credits': 10, 'reason': 'Welcome Bonus'})
                return render_template('login.html', message="Registered! Please login.")
            return render_template('login.html', error=msg)
        elif action == 'login':
            if user_manager.login(username, password):
                session['user'] = username
                return redirect(url_for('index'))
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('last_results', None)
    session.pop('last_credits', None)
    return redirect(url_for('login'))

@app.route('/wallet', methods=['GET', 'POST'])
def wallet():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = session['user']
    balance = blockchain.get_user_balance(user)
    all_users = [u for u in user_manager.get_all_users() if u != user]
    
    if request.method == 'POST':
        recipient = request.form.get('recipient')
        try:
            amount = float(request.form.get('amount'))
        except ValueError:
            return render_template('wallet.html', user=user, balance=balance, users=all_users, error="Invalid amount")
        if amount > balance:
            return render_template('wallet.html', user=user, balance=balance, users=all_users, error="Insufficient funds")
        blockchain.add_transaction(user, 'exchange', {'recipient': recipient, 'amount': amount})
        return redirect(url_for('wallet'))
    
    return render_template('wallet.html', user=user, balance=balance, users=all_users)

@app.route('/ledger')
def ledger():
    display_chain = []
    for block in blockchain.chain:
        b = block.to_dict()
        b['timestamp'] = datetime.datetime.fromtimestamp(b['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        display_chain.append(b)
    return render_template('ledger.html', chain=display_chain)

@app.route('/leaderboard')
def leaderboard():
    stats = []
    for u in user_manager.get_all_users():
        bal = blockchain.get_user_balance(u)
        total_emissions = 0
        eco_score_avg = 0
        count = 0
        for block in blockchain.chain:
            b = block.to_dict() if hasattr(block, 'to_dict') else block
            for tx in b.get("user_transactions", []):
                if tx["user_id"] == u and tx["transaction_type"] == "carbon_emission":
                    total_emissions += tx["data"].get("net", 0)
                    eco_score_avg += tx["data"].get("score", 0)
                    count += 1

        avg_score = round(eco_score_avg / count) if count else 0
        stats.append({'username': u, 'balance': bal, 'total_emissions': round(total_emissions, 2), 'eco_score': avg_score})
    
    stats.sort(key=lambda x: (x['eco_score'], x['balance']), reverse=True)
    return render_template('leaderboard.html', stats=stats)

# --- Main server ---
def run_server(port):
    server = make_server('0.0.0.0', port, app)
    server.serve_forever()

if __name__ == '__main__':
    Thread(target=run_server, args=(3000,), daemon=True).start()
    Thread(target=run_server, args=(5000,), daemon=True).start()
    print(" App running on ports 3000 and 5000")
    
    while True:
        time.sleep(1)
