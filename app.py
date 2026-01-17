from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from config import Config
from users import UserManager
from blockchain import Blockchain
from emissions import calculate_daily_emissions, calculate_green_credits
import os
import datetime
import json
import traceback

app = Flask(__name__)
app.config.from_object(Config)

# Initialize Systems
user_manager = UserManager()
blockchain = Blockchain()

# Ensure data files exist
if not os.path.exists(Config.DATA_DIR):
    os.makedirs(Config.DATA_DIR)

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
            # Handle Emission Calculation
            data = request.form.to_dict()
            
            # Server-side validation for hours (redundant safety)
            for field in ['ac_hours', 'screen_hours', 'tv_hours', 'lighting_hours']:
                try:
                    val = float(data.get(field, 0) or 0)
                    if val < 0 or val > 24:
                        return render_template('index.html', user=user, error=f"Invalid input: {field} must be 0-24 hours")
                except ValueError:
                    pass

            results = calculate_daily_emissions(data)
            credits = calculate_green_credits(results['net_emissions'], results['renewable_kwh'], results['eco_score'])
            
            # Record to Blockchain
            # Detailed human-readable data
            tx_data = {
                'inputs': {k: v for k, v in data.items() if v and v != '0'},
                'breakdown': results['breakdown'],
                'gross': results['gross_emissions'],
                'offset': results['renewable_offset'],
                'net': results['net_emissions'],
                'score': results['eco_score']
            }
            
            blockchain.add_transaction(user, 'emission', tx_data)
            
            if credits > 0:
                blockchain.add_transaction(user, 'reward', {'credits': credits, 'reason': 'Eco-Score Reward'})
                
            # Store results in session for the results page
            session['last_results'] = results
            session['last_credits'] = credits
            
            return redirect(url_for('results'))
            
        except Exception as e:
            print(f"Error processing submission: {e}")
            traceback.print_exc()
            return render_template('index.html', user=user, error="An error occurred while processing your data. Please check your inputs.")

    return render_template('index.html', user=user, balance=blockchain.get_user_balance(user))

@app.route('/results')
def results():
    if 'user' not in session or 'last_results' not in session:
        return redirect(url_for('index'))
    
    results = session['last_results']
    credits = session.get('last_credits', 0)
    
    # Determine status
    status = 'green' if results['eco_score'] >= 70 else 'yellow' if results['eco_score'] >= 40 else 'red'
    
    return render_template('results.html', results=results, credits=credits, status=status)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = session['user']
    balance = blockchain.get_user_balance(user)
    
    # Calculate stats
    total_emissions = 0
    tx_count = 0
    recent_txs = []
    
    for block in reversed(blockchain.chain):
        if block['user_id'] == user:
            tx_count += 1
            if block['transaction_type'] == 'emission':
                total_emissions += block['data'].get('net', 0) # Updated key
            
            # Add to recent (limit 5)
            if len(recent_txs) < 5:
                ts = datetime.datetime.fromtimestamp(block['timestamp']).strftime('%Y-%m-%d %H:%M')
                recent_txs.append({
                    'timestamp': ts,
                    'summary': block['readable_summary']
                })
                
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
            else:
                return render_template('login.html', error=msg)
        
        elif action == 'login':
            if user_manager.login(username, password):
                session['user'] = username
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('last_results', None)
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
    chain_data = blockchain.chain
    display_chain = []
    for block in chain_data:
        b = block.copy()
        b['timestamp'] = datetime.datetime.fromtimestamp(block['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        display_chain.append(b)
        
    return render_template('ledger.html', chain=display_chain)

@app.route('/leaderboard')
def leaderboard():
    users = user_manager.get_all_users()
    stats = []
    
    for u in users:
        bal = blockchain.get_user_balance(u)
        total_emissions = 0
        eco_score_avg = 0
        count = 0
        
        for block in blockchain.chain:
            if block['user_id'] == u and block['transaction_type'] == 'emission':
                total_emissions += block['data'].get('net', 0)
                eco_score_avg += block['data'].get('score', 0)
                count += 1
        
        avg_score = round(eco_score_avg / count) if count > 0 else 0
        
        stats.append({
            'username': u,
            'balance': bal,
            'total_emissions': round(total_emissions, 2),
            'eco_score': avg_score
        })
    
    # Sort by Eco Score (desc) then Balance
    stats.sort(key=lambda x: (x['eco_score'], x['balance']), reverse=True)
    
    return render_template('leaderboard.html', stats=stats)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
