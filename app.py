import os
import json
import urllib.parse
import google.generativeai as genai
from dotenv import load_dotenv
from database import database
from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from flask import Flask, request, jsonify, render_template, url_for

# Load environment variables
load_dotenv()

# Configure APIs
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize the generative model for text
model = genai.GenerativeModel('gemini-2.5-pro')
app = Flask(__name__)

def get_pollinations_image(query, destination):
    """Generates an image URL from Pollinations.ai based on a query."""
    # URL-encode the query
    encoded_query = urllib.parse.quote_plus(f"cinematic photograph of {query} in {destination}")
    # Construct the URL with a specific size for consistency
    image_url = f"https://image.pollinations.ai/prompt/{encoded_query}?width=600&height=400&nologo=true"
    return image_url

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/trip')
def trip():
    return render_template('trip.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        budget = data.get('budget')
        interests = data.get('interests')
        travel_style = data.get('travel_style')
        days = data.get('days')
        destination = data.get('destination')

        itinerary_json = generate_itinerary(budget, interests, travel_style, days, destination)

        if 'error' in itinerary_json:
            return jsonify(itinerary_json)

        # Enrich with Pollinations images
        for day_plan in itinerary_json.get('itinerary', []):
            for activity in day_plan.get('activities', []):
                location_name = activity.get('location_name')
                if location_name:
                    activity['photo'] = get_pollinations_image(location_name, destination)

        # Enrich accommodation with images
        for accommodation in itinerary_json.get('accommodation', []):
            acc_name = accommodation.get('name')
            if acc_name:
                accommodation['photo'] = get_pollinations_image(acc_name, destination)

        return jsonify(itinerary_json)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred on the server. Please try again."}), 500

def generate_itinerary(budget, interests, travel_style, days, destination):
    """Generates a personalized weekend itinerary as a JSON object."""
    user_prompt = USER_PROMPT_TEMPLATE.format(
        budget=budget,
        interests=interests,
        travel_style=travel_style,
        days=days,
        destination=destination
    )
    
    full_prompt = SYSTEM_PROMPT.format(destination=destination) + f"\n\nHere is the curated database of attractions and activities:\n{json.dumps(database['destinations'], indent=2)}\n\n{user_prompt}"
    
    try:
        response = model.generate_content(full_prompt)
        # Clean the response to extract the JSON part
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
        return json.loads(cleaned_response)
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error decoding AI response: {e}")
        return {"error": "Failed to generate a valid itinerary. Please try again."}

@app.route('/.well-known/appspecific/com.chrome.devtools.json')
def devtools():
    return '', 204

if __name__ == "__main__":
    app.run(debug=True)
