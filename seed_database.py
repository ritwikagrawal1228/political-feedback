import sqlite3
import json
import random
import time

DATABASE = 'database.db'

# --- Realistic Fake Data Pools ---
TOPICS = [
    "Affordable Housing", "Economic Growth", "Veterans' Benefits", 
    "Environment", "Infrastructure Development"
]

Q1_ANSWERS = [
    "It's just become impossible to live here. The rent is out of control.",
    "This is the most pressing issue for my family right now.",
    "I don't think the state is taking this seriously enough.",
    "I've been following this topic for a while and have some strong feelings about it.",
    "This directly impacts my community and my neighbors.",
    "We need real solutions, not just talk.",
    "It feels like nothing ever changes with this issue.",
    "I chose this because I see the consequences every single day."
]

Q2_OPINIONS = [
    "The zoning laws are outdated and need a complete overhaul.",
    "We need to incentivize developers to build more middle-income housing, not just luxury condos.",
    "The government needs to provide more direct assistance to renters, not just homeowners.",
    "Inflation is eating away at everyone's savings. We need policies that support workers.",
    "Small businesses are the backbone of our economy and they're being crushed.",
    "Veterans deserve better access to mental health services, period.",
    "The wait times at the VA are unacceptable.",
    "We need to invest in green energy, but not at the cost of current jobs.",
    "Protecting our natural resources should be a top priority for future generations.",
    "The roads are a mess and our public transit is unreliable. It's embarrassing."
]

Q4_OPINIONS_FOLLOWUP = [
    "Honestly, it's all connected. If people can't afford to live here, the economy suffers.",
    "It's about basic fairness. Everyone deserves a safe place to live and a decent job.",
    "I'm worried about the future my kids will inherit if we don't fix this.",
    "This second issue is almost as important as the first one I mentioned.",
    "We need leaders who can see the big picture and how these problems overlap.",
    "It feels like the system is rigged against normal people.",
    "I'm hopeful that things can change, but we need to act now.",
    "Just wanted to make sure my voice was heard on this as well."
]

def generate_fake_conversation(initial_topic):
    """Creates a realistic, multi-step conversation object."""
    conversation = []
    
    # Q1
    conversation.append({"from": "eli", "text": f"I see you chose {initial_topic}, what's behind that for you?"})
    conversation.append({"from": "user", "text": random.choice(Q1_ANSWERS)})
    
    # Q2
    conversation.append({"from": "eli", "text": f"What specific opinion do you have for {initial_topic}? Feel free to be blunt, we support free speech OR you can skip this."})
    if random.random() > 0.15: # 85% chance to not skip
        conversation.append({"from": "user", "text": random.choice(Q2_OPINIONS)})
    else:
        conversation.append({"from": "user", "text": "(Skipped)"})

    # Q3
    conversation.append({"from": "eli", "text": "Got it, thanks! Are there other issues of near or equal importance to you right now?"})
    second_topic = random.choice([t for t in TOPICS if t != initial_topic])
    conversation.append({"from": "user", "text": second_topic})

    # Q4
    conversation.append({"from": "eli", "text": "Feel free to express your opinion here, this is a free speech space. You can skip this as well."})
    if random.random() > 0.25: # 75% chance to not skip
        conversation.append({"from": "user", "text": random.choice(Q4_OPINIONS_FOLLOWUP)})
    else:
        conversation.append({"from": "user", "text": "(Skipped)"})

    return conversation

def seed_database():
    """Adds 100 fake submissions to the sample campaign."""
    print("Connecting to the database...")
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()

    try:
        # Find the Sample Campaign ID
        cursor.execute("SELECT id FROM campaigns WHERE name = 'Sample Campaign'")
        result = cursor.fetchone()
        if not result:
            print("Error: Could not find the 'Sample Campaign'. Please run the main app first to create it.")
            return
        
        campaign_id = result[0]
        print(f"Found 'Sample Campaign' with ID: {campaign_id}. Proceeding to generate data...")

        for i in range(100):
            initial_topic = random.choice(TOPICS)
            conversation_obj = generate_fake_conversation(initial_topic)
            conversation_json = json.dumps(conversation_obj)
            
            cursor.execute(
                "INSERT INTO conversations (campaign_id, initial_topic, conversation_json) VALUES (?, ?, ?)",
                (campaign_id, initial_topic, conversation_json)
            )
            time.sleep(0.01) # Small delay

        db.commit()
        print(f"\nSuccessfully inserted 100 fake submissions for campaign ID {campaign_id}.")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()
        print("Database connection closed.")

if __name__ == '__main__':
    seed_database() 