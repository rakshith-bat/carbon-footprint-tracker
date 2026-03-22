from emissions import INDIA_STATE_BASELINES, INDIA_NATIONAL_AVERAGE
from analyst.engine import get_personal_average, get_user_entries
import datetime


def vs_national(personal_avg):
    """Returns % better or worse than national average."""
    if personal_avg is None:
        return None
    diff = INDIA_NATIONAL_AVERAGE - personal_avg
    pct = round((diff / INDIA_NATIONAL_AVERAGE) * 100, 1)
    return pct   # positive = better than average


def vs_state(personal_avg, state):
    baseline = INDIA_STATE_BASELINES.get(state, INDIA_NATIONAL_AVERAGE)
    if personal_avg is None:
        return None
    diff = baseline - personal_avg
    pct = round((diff / baseline) * 100, 1)
    return pct


def get_best_day(username):
    entries = get_user_entries(username)
    if not entries:
        return None, None
    best_date = min(entries, key=lambda d: entries[d].get('net_emissions', 9999))
    return best_date, entries[best_date].get('net_emissions')


def get_worst_day(username):
    entries = get_user_entries(username)
    # Exclude occasional-event days from worst-day calc
    if not entries:
        return None, None
    worst_date = max(entries, key=lambda d: entries[d].get('net_emissions', 0))
    return worst_date, entries[worst_date].get('net_emissions')


def get_category_breakdown_avg(username):
    """Average contribution per category across all entries."""
    entries = get_user_entries(username)
    if not entries:
        return {}

    totals = {}
    count = 0
    for entry in entries.values():
        bd = entry.get('breakdown', {})
        for cat, val in bd.items():
            totals[cat] = totals.get(cat, 0) + val
        count += 1

    if count == 0:
        return {}
    return {k: round(v / count, 2) for k, v in totals.items()}