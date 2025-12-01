# simple_prompt_call.py
# BondKeeper — auto-selects the best available Gemini model from your account and generates suggestions.
# Paste this file into your BondKeeper folder (replace existing), then run:
#   python simple_prompt_call.py
#
# Notes:
# - Ensure your GEMINI_API_KEY is set in a .env file in the same folder:
#     GEMINI_API_KEY=your_key_here
# - If you hit quota/billing issues, set USE_MOCK=1 in .env to force mock outputs:
#     USE_MOCK=1

import os
import sqlite3
import json
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
USE_MOCK = os.getenv("USE_MOCK", "") == "1"

# Preferred models prioritized for quality / cost trade-off (customized to the list you provided)
PREFERRED_MODELS = [
    "models/gemini-pro-latest",         # best candidate (high-quality latest)
    "models/gemini-3-pro-preview",      # preview highly capable (if present)
    "models/gemini-2.5-pro",            # strong capability
    "models/gemini-2.5-flash",          # cheaper/faster flash family
    "models/gemini-flash-latest",       # fallback flash latest
    "models/gemini-2.0-flash",          # older flash
    "models/text-bison-001",            # PaLM/Bison style fallback (if available)
]

SYSTEM_INSTRUCTION = """
You are BondKeeper — an AI assistant that helps users maintain strong relationships.

Produce STRICT JSON with four fields:
1) short: a short reply (<= 20 words)
2) neutral: a neutral reply (30–60 words)
3) warm: a warm reply (60–120 words)
4) action: one suggested next action (e.g., schedule a call, send an article)

Return JSON only, no extra commentary. Example:
{ "short": "...", "neutral": "...", "warm": "...", "action": "..." }
"""

DB = "bondkeeper.db"

# Try import of Google GenAI SDK
try:
    import google.generativeai as genai
    from google.api_core import exceptions as google_exceptions
    HAVE_GENAI = True
except Exception:
    genai = None
    google_exceptions = None
    HAVE_GENAI = False

def get_context(contact_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT name, notes FROM contacts WHERE contact_id=?", (contact_id,))
    row = cur.fetchone()
    if row is None:
        conn.close()
        raise ValueError(f"No contact found with ID {contact_id}. Please run ingestion first.")
    name, notes = row
    cur.execute("""
        SELECT timestamp, direction, text
        FROM conversations
        WHERE contact_id=?
        ORDER BY timestamp DESC LIMIT 5
    """, (contact_id,))
    messages = cur.fetchall()
    conn.close()
    return name, notes, messages

def list_available_model_names():
    """Return a list of model name strings available via the SDK (or empty if listing fails)."""
    if not HAVE_GENAI or not GEMINI_KEY:
        return []
    try:
        # configure if required
        try:
            genai.configure(api_key=GEMINI_KEY)
        except Exception:
            pass
        models = list(genai.list_models())
    except Exception:
        return []

    names = []
    for m in models:
        try:
            name = getattr(m, "name", None) or str(m)
        except Exception:
            name = str(m)
        names.append(name)
    return names

def choose_best_model():
    """Pick the best preferred model that exists in the account; return model name or None."""
    available = list_available_model_names()
    if not available:
        return None

    lowered = [a.lower() for a in available]
    # Try matching preferred models in order
    for pref in PREFERRED_MODELS:
        for name in available:
            if pref.lower() == name.lower() or pref.lower() in name.lower():
                return name
    # Fallback heuristics: pick first model with 'gemini' or 'bison' in the name
    for name in available:
        ln = name.lower()
        if "gemini" in ln or "bison" in ln or "text" in ln:
            return name
    return None

def generate_suggestions(contact_id=1):
    # gather context
    name, notes, messages = get_context(contact_id)
    user_prompt = f"Contact: {name}\nNotes: {notes}\nRecent messages: {messages}\n\nTask: return JSON with short, neutral, warm, action."

    # forced mock mode
    if USE_MOCK:
        print("USE_MOCK is enabled — returning mock suggestions.")
        print(json.dumps({
            "short": "Hey — checking in. Coffee this week?",
            "neutral": "I heard you're swamped. If you'd like, I can help break the task into small steps and assist.",
            "warm": "I'm really sorry things have been tough. I'm here for you — want to talk Friday evening and make a plan?",
            "action": "Propose a 30-minute check-in call and share a 3-step plan."
        }, indent=2))
        return

    # missing library or key => show prompt + mock for reproducibility
    if not HAVE_GENAI or not GEMINI_KEY:
        print("=== GEMINI SDK or API KEY MISSING ===")
        print("SYSTEM_INSTRUCTION:\n", SYSTEM_INSTRUCTION)
        print("\nUSER_PROMPT:\n", user_prompt)
        print("\nMock JSON (for Kaggle/demo):")
        print(json.dumps({
            "short": "Hey — checking in. Coffee this week?",
            "neutral": "I heard you're swamped. If you'd like, I can help break the task into small steps and assist.",
            "warm": "I'm really sorry things have been tough. I'm here for you — want to talk Friday evening and make a plan?",
            "action": "Propose a 30-minute check-in call and share a 3-step plan."
        }, indent=2))
        return

    # choose model
    model_name = choose_best_model()
    if not model_name:
        print("No suitable model discovered. Falling back to mock output.")
        print(json.dumps({
            "short": "Hey — checking in. Coffee this week?",
            "neutral": "I heard you're swamped. If you'd like, I can help break the task into small steps and assist.",
            "warm": "I'm really sorry things have been tough. I'm here for you — want to talk Friday evening and make a plan?",
            "action": "Propose a 30-minute check-in call and share a 3-step plan."
        }, indent=2))
        return

    print(f"Selected model: {model_name}")

    # Attempt real API call with graceful fallback
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel(model_name)
        resp = model.generate_content(SYSTEM_INSTRUCTION + "\n\n" + user_prompt)
        text = getattr(resp, "text", None) or str(resp)
        # Try to parse JSON if model returned JSON string
        try:
            parsed = json.loads(text)
            print(json.dumps(parsed, indent=2))
        except Exception:
            # If not JSON, print raw text
            print("Model output (raw):")
            print(text)
    except Exception as e:
        # detect quota/billing errors heuristically
        err_str = str(e).lower()
        is_quota = ("quota" in err_str) or ("resourceexhausted" in err_str) or ("429" in err_str)
        print("API call failed:", e)
        if is_quota:
            print("Quota/billing issue detected. Falling back to mock output.")
        else:
            print("Falling back to mock output due to error.")
        print(json.dumps({
            "short": "Hey — checking in. Coffee this week?",
            "neutral": "I heard you're swamped. If you'd like, I can help break the task into small steps and assist.",
            "warm": "I'm really sorry things have been tough. I'm here for you — want to talk Friday evening and make a plan?",
            "action": "Propose a 30-minute check-in call and share a 3-step plan."
        }, indent=2))

if __name__ == "__main__":
    try:
        generate_suggestions(1)
    except Exception as exc:
        print("Unhandled error:", exc)
        print("Ensure bondkeeper.db exists and contains a contact with contact_id=1. Run ingest_run.py to populate sample data.")
