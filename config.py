import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ── Keep your original secret key exactly as is ──
    SECRET_KEY = "super-secret-key"

    # ── File paths ────────────────────────────────────
    DATA_DIR = "data"
    USERS_FILE = "data/users.json"
    ENTRIES_FILE = "data/entries.json"
    ASSET_ID_FILE = "data/asset_id.json"

    # ── Algorand ──────────────────────────────────────
    ALGO_TREASURY_MNEMONIC = os.getenv("ALGO_TREASURY_MNEMONIC")
    ALGO_TREASURY_ADDRESS  = os.getenv("ALGO_TREASURY_ADDRESS")
    ANTHROPIC_API_KEY      = os.getenv("ANTHROPIC_API_KEY", "")

    # ── App behaviour ─────────────────────────────────
    DAILY_ENTRY_LIMIT       = 1
    STREAK_BONUS_CREDITS    = 2.0
    STREAK_BONUS_THRESHOLD  = 7