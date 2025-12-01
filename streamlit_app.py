# streamlit_app.py (comfy, colorful UI)
import streamlit as st
import pandas as pd
import sqlite3
import io, sys, traceback, os, json
from simple_ingest import init_db, ingest
from simple_prompt_call import generate_suggestions as llm_generate

# --- Page config
st.set_page_config(
    page_title="BondKeeper — Social Interaction AI",
    page_icon="🤝",
    layout="wide",
)

# --- CSS / design variables (soft palette, rounded cards)
PRIMARY = "#5B8BF7"      # soft blue
ACCENT = "#7BE495"       # mint
BG = "#F7FAFF"
CARD = "#FFFFFF"
TEXT = "#1F2937"
MUTED = "#6B7280"

STYLES = f"""
<style>
:root {{
  --primary: {PRIMARY};
  --accent: {ACCENT};
  --bg: {BG};
  --card: {CARD};
  --text: {TEXT};
  --muted: {MUTED};
}}

body {{ background: var(--bg); color: var(--text); }}
header .css-1v3fvcr {{ display:none; }} /* hide default menu area (Streamlit internals vary) */

.app-header {{
  display:flex;
  align-items:center;
  gap:16px;
  padding:18px;
  border-radius:14px;
  background: linear-gradient(90deg, rgba(91,139,247,0.12), rgba(123,228,149,0.07));
  margin-bottom:18px;
  box-shadow: 0 6px 18px rgba(40,50,80,0.04);
}}
.brand-title {{
  font-size:28px;
  font-weight:700;
  color:var(--text);
  margin:0;
}}
.brand-sub {{
  margin:0;
  color:var(--muted);
  font-size:13px;
}}

.card {{
  background: var(--card);
  padding:16px;
  border-radius:12px;
  box-shadow: 0 6px 16px rgba(33, 40, 60, 0.04);
  margin-bottom:12px;
}}

.small-muted {{
  color:var(--muted);
  font-size:12px;
}}

.btn-primary {{
  background: var(--primary) !important;
  color: white !important;
  border-radius:10px !important;
  padding: 8px 12px !important;
  box-shadow:none !important;
}}

.contact-item {{
  padding:10px;
  border-radius:10px;
  background: linear-gradient(90deg, rgba(91,139,247,0.04), rgba(0,0,0,0.00));
  margin-bottom:8px;
}}

.json-card {{
  font-family: monospace;
  background:#0f1724;
  color:#e6f2ff;
  padding:12px;
  border-radius:8px;
  overflow:auto;
}}
</style>
"""

st.markdown(STYLES, unsafe_allow_html=True)

# --- Header area (left brand + right quick stats)
with st.container():
    st.markdown(
        """
        <div class="app-header">
            <div style="font-size:36px">🤝</div>
            <div>
              <h1 class="brand-title">BondKeeper — Social Interaction AI</h1>
              <div class="brand-sub">Gentle nudges, empathetic replies, and short actionable follow-ups — built for better relationships</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- Sidebar settings
with st.sidebar:
    st.header("Controls")
    if st.button("Initialize Database"):
        try:
            init_db()
            st.success("Database initialized.")
        except Exception as e:
            st.error("Init failed")
            st.text(traceback.format_exc())

    st.markdown("---")
    st.markdown("**Upload CSV** (timestamp,direction,text)")
    uploaded = st.file_uploader("Upload message CSV", type=["csv"])
    contact_name = st.text_input("Contact Name (for import)", value="")

    if st.button("Import messages"):
        if not uploaded:
            st.error("Upload a CSV first.")
        elif not contact_name.strip():
            st.error("Enter contact name before importing.")
        else:
            try:
                df = pd.read_csv(uploaded)
                df.to_csv("uploaded_messages.csv", index=False)
                ingest("uploaded_messages.csv", contact_name.strip())
                st.success(f"Imported messages for {contact_name.strip()}")
            except Exception:
                st.error("Import failed")
                st.text(traceback.format_exc())

    st.markdown("---")
    st.markdown("**Demo Options**")
    use_mock = st.checkbox("Force mock output (no API calls)", value=False)
    st.markdown("**Appearance**")
    st.caption("Choose a color accent")
    st.markdown(f"<div style='display:flex;gap:8px'><div style='background:{PRIMARY};width:24px;height:24px;border-radius:6px'></div><div style='background:{ACCENT};width:24px;height:24px;border-radius:6px'></div></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("Made with ❤️ — Keep relationships real")

# --- Main content area
col1, col2 = st.columns([1, 1.4], gap="large")

# Left column: contacts + recent convos
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Contacts")
    try:
        conn = sqlite3.connect("bondkeeper.db")
        cur = conn.cursor()
        cur.execute("SELECT contact_id, name FROM contacts ORDER BY contact_id DESC")
        contacts = cur.fetchall()
        conn.close()
    except Exception:
        contacts = []

    if not contacts:
        st.info("No contacts found. Import messages to populate contacts.")
    else:
        for cid, name in contacts:
            # fetch 2 latest messages preview for UI
            conn = sqlite3.connect("bondkeeper.db")
            cur = conn.cursor()
            cur.execute("SELECT timestamp, direction, text FROM conversations WHERE contact_id=? ORDER BY timestamp DESC LIMIT 2", (cid,))
            msgs = cur.fetchall()
            conn.close()
            preview = "<br/>".join([f"<span style='font-size:13px;color:var(--muted)'>[{m[0]}] {m[1]}: {m[2][:80]}...</span>" for m in msgs])
            st.markdown(f"<div class='contact-item'><b>{name}</b> <span class='small-muted'> — id={cid}</span><div style='margin-top:6px'>{preview}</div></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Quick Actions")
    contact_id = st.number_input("Contact ID to generate for", min_value=1, value=1, step=1)
    if st.button("Generate Suggestions", key="gen_main"):
        # call llm and capture output
        try:
            # capture printed stdout from backend
            temp_out = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = temp_out
            try:
                # respect mock toggle in sidebar
                if use_mock:
                    os.environ["USE_MOCK"] = "1"
                else:
                    if "USE_MOCK" in os.environ:
                        os.environ.pop("USE_MOCK")
                llm_generate(contact_id)
            finally:
                sys.stdout = old_stdout
            output = temp_out.getvalue()
            if output:
                st.success("Suggestions generated below")
                # try to parse JSON from output
                try:
                    parsed = json.loads(output)
                    st.markdown("<div style='margin-top:8px'><b>Short</b></div>", unsafe_allow_html=True)
                    st.write(parsed.get("short",""))
                    st.markdown("<div style='margin-top:8px'><b>Neutral</b></div>", unsafe_allow_html=True)
                    st.write(parsed.get("neutral",""))
                    st.markdown("<div style='margin-top:8px'><b>Warm</b></div>", unsafe_allow_html=True)
                    st.write(parsed.get("warm",""))
                    st.markdown("<div style='margin-top:8px'><b>Action</b></div>", unsafe_allow_html=True)
                    st.info(parsed.get("action",""))
                    st.markdown("<hr/>", unsafe_allow_html=True)
                    st.markdown("<div class='json-card'>" + json.dumps(parsed, indent=2) + "</div>", unsafe_allow_html=True)
                except Exception:
                    # fallback: show raw
                    st.code(output, language="json")
            else:
                st.warning("No output returned. Check logs/terminal.")
        except Exception:
            st.error("Failed to generate suggestions.")
            st.text(traceback.format_exc())
    st.markdown('</div>', unsafe_allow_html=True)

# Right column: instructions + logs
with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("How to use BondKeeper")
    st.write(
        """
        1. Initialize database (if first-time).  
        2. Upload a CSV with columns: `timestamp,direction,text`.  
        3. Enter a Contact Name and click Import messages.  
        4. Select a contact id from the Contacts list on the left.  
        5. Click Generate Suggestions and review Short / Neutral / Warm / Action outputs.
        """
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Last run output (debug)")
    try:
        # show small tail of streamlit_server.log if present - helpful when deployed
        log_path = ".streamlit/logs/debug.log"
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()[-40:]
                st.text("".join(lines))
        else:
            st.text("No local debug log found. Use the terminal for live logs.")
    except Exception:
        st.text("Could not read logs.")
    st.markdown("</div>", unsafe_allow_html=True)

# footer
st.markdown("<div style='margin-top:18px; text-align:center; color:var(--muted)'>BondKeeper — built for kinder, smaller social nudges • Demo mode</div>", unsafe_allow_html=True)
