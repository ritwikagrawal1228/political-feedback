# Eliworks AI Feedback System

Eliworks is a sophisticated, AI-powered platform designed to help political campaigns and organizations gather, analyze, and act on constituent feedback. It uses a scripted chatbot to engage users in meaningful conversations and leverages Google's Gemini AI to generate insightful, multi-section intelligence reports from the collected data.

![Dashboard](ui-demo-sc.png)

## Key Features

- **AI-Powered Campaign Creation**: Use a simple theme (e.g., "public transit") to have Gemini AI instantly generate a catchy campaign name, an engaging main question, and a set of relevant topics with emojis.
- **Multi-Campaign Management**: Run multiple campaigns simultaneously from a central dashboard. Each campaign has its own analytics, reports, and unique chat interface.
- **Engaging Chat Interface**: A clean, mobile-friendly chat interface guides users through a multi-step conversation, collecting both structured (topic selection) and qualitative (open-ended) feedback.
- **Dynamic Analytics Dashboard**: Each campaign card on the dashboard features live-updating charts:
    - **Pie Chart**: Shows the breakdown of initial issue selections.
    - **Line Chart**: Visualizes the user engagement funnel, showing how many participants completed each question.
- **AI-Generated Intelligence Reports**: Go beyond raw data. With one click, generate a comprehensive, nine-section report that analyzes the collected conversations. The AI provides an executive summary, emotional landscape analysis, strategic insights, social media messaging, and more.
- **Report Saving & Management**: Save any number of generated reports as HTML files. Access them at any time from the "Saved Reports" section of each campaign.
- **Easy Sharing with QR Codes**: Instantly generate a shareable URL and a scannable QR code for any campaign, making it simple to deploy in the field on posters, mailers, or digital ads.

## Tech Stack

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Database**: SQLite
- **AI**: Google Gemini 1.5 Flash API
- **Deployment**: Git, GitHub

## Setup and Installation

Follow these steps to get the Eliworks system running on your local machine.

### 1. Prerequisites
- Python 3.8+
- `pip` for package management
- Git command-line tools

### 2. Clone the Repository
```bash
git clone https://github.com/ritwikagrawal1228/political-feedback.git
cd political-feedback
```

### 3. Create a Virtual Environment
It's highly recommended to use a virtual environment to manage dependencies.
```bash
# For Windows
python -m venv env
env\Scripts\activate

# For macOS/Linux
python3 -m venv env
source env/bin/activate
```

### 4. Install Dependencies
Install all required Python packages using the `requirements.txt` file.
```bash
pip install -r requirements.txt
```

### 5. Set Up Environment Variables
Create a `.env` file in the root of the project by copying the example file.
```bash
# For Windows
copy env.example .env

# For macOS/Linux
cp env.example .env
```
Now, open the `.env` file and add your Google Gemini API key:
```
GEMINI_API_KEY="YOUR_API_KEY_HERE"
GEMINI_MODEL_NAME="gemini-1.5-flash"
DEBUG_MODE="False"
```

### 6. Initialize the Database
Run the Flask application once to initialize the database schema. This will create the `database.db` file and all necessary tables. It will also create and populate the "Sample Campaign".
```bash
flask run
```
Once you see the server running, you can stop it with `Ctrl+C`.

### 7. Seed the Database (Optional)
To populate the "Sample Campaign" with 100 fake conversations for demonstration purposes, run the `seed_database.py` script.
```bash
python seed_database.py
```

### 8. Run the Application
You can now start the Flask development server.
```bash
flask run
```
Navigate to `http://127.0.0.1:5000` in your web browser to view the campaign dashboard.