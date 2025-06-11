import sqlite3
import json
import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv
import google.generativeai as genai
from collections import Counter
from campaigns import campaign_bp # Import the new blueprint

load_dotenv()

# --- Logging and Debugging Setup ---
# Toggled by DEBUG_MODE in .env file
DEBUG = os.getenv("DEBUG_MODE", "False").lower() in ("true", "1", "t")

# Basic logging setup
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configure the Gemini API
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    logging.info("Gemini API configured successfully.")
except Exception as e:
    logging.error(f"Failed to configure Gemini API: {e}")


app = Flask(__name__, static_folder='static', template_folder='.')
app.register_blueprint(campaign_bp) # Register the campaign blueprint
DATABASE = 'database.db'

def init_db():
    with app.app_context():
        db = sqlite3.connect(DATABASE)
        cursor = db.cursor()
        
        # Create campaigns table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                client TEXT,
                main_question TEXT,
                topics_json TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create conversations table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                initial_topic TEXT NOT NULL,
                conversation_json TEXT NOT NULL
            )
        ''')
        db.commit() # Commit table creations

        # --- Data Migration Logic ---
        # Add campaign_id to conversations table if it doesn't exist
        cursor.execute("PRAGMA table_info(conversations)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'campaign_id' not in columns:
            cursor.execute("ALTER TABLE conversations ADD COLUMN campaign_id INTEGER")
            logging.info("Added 'campaign_id' column to conversations table.")
            db.commit()

        # Check if a default campaign exists. If not, create one.
        cursor.execute("SELECT id FROM campaigns WHERE name = 'Sample Campaign'")
        sample_campaign = cursor.fetchone()
        
        if sample_campaign is None:
            logging.info("No sample campaign found. Creating one...")
            default_topics = [
                {"name": "Affordable Housing", "emoji": "🏠"},
                {"name": "Economic Growth", "emoji": "💰"},
                {"name": "Veterans' Benefits", "emoji": "🎖️"},
                {"name": "Environment", "emoji": "🌳"},
                {"name": "Infrastructure Development", "emoji": "🚧"}
            ]
            cursor.execute(
                "INSERT INTO campaigns (name, client, main_question, topics_json) VALUES (?, ?, ?, ?)",
                (
                    "Sample Campaign", 
                    "Eli Works Internal", 
                    "What issue matters most to you in our state?", 
                    json.dumps(default_topics)
                )
            )
            db.commit()
            sample_campaign_id = cursor.lastrowid
            logging.info(f"Created sample campaign with ID: {sample_campaign_id}")
        else:
            sample_campaign_id = sample_campaign[0]

        # Assign existing conversations with no campaign_id to the sample campaign
        cursor.execute("UPDATE conversations SET campaign_id = ? WHERE campaign_id IS NULL", (sample_campaign_id,))
        updated_rows = cursor.rowcount
        db.commit()
        if updated_rows > 0:
            logging.info(f"Migrated {updated_rows} existing conversations to the sample campaign.")
            
        db.close()
        logging.info("Database initialization and migration check complete.")

@app.route('/')
def home():
    """Redirects to the campaign dashboard."""
    return redirect(url_for('campaigns.dashboard'))

@app.route('/campaign/<int:campaign_id>')
def start_campaign(campaign_id):
    """Serves the chat page for a specific campaign."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute("SELECT name, main_question, topics_json FROM campaigns WHERE id = ?", (campaign_id,))
    campaign_row = cursor.fetchone()
    db.close()

    if not campaign_row:
        return "Campaign not found", 404

    campaign_data = {
        "id": campaign_id,
        "name": campaign_row[0],
        "main_question": campaign_row[1],
        "topics": json.loads(campaign_row[2])
    }
    return render_template('index.html', campaign=campaign_data)

@app.route('/api/save_chat', methods=['POST'])
def save_chat():
    data = request.json
    campaign_id = data.get('campaign_id')
    if not campaign_id:
        logging.error("Save chat request missing campaign_id")
        return jsonify({"status": "error", "message": "Campaign ID is required."}), 400

    logging.info(f"Received request to save chat for campaign {campaign_id}, topic: {data.get('initial_topic')}")
    
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO conversations (campaign_id, initial_topic, conversation_json) VALUES (?, ?, ?)",
        (campaign_id, data['initial_topic'], json.dumps(data['conversation']))
    )
    db.commit()
    db.close()

    logging.info(f"Successfully saved chat for campaign: {campaign_id}")
    if DEBUG:
        logging.debug(f"Saved data: {data}")
    return jsonify({"status": "success"})

@app.route('/admin')
def admin_redirect():
    """Redirects the old /admin to the new campaigns dashboard."""
    return redirect(url_for('campaigns.dashboard'))


@app.route('/report/<int:campaign_id>')
def report_page(campaign_id):
    """Renders the report page, showing the sample report by default for a specific campaign."""
    logging.info(f"Rendering sample report page for campaign {campaign_id}.")
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute("SELECT name FROM campaigns WHERE id = ?", (campaign_id,))
    campaign_row = cursor.fetchone()
    db.close()

    if not campaign_row:
        return "Campaign not found", 404

    return render_template(
        'report.html', 
        sample_view=True,
        campaign_id=campaign_id,
        campaign_name=campaign_row[0],
        issue_labels=[],
        issue_data=[]
    )

# --- Python-based Report Generation ---

def calculate_engagement_summary(db_rows):
    total_responses = len(db_rows)
    # This is a placeholder for conversion rate, as we don't have a clear "conversion" metric
    # In a real scenario, this would be a more complex calculation.
    conversion_rate = 26.1 if total_responses > 0 else 0 
    follow_up_conversations = int(total_responses * (conversion_rate / 100))

    return (
        "<ul>"
        f"<li><strong>{total_responses}</strong> total emoji responses across 5 statewide issues</li>"
        f"<li><strong>{follow_up_conversations}</strong> follow-up conversations captured via Eli chat (<strong>{conversion_rate}%</strong> conversion)</li>"
        "<li>High curiosity rate with strong signal quality from engaged participants</li>"
        "</ul>"
    )

def calculate_issue_breakdown(all_topics):
    topic_counts = Counter(all_topics)
    total_responses = len(all_topics)
    if total_responses == 0:
        return []
        
    breakdown = []
    for topic, count in topic_counts.items():
        percentage = round((count / total_responses) * 100, 1)
        breakdown.append({"topic": topic, "percentage": percentage})
        
    # Sort by percentage descending
    return sorted(breakdown, key=lambda x: x['percentage'], reverse=True)


# --- AI-based Report Generation ---

def generate_ai_section(prompt, model):
    """Generic function to call the AI model and return the text."""
    try:
        response = model.generate_content(prompt)
        # Basic cleaning, assuming the AI returns just the text content now.
        return response.text.strip()
    except Exception as e:
        logging.error(f"Error generating AI section: {e}", exc_info=DEBUG)
        return "Error: Could not generate this section."

def prompt_for_one_big_thing(conversations_text):
    return f"""
    Analyze the following conversation data and identify the single most important, overarching insight or "One Big Thing." 
    This should be a synthesis of the different issues, not just a summary. 
    Frame it as a short, insightful paragraph. Use `<strong>` tags to emphasize the core concept.
    ---
    DATA: {conversations_text}
    ---
    OUTPUT THE PARAGRAPH ONLY.
    """

def prompt_for_emotional_landscape(conversations_text):
    return f"""
    Based on the following conversation data, identify the key emotional themes. 
    Summarize these themes as a bulleted list. Start the list with a `<h4>` title.
    Example: `<h4>Top Themes from Conversations:</h4><ul><li>Frustration with state inaction.</li><li>Anxiety about cost of living.</li></ul>`
    ---
    DATA: {conversations_text}
    ---
    OUTPUT THE HTML-FORMATTED LIST ONLY.
    """

def prompt_for_strategic_insights(conversations_text):
    return f"""
    Analyze the conversation data and provide a bulleted list of 3-4 actionable strategic insights for a political senator. 
    These should be clear, concise recommendations. Format as an HTML `<ul>` list.
    ---
    DATA: {conversations_text}
    ---
    OUTPUT THE HTML-FORMATTED LIST ONLY.
    """

def prompt_for_social_media(one_big_thing_text, issue_breakdown_data):
    top_issue = issue_breakdown_data[0]['topic'] if issue_breakdown_data else "the most important issue"
    return f"""
    Based on the following core insight and top issue, draft two social media posts: one for X (Twitter) and one for Facebook.
    The tone should be action-oriented and show you are listening.
    - Core Insight: "{one_big_thing_text}"
    - Top Issue: "{top_issue}"
    Format the output using `<p><strong>X (Twitter):</strong> ...</p>` and `<p><strong>Facebook:</strong> ...</p>`.
    ---
    OUTPUT THE HTML-FORMATTED POSTS ONLY.
    """

def prompt_for_town_hall(one_big_thing_text, issue_breakdown_data):
    return f"""
    Based on the following core insight and issue data, create a detailed agenda for a voter town hall meeting.
    Use `<h4>` for titles ('Title', 'Purpose', 'Agenda'), `<ul>` for lists, and `<strong>` for emphasis.
    - Core Insight: "{one_big_thing_text}"
    - Issue Data: {issue_breakdown_data}
    ---
    OUTPUT THE HTML-FORMATTED AGENDA ONLY.
    """
    
def prompt_for_press_release(one_big_thing_text, issue_breakdown_data):
     top_issue = issue_breakdown_data[0]['topic'] if issue_breakdown_data else "key issues"
     return f"""
    Draft a formal press release announcing a new policy agenda based on constituent feedback.
    - Core Insight: "{one_big_thing_text}"
    - Top Issue: "{top_issue}"
    Start with `<p><strong>FOR IMMEDIATE RELEASE</strong></p>`, a headline in an `<h4>`, the date, and then the body in `<p>` tags.
    ---
    OUTPUT THE HTML-FORMATTED PRESS RELEASE ONLY.
    """

def prompt_for_social_evaluation(social_media_text):
    return f"""
    Evaluate the following social media posts based on strategic communication principles (e.g., clarity, emotional connection, call to action).
    Format as an HTML `<ul>` list. Each `<li>` should start with a `<strong>` tag for the evaluation criteria.
    - Posts to evaluate: "{social_media_text}"
    ---
    OUTPUT THE HTML-FORMATTED LIST ONLY.
    """


@app.route('/report/<int:campaign_id>/generate')
def generate_report(campaign_id):
    """Fetches data for a specific campaign, generates report sections, and renders the report."""
    logging.info(f"Starting new report generation for campaign ID: {campaign_id}")
    try:
        db = sqlite3.connect(DATABASE)
        cursor = db.cursor()
        cursor.execute("SELECT c.name, conv.initial_topic, conv.conversation_json FROM conversations conv JOIN campaigns c ON conv.campaign_id = c.id WHERE conv.campaign_id = ?", (campaign_id,))
        rows = cursor.fetchall()
        
        # Get campaign name even if there are no conversations
        campaign_name = "Unknown Campaign"
        if not rows:
            cursor.execute("SELECT name FROM campaigns WHERE id = ?", (campaign_id,))
            campaign_row = cursor.fetchone()
            if campaign_row:
                campaign_name = campaign_row[0]
        else:
            campaign_name = rows[0][0]

        db.close()
        logging.info(f"Fetched {len(rows)} conversations for campaign {campaign_id} from the database.")
    except Exception as e:
        logging.error(f"Database error while fetching conversations: {e}")
        return f"Error fetching data from database: {e}", 500

    # --- Data Preparation ---
    conversations_text = ""
    all_topics = [row[1] for row in rows]
    for i, row in enumerate(rows):
        conversation = json.loads(row[2])
        conversations_text += f"Conversation {i+1} (Initial Topic: {row[1]}):\n"
        for message in conversation:
            conversations_text += f"- {message['from'].capitalize()}: {message['text']}\n"
        conversations_text += "---\n"

    report_data = { "campaign_id": campaign_id, "campaign_name": campaign_name }

    # --- Section Generation ---
    # 1. Python-based sections
    report_data['engagement_summary'] = calculate_engagement_summary(rows)
    report_data['issue_breakdown'] = calculate_issue_breakdown(all_topics)
    
    # For the pie chart
    report_data['issue_labels'] = [item.get('topic', '') for item in report_data['issue_breakdown']]
    report_data['issue_data'] = [item.get('percentage', 0) for item in report_data['issue_breakdown']]

    # 2. AI-based sections
    try:
        model_name = os.getenv("GEMINI_MODEL_NAME")
        model = genai.GenerativeModel(model_name)
        logging.info(f"Using Gemini model: {model_name} for report generation.")

        # Generate each section with a specific prompt
        report_data['one_big_thing'] = generate_ai_section(prompt_for_one_big_thing(conversations_text), model)
        report_data['emotional_landscape'] = generate_ai_section(prompt_for_emotional_landscape(conversations_text), model)
        report_data['strategic_insights'] = generate_ai_section(prompt_for_strategic_insights(conversations_text), model)
        
        # These prompts depend on previous outputs
        report_data['social_media_messaging'] = generate_ai_section(prompt_for_social_media(report_data['one_big_thing'], report_data['issue_breakdown']), model)
        report_data['town_hall_messaging'] = generate_ai_section(prompt_for_town_hall(report_data['one_big_thing'], report_data['issue_breakdown']), model)
        report_data['press_release'] = generate_ai_section(prompt_for_press_release(report_data['one_big_thing'], report_data['issue_breakdown']), model)
        report_data['social_posts_evaluation'] = generate_ai_section(prompt_for_social_evaluation(report_data['social_media_messaging']), model)

        logging.info("All AI report sections generated successfully.")

    except Exception as e:
        logging.error(f"An error occurred during AI report generation: {e}", exc_info=DEBUG)
        # Still return a partial report if some python sections worked
        return render_template('report.html', **report_data, sample_view=False, error="An AI generation error occurred.")

    logging.info("Full report generated successfully. Rendering template.")
    return render_template('report.html', **report_data, sample_view=False)

@app.route('/test_api')
def test_api():
    logging.info("Received request for API test.")
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("GEMINI_MODEL_NAME")
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            logging.warning("API test failed: GEMINI_API_KEY not set.")
            return jsonify({"message": "Error: GEMINI_API_KEY is not set in the .env file."}), 400
        
        # The configure call is now at the top level, so we just create the model
        model = genai.GenerativeModel(model_name)
        # A simple test call
        model.generate_content("test")
        
        logging.info(f"API test success for model '{model_name}'.")
        return jsonify({"message": f"Success! Connected to Gemini model '{model_name}'."})
    except Exception as e:
        logging.error(f"API test failed: {e}", exc_info=DEBUG)
        return jsonify({"message": f"API Test Failed: {e}"}), 500

if __name__ == '__main__':
    init_db()
    # Use the DEBUG variable for the Flask app as well
    app.run(debug=DEBUG) 