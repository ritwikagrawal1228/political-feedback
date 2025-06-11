import sqlite3
import json
import os
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from collections import Counter
import google.generativeai as genai

# Toggled by DEBUG_MODE in .env file
DEBUG = os.getenv("DEBUG_MODE", "False").lower() in ("true", "1", "t")

campaign_bp = Blueprint('campaigns', __name__, template_folder='.')
DATABASE = 'database.db'

# --- AI Agent for Campaign Setup ---
def generate_campaign_details_with_ai(theme):
    """Uses Gemini to generate a main question and topics for a new campaign."""
    model = genai.GenerativeModel(os.getenv("GEMINI_MODEL_NAME"))
    prompt = f"""
    You are a creative assistant for a political engagement platform called EliWorks.
    Your task is to generate the core components of a new constituent outreach campaign based on a single theme.

    The user will provide a theme, for example: "public transportation".

    You must return a single, valid JSON object with three keys:
    1. "name": A catchy, short name for the campaign (e.g., "Future of State Transit").
    2. "main_question": A clear and engaging question to ask constituents.
    3. "topics": A list of exactly 5 related sub-topics. Each item in the list must be an object with two keys: "name" (the topic) and "emoji" (a relevant emoji).

    Example Input: "affordable healthcare"
    Example Output:
    {{
        "name": "Healthcare for All",
        "main_question": "What is most important to you when it comes to healthcare in our state?",
        "topics": [
            {{"name": "Lowering Costs", "emoji": "💰"}},
            {{"name": "Prescription Drugs", "emoji": "💊"}},
            {{"name": "Hospital Access", "emoji": "🏥"}},
            {{"name": "Mental Health", "emoji": "🧠"}},
            {{"name": "Insurance Coverage", "emoji": "📄"}}
        ]
    }}

    ---
    THEME: "{theme}"
    ---
    Generate the JSON output now.
    """
    try:
        response = model.generate_content(prompt)
        clean_response = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_response)
    except Exception as e:
        print(f"AI generation failed: {e}")
        return None

@campaign_bp.route('/campaigns')
def dashboard():
    """Displays the main campaign dashboard."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    # Fetch all campaigns to display on the dashboard
    cursor.execute("SELECT id, name, client, main_question FROM campaigns ORDER BY created_at DESC")
    campaigns = cursor.fetchall()
    db.close()
    
    campaigns_data = [{
        "id": row[0], "name": row[1], "client": row[2], "main_question": row[3]
    } for row in campaigns]

    return render_template('dashboard.html', campaigns=campaigns_data)

@campaign_bp.route('/campaigns/create', methods=['POST'])
def create_campaign():
    """Saves a new campaign to the database."""
    data = request.json
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO campaigns (name, client, main_question, topics_json) VALUES (?, ?, ?, ?)",
        (data['name'], data['client'], data['main_question'], json.dumps(data['topics']))
    )
    db.commit()
    new_campaign_id = cursor.lastrowid
    db.close()
    return jsonify({"status": "success", "new_campaign_id": new_campaign_id})

@campaign_bp.route('/campaigns/generate_with_ai', methods=['POST'])
def generate_with_ai():
    """API endpoint to get AI-generated campaign details."""
    theme = request.json.get('theme')
    if not theme:
        return jsonify({"error": "Theme is required."}), 400
    
    details = generate_campaign_details_with_ai(theme)
    if details:
        return jsonify(details)
    else:
        return jsonify({"error": "Failed to generate details with AI."}), 500

@campaign_bp.route('/campaigns/data/<int:campaign_id>')
def get_campaign_data(campaign_id):
    """API endpoint to fetch analytics data for a specific campaign."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    
    # Fetch all conversations for this campaign
    cursor.execute("SELECT initial_topic, conversation_json, timestamp FROM conversations WHERE campaign_id = ? ORDER BY timestamp DESC", (campaign_id,))
    rows = cursor.fetchall()
    db.close()

    # 1. Pie Chart Data (Issue Breakdown)
    all_topics = [row[0] for row in rows]
    topic_counts = Counter(all_topics)
    total_responses = len(all_topics)
    
    pie_chart_data = {
        "labels": list(topic_counts.keys()),
        "data": list(topic_counts.values())
    }

    # 2. Line Chart Data (Engagement Rate)
    # Count how many conversations reached each step (1 to 4)
    engagement_counts = [0, 0, 0, 0]
    for row in rows:
        conversation = json.loads(row[1])
        # A conversation has a length of 2 for each Q&A pair.
        # Q1 answered -> len >= 2
        # Q2 answered -> len >= 4
        # Q3 answered -> len >= 6
        # Q4 answered -> len >= 8
        num_messages = len(conversation)
        if num_messages >= 2:
            engagement_counts[0] += 1
        if num_messages >= 4:
            engagement_counts[1] += 1
        if num_messages >= 6:
            engagement_counts[2] += 1
        if num_messages >= 8:
            engagement_counts[3] += 1

    line_chart_data = {
        "labels": ["Question 1", "Question 2", "Question 3", "Question 4"],
        "data": engagement_counts
    }

    # 3. Conversations data for the submissions view
    conversations_data = []
    for row in rows:
        conversations_data.append({
            "initial_topic": row[0],
            "conversation_json": row[1],
            "timestamp": row[2]
        })

    return jsonify({
        "pie_chart": pie_chart_data,
        "line_chart": line_chart_data,
        "total_conversations": total_responses,
        "conversations": conversations_data
    }) 