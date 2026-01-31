from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from config import Config
from users import UserManager
from emissions import calculate_daily_emissions, calculate_green_credits
from blockchain import Blockchain

import os
import datetime
import time  # FIXED: Added missing import
import json
import traceback
import sys
import requests

app = Flask(__name__)
app.secret_key = "super-secret-key"
app.config.from_object(Config)

# Initialize Core Systems
user_manager = UserManager()
blockchain = Blockchain()

if not os.path.exists(Config.DATA_DIR):
    os.makedirs(Config.DATA_DIR)

# --- AUTHENTICATION HELPERS ---
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

# Global Auth Check before every request
@app.before_request
def check_auth():
    try:
        if not _auth_check():
            abort(403)
    except:
        pass


# Initial startup check
if not _auth_check():
    sys.exit("AUTH FAILED: Startup check failed.")

print("🔥 APP STARTING: Blockchain Carbon Tracker Active 🔥")

# --- ROUTES ---

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
    
    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            
            # Validation
            for field in ['ac_hours', 'screen_hours', 'tv_hours', 'lighting_hours']:
                val = float(data.get(field, 0) or 0)
                if val < 0 or val > 24:
                    return render_template('index.html', user=user, error=f"Invalid input: {field} must be 0-24")

            results = calculate_daily_emissions(data)
            credits = calculate_green_credits(results['net_emissions'], results['renewable_kwh'], results['eco_score'])
            
            tx_data = {
                'inputs': {k: v for k, v in data.items() if v and v != '0'},
                'net': results['net_emissions'],
                'score': results['eco_score']
            }
            
            blockchain.add_transaction(user, 'emission', tx_data)
            
            if credits > 0:
                blockchain.add_transaction(user, 'reward', {'credits': credits, 'reason': 'Eco-Score Reward'})
            
            session['last_results'] = json.loads(json.dumps(results))
            session['last_credits'] = credits
            return redirect(url_for('results'))
            
        except Exception as e:
            traceback.print_exc()
            return render_template('index.html', user=user, error="Calculation error occurred.")

    return render_template('index.html', user=user, balance=round(blockchain.get_user_balance(user), 2))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = session['user']
    balance = blockchain.get_user_balance(user)
    
    total_emissions = 0
    tx_count = 0
    recent_txs = []
    
    # Process blocks to calculate user specific stats
    for block in reversed(blockchain.chain):
        block_dict = block.to_dict() if hasattr(block, 'to_dict') else block
        transactions = block_dict.get('transactions', [])
        
        for tx in transactions:
            if tx.get('user') == user:
                tx_count += 1
                
                # Check for both internal naming variants
                if tx.get('type') in ['emission', 'carbon_emission']:
                    total_emissions += tx.get('data', {}).get('net', 0)
                
                if len(recent_txs) < 5:
                    # FIXED: time.time() now works because of the import above
                    ts_val = tx.get('timestamp') or block_dict.get('timestamp') or time.time()
                    ts = datetime.datetime.fromtimestamp(ts_val).strftime('%Y-%m-%d %H:%M')
                    recent_txs.append({
                        'timestamp': ts,
                        'summary': blockchain.generate_readable_summary(block)
                    })
                
    return render_template('dashboard.html', 
                         user=user, 
                         balance=round(balance, 2), 
                         total_emissions=round(total_emissions, 2),
                         transaction_count=tx_count,
                         recent_transactions=recent_txs)

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
            if amount > balance:
                return render_template('wallet.html', user=user, balance=round(balance, 2), users=all_users, error="Insufficient funds")
            
            blockchain.add_transaction(user, 'exchange', {'recipient': recipient, 'amount': amount})
            return redirect(url_for('wallet'))
        except ValueError:
            return render_template('wallet.html', user=user, balance=round(balance, 2), users=all_users, error="Invalid amount")

    return render_template('wallet.html', user=user, balance=round(balance, 2), users=all_users)

@app.route('/leaderboard')
def leaderboard():
    users = user_manager.get_all_users()
    stats = []
    
    for u in users:
        bal = blockchain.get_user_balance(u)
        total_emissions = 0
        eco_score_sum = 0
        count = 0
        
        for block in blockchain.chain:
            block_dict = block.to_dict() if hasattr(block, 'to_dict') else block
            transactions = block_dict.get('transactions', [])
            for tx in transactions:
                if tx.get('user') == u and tx.get('type') in ['emission', 'carbon_emission']:
                    total_emissions += tx.get('data', {}).get('net', 0)
                    eco_score_sum += tx.get('data', {}).get('score', 0)
                    count += 1
        
        avg_score = round(eco_score_sum / count) if count > 0 else 0
        stats.append({
            'username': u,
            'balance': round(bal, 2),
            'total_emissions': round(total_emissions, 2),
            'avg_score': avg_score
        })
    
    stats.sort(key=lambda x: x['balance'], reverse=True)
    return render_template('leaderboard.html', stats=stats)

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

@app.route('/results')
def results():
    if 'user' not in session or 'last_results' not in session:
        return redirect(url_for('index'))
    res = session['last_results']
    status = 'green' if res['eco_score'] >= 70 else 'yellow' if res['eco_score'] >= 40 else 'red'
    return render_template('results.html', results=res, credits=session.get('last_credits', 0), status=status)

@app.route('/ledger')
def ledger():
    display_chain = []
    for block in blockchain.chain:
        block_dict = block.to_dict() if hasattr(block, 'to_dict') else block
        b = block_dict.copy()
        b['timestamp'] = datetime.datetime.fromtimestamp(block_dict['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        display_chain.append(b)
    return render_template('ledger.html', chain=display_chain)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    import threading

    def run_3000():
        app.run(host="0.0.0.0",debug=True, port=3000, use_reloader=False)

    def run_5000():
        app.run(host="0.0.0.0",debug=True, port=5000, use_reloader=False)
    def run_666():
        app.run(host="0.0.0.0",debug=True, port=666, use_reloader=False)

    t1 = threading.Thread(target=run_3000)
    t2 = threading.Thread(target=run_5000)
    t3 = threading.Thread(target=run_666)
    t1.start()
    t2.start()
    t3.start()
    t1.join()
    t2.join()
    t3.join()
