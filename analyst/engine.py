import json
import os
import datetime
from config import Config
from emissions import get_state_baseline, INDIA_NATIONAL_AVERAGE


def load_entries():
    if not os.path.exists(Config.ENTRIES_FILE):
        return {}
    try:
        with open(Config.ENTRIES_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}


def save_entry(username, date_str, entry_data):
    """
    Save or overwrite a user's entry for a given date.
    entry_data should be the full result dict from calculate_daily_emissions
    plus raw inputs and credits earned.
    """
    entries = load_entries()
    if username not in entries:
        entries[username] = {}
    entries[username][date_str] = entry_data
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    with open(Config.ENTRIES_FILE, 'w') as f:
        json.dump(entries, f, indent=2)


def get_user_entries(username):
    """Returns dict of {date_str: entry} sorted oldest to newest."""
    entries = load_entries()
    user_data = entries.get(username, {})
    return dict(sorted(user_data.items()))


def can_submit_today(username):
    """Returns (can_submit: bool, existing_entry: dict or None)"""
    today = datetime.date.today().isoformat()
    entries = get_user_entries(username)
    existing = entries.get(today)
    return (existing is None), existing


def get_personal_average(username):
    """Average net emissions over all entries except today."""
    today = datetime.date.today().isoformat()
    entries = get_user_entries(username)
    values = [
        e['net_emissions'] for d, e in entries.items()
        if d != today and 'net_emissions' in e
    ]
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def get_monthly_usage(username):
    """Returns total net emissions logged this calendar month."""
    now = datetime.date.today()
    prefix = now.strftime('%Y-%m')
    entries = get_user_entries(username)
    total = sum(
        e['net_emissions'] for d, e in entries.items()
        if d.startswith(prefix) and 'net_emissions' in e
    )
    return round(total, 2)


def get_weekly_trend(username):
    """
    Returns 'improving', 'worsening', or 'stable'
    by comparing last 3 days avg vs 3 days before that.
    """
    entries = get_user_entries(username)
    dates = sorted(entries.keys())
    if len(dates) < 4:
        return 'stable'

    recent = dates[-3:]
    previous = dates[-6:-3] if len(dates) >= 6 else dates[:-3]

    def avg(ds):
        vals = [entries[d]['net_emissions'] for d in ds if 'net_emissions' in entries[d]]
        return sum(vals) / len(vals) if vals else 0

    recent_avg = avg(recent)
    prev_avg = avg(previous)

    if prev_avg == 0:
        return 'stable'
    change = (recent_avg - prev_avg) / prev_avg

    if change < -0.05:
        return 'improving'
    elif change > 0.05:
        return 'worsening'
    return 'stable'


def detect_anomaly(username, today_net):
    """
    Returns True if today's emission is more than 2x personal average.
    Flights/shopping are excluded from this check automatically
    since they're not in net_emissions.
    """
    avg = get_personal_average(username)
    if avg is None or avg == 0:
        return False
    return today_net > (avg * 2.0)


def get_streak_status(username):
    """
    Returns current streak length by checking consecutive days
    where net < personal average.
    """
    entries = get_user_entries(username)
    dates = sorted(entries.keys(), reverse=True)
    if not dates:
        return 0

    avg = get_personal_average(username)
    if avg is None:
        return 0

    streak = 0
    for d in dates:
        net = entries[d].get('net_emissions', 999)
        if net < avg:
            streak += 1
        else:
            break
    return streak


def get_peer_rank(username, all_usernames):
    """
    Returns (rank, total_users) by average daily emissions.
    Lower emissions = better rank.
    """
    averages = {}
    for u in all_usernames:
        avg = get_personal_average(u)
        if avg is not None:
            averages[u] = avg

    if username not in averages:
        return None, len(all_usernames)

    sorted_users = sorted(averages.items(), key=lambda x: x[1])
    rank = next((i + 1 for i, (u, _) in enumerate(sorted_users) if u == username), None)
    return rank, len(averages)


def build_analyst_report(username, user_state, all_usernames, monthly_goal):
    """
    Master function. Returns a structured dict with all insights.
    This is what gets passed to the narrator and the template.
    """
    entries = get_user_entries(username)
    today = datetime.date.today().isoformat()
    today_entry = entries.get(today)

    personal_avg = get_personal_average(username)
    monthly_used = get_monthly_usage(username)
    state_baseline = get_state_baseline(user_state)
    trend = get_weekly_trend(username)
    streak = get_streak_status(username)
    rank, total_users = get_peer_rank(username, all_usernames)

    # Monthly goal progress
    monthly_remaining = round(monthly_goal - monthly_used, 2) if monthly_goal else None
    days_left = (datetime.date.today().replace(day=1) +
                 datetime.timedelta(days=32)).replace(day=1) - datetime.date.today()
    days_left = days_left.days

    # Projection: at current avg, will they hit goal?
    on_track = None
    if personal_avg and monthly_goal:
        projected = monthly_used + (personal_avg * days_left)
        on_track = projected <= monthly_goal

    # Anomaly (only if today has an entry)
    anomaly = False
    if today_entry:
        anomaly = detect_anomaly(username, today_entry.get('net_emissions', 0))

    # Breakdown dominance — which category is biggest today
    dominant_category = None
    if today_entry and today_entry.get('breakdown'):
        bd = today_entry['breakdown']
        dominant_category = max(bd, key=bd.get) if bd else None

    return {
        'username':           username,
        'today_net':          today_entry.get('net_emissions') if today_entry else None,
        'today_score':        today_entry.get('eco_score') if today_entry else None,
        'personal_avg':       personal_avg,
        'state_baseline':     state_baseline,
        'national_avg':       INDIA_NATIONAL_AVERAGE,
        'monthly_used':       monthly_used,
        'monthly_goal':       monthly_goal,
        'monthly_remaining':  monthly_remaining,
        'days_left_in_month': days_left,
        'on_track':           on_track,
        'trend':              trend,
        'streak':             streak,
        'rank':               rank,
        'total_users':        total_users,
        'anomaly_today':      anomaly,
        'dominant_category':  dominant_category,
        'entry_count':        len(entries),
    }