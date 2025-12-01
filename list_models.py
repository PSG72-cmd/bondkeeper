# list_models.py
# Run: python list_models.py
import os
from dotenv import load_dotenv
load_dotenv()

try:
    import google.generativeai as genai
except Exception as e:
    print("google.generativeai library not installed or failed to import:", e)
    raise SystemExit(1)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY not set in .env. Please set it and retry.")
    raise SystemExit(1)

# configure key if using older SDK style; some installs require genai.configure
try:
    genai.configure(api_key=api_key)
except Exception:
    pass

print("Listing available models (this may take a moment)...\n")
try:
    for m in genai.list_models():
        # m is a protobuf-like object; print name and maybe metadata if present
        name = getattr(m, "name", None) or str(m)
        print(name)
except Exception as e:
    print("Error calling list_models():", e)
    print("If this fails, check your API key or network access.")
