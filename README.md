# 🧘 Adaptive Yoga Recommendation System
This project is a Streamlit-based GUI app that recommends yoga poses based on daily journal inputs (typed or spoken) using a locally hosted LLM (TinyLLaMA) and a Whisper voice transcription model. It also tracks user progress and fatigue trends over time.

🔧 Features
📝 Text & Voice Journal Input

🧘 Personalized Yoga Pose Recommendations

🧠 Fatigue Detection using natural language

🎬 Auto-play Yoga Tutorials

📊 Weekly Progress Reports (Accuracy, Fatigue, Pose Stats)

💡 Offline-capable and Raspberry Pi 5 Optimized

📁 Project Structure
bash
Copy
Edit
.
├── app.py                   # Streamlit GUI
├── yoga_agent.py            # Core logic (LLM, Whisper, DB)
├── yoga_recommendation.db   # SQLite DB (auto-created)
└── README.md
🚀 Setup Instructions
1. 🔌 Hardware Requirements
Raspberry Pi 5 (or any Linux/Windows machine)

Microphone (for voice input)

2. 📦 Install Dependencies
bash
Copy
Edit


# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
3. 🧠 Download TinyLLaMA + Whisper Models
These are automatically downloaded on first run:

TinyLLaMA-1.1B-Chat-v0.6

Whisper tiny model (int8 CPU optimized via faster-whisper)

🧪 Run the App
bash
Copy
Edit
streamlit run app.py
Open your browser to: http://localhost:8501

🗃️ Database Tables
users: user profile info (name, age, injuries, goals)

journal_logs: daily journals (text or transcribed)

weekly_data: pose accuracy + major errors per session

📊 Reporting
Click "📈 Show Weekly Report" to see:

📈 Pose Accuracy Over Time

😓 Fatigue/Mood Trends

🔁 Common Poses Recommended

🤖 Model Notes
LLM: TinyLLaMA via HuggingFace Transformers

Voice: faster-whisper Tiny (int8) for Raspberry Pi

LangChain: Used for agent orchestration and tool chaining

# Working Demonstration
https://drive.google.com/file/d/1YQVVyRA6UvBhUNszeu_RkxbYkgcmAaeX/view?usp=sharing
