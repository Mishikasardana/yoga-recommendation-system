import sqlite3
import os
import pandas as pd
import requests
from datetime import datetime
from collections import Counter
from faster_whisper import WhisperModel
from bs4 import BeautifulSoup

# Load Whisper model (CPU-compatible)
model = WhisperModel("base", device="cpu")

# ---------------------------- Knowledge Base ----------------------------

YOGA_KNOWLEDGE_BASE = {
    "Tree Pose": {
        "benefits": "Improves balance, strengthens thighs, ankles, and spine",
        "for_issues": ["balance", "back pain", "focus"],
        "difficulty": "beginner"
    },
    "Cat-Cow": {
        "benefits": "Increases spinal flexibility, relieves back pain",
        "for_issues": ["back pain", "posture", "stress"],
        "difficulty": "beginner"
    },
    "Downward Dog": {
        "benefits": "Strengthens arms and legs, stretches shoulders",
        "for_issues": ["shoulder pain", "flexibility", "stress"],
        "difficulty": "intermediate"
    },
    "Warrior II": {
        "benefits": "Strengthens legs and arms, improves balance",
        "for_issues": ["balance", "leg strength", "stamina"],
        "difficulty": "beginner"
    },
    "Bridge Pose": {
        "benefits": "Stretches chest and spine, relieves back pain",
        "for_issues": ["back pain", "posture", "stress"],
        "difficulty": "beginner"
    },
    "Child's Pose": {
        "benefits": "Relaxes the body, calms the mind, and relieves fatigue",
        "for_issues": ["fatigue", "stress"],
        "difficulty": "beginner"
    },
    "Seated Forward Bend": {
        "benefits": "Calms the mind, relieves stress, and stretches the spine",
        "for_issues": ["fatigue", "stress"],
        "difficulty": "beginner"
    }
}

# ---------------------------- Voice Transcription ----------------------------

def transcribe_voice(audio_path):
    segments, _ = model.transcribe(audio_path)
    return " ".join([seg.text for seg in segments if seg.text])

# ---------------------------- Journal Logger ----------------------------

def save_journal_entry(user_id, journal_text):
    conn = sqlite3.connect("yoga_recommendation.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS journal_logs (
            user_id INTEGER,
            entry_date TEXT,
            journal_text TEXT
        )
    """)
    cursor.execute("""
        INSERT INTO journal_logs (user_id, entry_date, journal_text)
        VALUES (?, ?, ?)
    """, (user_id, datetime.now().strftime("%Y-%m-%d"), journal_text))
    conn.commit()
    conn.close()

# ---------------------------- Get User Data ----------------------------

def get_user_data(user_id):
    conn = sqlite3.connect("yoga_recommendation.db")
    cursor = conn.cursor()

    cursor.execute("SELECT name, age, gender, injury_history, fitness_goal FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    cursor.execute("SELECT pose_accuracy, major_errors FROM weekly_data WHERE user_id = ?", (user_id,))
    data = cursor.fetchall()

    cursor.execute("SELECT journal_text FROM journal_logs WHERE user_id = ?", (user_id,))
    journal_entries = [row[0] for row in cursor.fetchall()]
    conn.close()

    accuracies = [d[0] for d in data]
    errors = [d[1].lower() for d in data if d[1]]
    avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 100
    trend = "improving" if len(accuracies) >= 2 and accuracies[-1] > accuracies[-2] else "stagnant"
    all_errors = " ".join(errors)
    recurring = Counter([w for w in ["back pain", "shoulder pain", "knee pain", "fatigue"] 
                        if " ".join(journal_entries).lower().count(w) >= 2])

    return {
        "name": user[0], "age": user[1], "gender": user[2],
        "injury": user[3], "goal": user[4],
        "avg_accuracy": avg_accuracy,
        "accuracy_trend": trend,
        "common_errors": all_errors,
        "recurring_issues": recurring,
        "journal_history": journal_entries
    }

# ---------------------------- Wikipedia Knowledge Fetch ----------------------------

def fetch_wiki_asana_info(pose_name):
    try:
        response = requests.get(
            f"https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "titles": pose_name,
                "prop": "extracts",
                "exintro": True,
                "explaintext": True
            }
        )
        data = response.json()
        page = next(iter(data['query']['pages'].values()))
        return page.get('extract', 'No Wikipedia information available.')
    except:
        return "Could not fetch additional information"

# ---------------------------- Web Search (DuckDuckGo) ----------------------------

def search_web(query, max_results=2):
    try:
        url = f"https://duckduckgo.com/html/?q={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        results = []
        for link in soup.select(".result__a", limit=max_results):
            text = link.get_text(strip=True)
            href = link.get("href")
            results.append(f"{text}\n{href}")
        return results if results else ["No results found."]
    except Exception as e:
        return [f"Error fetching search results: {str(e)}"]

# ---------------------------- Recommendation Engine ----------------------------

def generate_recommendations(user_data, journal_text):
    issues = set()
    text = journal_text.lower() + " " + user_data['common_errors'].lower()

    if any(f in text for f in ["tired", "fatigue", "exhausted"]):
        issues.add("fatigue")
    if any(p in text for p in ["back pain", "backache"]):
        issues.add("back pain")
    if "shoulder" in text:
        issues.add("shoulder pain")
    if "knee" in text:
        issues.add("knee pain")
    if any(b in text for b in ["balance", "dizzy", "unstable"]):
        issues.add("balance")

    for issue, count in user_data['recurring_issues'].items():
        if count >= 2:
            issues.add(issue)

    recommended_poses = []
    for pose, info in YOGA_KNOWLEDGE_BASE.items():
        if any(issue in info['for_issues'] for issue in issues):
            recommended_poses.append((pose, info))

    if user_data['age'] > 50 or user_data['injury']:
        recommended_poses.sort(key=lambda x: 0 if x[1]['difficulty'] == 'beginner' else 1)

    return recommended_poses[:3]

# ---------------------------- Prompt Generation ----------------------------

def build_prompt(user, journal_text, recommended_poses):
    pose_details = "\n".join(
        [f"{pose}: {info['benefits']}" for pose, info in recommended_poses]
    )

    return f"""
Yoga Recommendation Analysis:

User  Profile:
- Name: {user['name']}
- Age: {user['age']}, Gender: {user['gender']}
- Injury History: {user['injury']}
- Primary Goal: {user['goal']}
- Performance: {user['avg_accuracy']:.1f}% accuracy ({user['accuracy_trend']})
- Common Errors: {user['common_errors']}
- Recurring Issues: {', '.join(user['recurring_issues'].keys())}

Journal Entry:
"{journal_text}"

Identified Issues:
{', '.join(set(user['common_errors'].split() + list(user['recurring_issues'].keys())))}

Recommended Poses:
{pose_details}

Please provide:
1. Personalized recommendation based on above analysis
2. Pose modifications if injuries present
3. Estimated duration for practice
4. One motivational quote
"""

# ---------------------------- TinyLLaMA Integration ----------------------------

def run_tinyllama(prompt, recommended_poses):
    pose_names = [pose[0] for pose in recommended_poses]

    wiki_snippets = "\n".join([
        f"- {pose[0]}: {fetch_wiki_asana_info(pose[0])[:200]}..."
        for pose in recommended_poses
    ])

    web_results_text = ""
    for pose in pose_names:
        search_results = search_web(f"{pose} yoga benefits and steps", max_results=2)
        web_results_text += f"\n🔍 {pose} - Web Links:\n" + "\n".join(search_results) + "\n"

    return f"""
🧘 Personalized Yoga Suggestions:

📌 Recommended Poses: {', '.join(pose_names)}

📖 Wikipedia Insights:
{wiki_snippets}

🌐 Web Resources:
{web_results_text.strip()}

📋 Practice Tips:
- Hold each pose for 30–60 seconds
- Use a pillow/blanket for support if needed
- Avoid pain and maintain consistency

💬 Quote: "Yoga is the journey of the self, through the self, to the self."
"""

# ---------------------------- Yoga Recommendation Agent ----------------------------

def recommend_yoga(user_id, journal_input, voice=False):
    journal_text = transcribe_voice(journal_input) if voice else journal_input
    save_journal_entry(user_id, journal_text)

    user = get_user_data(user_id)
    recommended_poses = generate_recommendations(user, journal_text)
    prompt = build_prompt(user, journal_text, recommended_poses)
    response = run_tinyllama(prompt, recommended_poses)

    print("🤖 Yoga Recommendation:\n", response)
    return {
        "recommendations": [pose[0] for pose in recommended_poses],
        "details": response,
        "user_data": user
    }

# ---------------------------- Weekly Report Generator ----------------------------

def generate_weekly_report(user_id):
    conn = sqlite3.connect("yoga_recommendation.db")
    cursor = conn.cursor()

    cursor.execute("SELECT session_date, pose_accuracy FROM weekly_data WHERE user_id=? ORDER BY session_date", (user_id,))
    session_data = cursor.fetchall()

    cursor.execute("SELECT entry_date, journal_text FROM journal_logs WHERE user_id=?", (user_id,))
    journal_data = cursor.fetchall()

    cursor.execute("SELECT major_errors FROM weekly_data WHERE user_id=?", (user_id,))
    errors = [row[0].lower() for row in cursor.fetchall() if row[0]]

    conn.close()

    session_df = pd.DataFrame(session_data, columns=["Date", "Accuracy"])
    fatigue_scores = [
        (date, sum(1 for word in ["tired", "pain", "exhausted"] if word in text.lower()))
        for date, text in journal_data
    ]
    fatigue_df = pd.DataFrame(fatigue_scores, columns=["Date", "Fatigue"])

    error_counts = Counter()
    for error in errors:
        error_counts.update(error.split())

    return session_df, fatigue_df, error_counts.most_common(3)


