📌 BondKeeper — AI-Powered Social Interaction Concierge Agent

🤝 BondKeeper is an AI agent designed to help individuals maintain healthy social relationships by analyzing conversations, understanding emotional intent, and generating empathetic replies in multiple tones (short, neutral, warm, and action-oriented).
This project is my capstone submission for the Google Agents Intensive Certification (2025) and is built using Gemini models + Python + Streamlit.

🚀 Features
🔹 Conversational Memory

Imports user conversations from a CSV

Stores them in a local SQLite database

Provides context-aware message suggestions

🔹 Empathetic AI Suggestions

For each contact, BondKeeper generates:

Short reply

Neutral reply

Warm emotional reply

Action suggestion (e.g., “Call him tomorrow”)

🔹 Streamlit Web UI

Clean, modern, colorful interface

CSV upload + contact management

One-click AI generation

Mock mode for demonstration without API costs

🔹 Flexible Backend

Gemini API powered

Fallback to mock JSON for demos

Fully open-source and reproducible

🏗️ Architecture Overview
User CSV → simple_ingest.py → SQLite DB  
SQLite DB → simple_prompt_call.py → Gemini Model  
Gemini Output → Streamlit UI → Final Replies  

📁 Project Structure
bondkeeper/
│── streamlit_app.py              
│── simple_ingest.py              
│── simple_prompt_call.py        
│── ingest_run.py               
│── sample_messages.csv         
│── requirements.txt             
│── bondkeeper.db (optional)      
│── .env.example                  
│── README.md                     

🛠️ Installation
1️⃣ Clone the repository
git clone https://github.com/YOUR_USERNAME/bondkeeper.git
cd bondkeeper

2️⃣ Create & activate virtual environment
python -m venv venv
source venv/bin/activate      # Mac/Linux
.\venv\Scripts\activate       # Windows

3️⃣ Install dependencies
pip install -r requirements.txt

4️⃣ Add your API key

Create a .env file:

GEMINI_API_KEY=YOUR-KEY-HERE
MODEL_NAME=models/gemini-pro-latest

▶️ Running BondKeeper
Start Streamlit UI
streamlit run streamlit_app.py


Your browser will open:

http://localhost:8501

🧪 Demoing Without API Usage

Enable mock responses with:

Sidebar → “Force mock output”

No API calls needed.

📚 Sample CSV Format
timestamp,direction,text
2025-11-20,user,Hey I've been stressed and not keeping up
2025-11-20,friend,It's okay bro take your time
2025-11-21,user,Great meeting today! Coffee soon?

🧵 Future Improvements

Cloud deployment

Multi-contact batch recommendations

Relationship strength scoring

Mobile responsive UI

🙋‍♂️ Author

Prathmesh Sharma
AI Agent Developer | Google Agents Intensive 2025
