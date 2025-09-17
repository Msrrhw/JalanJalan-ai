from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import psycopg2
from dotenv import load_dotenv
import os
import json
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
CORS(app)

# -------------------------
# DB config
# -------------------------
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "itinerary_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", 5432)
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

def query_db(query, args=(), one=False):
    conn = get_db_connection()
    cur = conn.cursor()
    rv = None
    try:
        cur.execute(query, args)
        if cur.description:
            rv = cur.fetchall()
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"[DB] error: {e}")
        raise
    finally:
        cur.close()
        conn.close()
    return (rv[0] if rv else None) if one else rv

# -------------------------
# Get POIs
# -------------------------
def get_pois(budget, interests, travel_style):
    rows = query_db(
        "SELECT name, category, description, latitude, longitude FROM poi "
        "WHERE budget_level=%s AND category=ANY(%s) AND (travel_style=%s OR travel_style IS NULL)",
        (budget, interests, travel_style)
    )
    return [{"name": r[0], "category": r[1], "description": r[2], "lat": r[3], "lon": r[4]} for r in rows]

# -------------------------
# Conversation memory
# -------------------------
conversation_state = {}
SYSTEM_PROMPT = """You are JalanJalan.AI, a friendly travel assistant.
Guide the user step-by-step to create a weekend trip.
Always respond conversationally and provide buttons for budget, travel style, and interests."""

@app.route("/")
def index():
    return render_template("index.html")

# ...existing code...

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_id = data.get("user_id", "default")
        user_message = data.get("message", "").strip()

        if not conversation_state.get(user_id):
            conversation_state[user_id] = {
                "history": [],
                "stage": "idle",
                "prefs": {},
                "pois": []
            }

        state = conversation_state[user_id]
        state["history"].append({"role": "user", "content": user_message})

        # --- Stage 1: User wants to create a trip ---
        if state["stage"] == "idle" and "create" in user_message.lower() and "trip" in user_message.lower():
            state["stage"] = "ask_budget"
            reply = """
            Great! Let's plan your weekend trip 🗺️<br>
            <b>Select your budget:</b><br>
            <button class='preference-btn' data-type='budget' data-value='low'>Low</button>
            <button class='preference-btn' data-type='budget' data-value='medium'>Medium</button>
            <button class='preference-btn' data-type='budget' data-value='high'>High</button>
            """
            return jsonify({"reply": reply})

        # --- Stage 2-4: Collect preferences via buttons ---
        try:
            pref_data = json.loads(user_message)
            pref_type = pref_data.get("preference_type")
            value = pref_data.get("value")
        except Exception:
            pref_type = value = None

        if state["stage"] == "ask_budget" and pref_type == "budget":
            state["prefs"]["budget"] = value
            state["stage"] = "ask_travel_style"
            reply = f"""
            Got it! Budget: <b>{value}</b><br>
            Select your travel style:<br>
            <button class='preference-btn' data-type='travel_style' data-value='relaxed'>Relaxed</button>
            <button class='preference-btn' data-type='travel_style' data-value='adventurous'>Adventurous</button>
            <button class='preference-btn' data-type='travel_style' data-value='family-friendly'>Family-friendly</button>
            """
            return jsonify({"reply": reply})

        if state["stage"] == "ask_travel_style" and pref_type == "travel_style":
            state["prefs"]["travel_style"] = value
            state["stage"] = "ask_interests"
            reply = """
            Great! Now select your interests:<br>
            <button class='preference-btn' data-type='interest' data-value='alam'>Alam</button>
            <button class='preference-btn' data-type='interest' data-value='kuliner'>Kuliner</button>
            <button class='preference-btn' data-type='interest' data-value='sejarah'>Sejarah</button>
            <button class='preference-btn' data-type='interest' data-value='belanja'>Belanja</button>
            <button class='preference-btn' data-type='interest' data-value='santai'>Santai</button><br>
            <button class='preference-btn' data-type='confirm_interests' data-value='done'>Done</button>
            """
            state["prefs"]["interests"] = []
            return jsonify({"reply": reply})

        if state["stage"] == "ask_interests" and pref_type == "interest":
            if value not in state["prefs"]["interests"]:
                state["prefs"]["interests"].append(value)
            return jsonify({"reply": f"Added interest: <b>{value}</b>"})

        if state["stage"] == "ask_interests" and pref_type == "confirm_interests":
            state["stage"] = "suggest_options"
            budget = state["prefs"]["budget"]
            style = state["prefs"]["travel_style"]
            interests = state["prefs"]["interests"]

            pois = get_pois(budget, interests, style)
            state["pois"] = pois
            reply = "<b>Here are suggested POIs for your trip:</b><br>"
            for p in pois:
                reply += f"- {p['name']} ({p['category']}): {p['description']}<br>"
            reply += "<br><button class='preference-btn' data-type='generate_itinerary' data-value='yes'>Confirm & Generate Hourly Itinerary</button>"
            return jsonify({"reply": reply, "pois": pois})

        # --- Stage 5: Generate itinerary ---
        if state["stage"] == "suggest_options" and pref_type == "generate_itinerary":
            prefs = state["prefs"]
            pois = state["pois"]

            poi_text = "\n".join([f"- {p['name']} ({p['category']})" for p in pois])
            prompt = f"""
            You are JalanJalan.AI. User preferences: Budget {prefs['budget']}, Travel style {prefs['travel_style']}, Interests {', '.join(prefs['interests'])}.
            Suggested POIs: {poi_text}
            Generate a weekend itinerary, hour-by-hour, JSON array with fields: time, title, description, poi_name, lat, lon
            """
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)

            try:
                itinerary = json.loads(response.text)
                reply = "✅ Hour-by-hour itinerary generated!"
            except Exception:
                itinerary = [{"time": "", "title": "Itinerary", "description": response.text, "poi_name": None, "lat": None, "lon": None}]
                reply = "✅ Itinerary generated, but could not parse as JSON. Showing as text."

            state["stage"] = "completed"
            return jsonify({"reply": reply, "itinerary": itinerary})

        # --- Default: AI fallback ---
        model = genai.GenerativeModel("gemini-1.5-flash")
        full_prompt = f"{SYSTEM_PROMPT}\n\nConversation history:\n"
        for turn in state["history"]:
            full_prompt += f"{turn['role']}: {turn['content']}\n"
        full_prompt += f"user: {user_message}"

        ai_response = model.generate_content(full_prompt)
        state["history"].append({"role": "assistant", "content": ai_response.text})
        return jsonify({"reply": ai_response.text})

    except Exception as e:
        print(f"[CHAT] error: {e}")
        return jsonify({"reply": "⚠️ Internal server error. Please try again later."}), 500

# ...existing code...

if __name__ == "__main__":
    app.run(debug=True)
