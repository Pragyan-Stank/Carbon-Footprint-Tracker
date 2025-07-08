import sqlite3
from datetime import datetime,timedelta  

DB_NAME = 'carbon_scores.db'


# ---------------- Database Initialization ----------------
def init_db():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    # Carbon scores table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carbon_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            score REAL NOT NULL,
            timestamp TEXT NOT NULL
        );
    ''')

    # Activity logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            details TEXT NOT NULL,
            carbon_impact REAL NOT NULL,
            timestamp TEXT NOT NULL
        );
    ''')

    # ✅ Add this table for Eco Warrior Goals
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            goal_title TEXT NOT NULL,
            completed INTEGER DEFAULT 0
        );
    ''')

    connection.commit()
    connection.close()
    

# ---------------- Insert & Fetch Scores ----------------
def insert_score(user_id, score):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        INSERT INTO carbon_scores (user_id, score, timestamp)
        VALUES (?, ?, ?)
    ''', (user_id, float(score), timestamp))

    connection.commit()
    connection.close()


def get_daily_averages():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute('''
        SELECT DATE(timestamp) as day, AVG(score)
        FROM carbon_scores
        GROUP BY day
        ORDER BY day DESC
    ''')

    results = cursor.fetchall()
    connection.close()
    return results


# ---------------- Insert & Fetch Activities ----------------
def insert_activity(user_id, activity_type, details, carbon_impact):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        INSERT INTO activity_logs (user_id, activity_type, details, carbon_impact, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, activity_type, details, float(carbon_impact), timestamp))

    connection.commit()
    connection.close()


def get_recent_activities(limit=5):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute('''
        SELECT activity_type, details, carbon_impact
        FROM activity_logs
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))

    rows = cursor.fetchall()
    connection.close()
    return rows


def get_emissions_by_category():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT activity_type, SUM(carbon_impact)
        FROM activity_logs
        GROUP BY activity_type
    ''')
    results = cursor.fetchall()
    conn.close()
    return {row[0]: round(row[1], 2) for row in results}


# ---------------- AI Recommendation Engine ----------------
def generate_ai_recommendations(user_id="pragyan123"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT activity_type, details, SUM(carbon_impact)
        FROM activity_logs
        WHERE user_id = ?
        GROUP BY activity_type, details
        ORDER BY SUM(carbon_impact) DESC
        LIMIT 10
    ''', (user_id,))
    data = cursor.fetchall()
    conn.close()

    recommendations = []

    for activity_type, details, impact in data:
        details = details.lower()

        if activity_type == "Transport" and ("car" in details or "scooter" in details):
            recommendations.append({
                "icon": "🚲",
                "title": "Try cycling to work 2x per week",
                "desc": "Could save 6kg CO₂ weekly"
            })
        elif activity_type == "Food" and any(meat in details for meat in ["meat", "chicken", "beef", "mutton", "biryani", "fish", "egg"]):
            recommendations.append({
                "icon": "🥗",
                "title": "Reduce meat-heavy meals like biryani",
                "desc": "Save up to 8kg CO₂ monthly"
            })
        elif activity_type == "Energy" and any(word in details for word in ["heater", "ac", "air conditioner", "fan", "light", "bulb"]):
            recommendations.append({
                "icon": "💡",
                "title": "Switch to energy-efficient appliances",
                "desc": "Could cut energy emissions by 40%"
            })
        elif activity_type == "Transport" and any(flight_word in details for flight_word in ["flight", "plane", "aeroplane"]):
            recommendations.append({
                "icon": "✈️",
                "title": "Fly less or opt for trains",
                "desc": "Flights emit the most CO₂ per km"
            })
        elif activity_type == "Transport" and "bus" in details:
            recommendations.append({
                "icon": "🚌",
                "title": "Use public transport more often",
                "desc": "Cuts CO₂ by 70% compared to cars"
    })


    return recommendations[:3]



GOAL_THRESHOLD = 10.0  # e.g., 10kg CO₂/day
GLOBAL_AVG = 16.4      # Global average in kg
POINTS_PER_KG_SAVED = 10  # Award 10 points per 1kg saved


def get_eco_warrior_stats(user_id="pragyan123"):
    return {
        "streak": get_current_streak(user_id),
        "points": calculate_eco_points(user_id),
        "completed_goals": get_completed_goals(user_id),
        "total_goals": 5  # static or dynamic as needed
    }

def get_completed_goals(user_id="pragyan123"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM user_goals WHERE user_id = ? AND completed = 1', (user_id,))
    count = cursor.fetchone()[0] or 0
    conn.close()
    return count

def fetch_user_goals(user_id="pragyan123"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT goal_title, completed FROM user_goals WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    conn.close()

    icon_map = {
        "cycle": "🚴", "vegetarian": "🥗", "bulb": "💡",
        "carpool": "🚗", "solar": "☀️"
    }

    def detect_icon(title):
        title = title.lower()
        for keyword, icon in icon_map.items():
            if keyword in title:
                return icon
        return "✅"

    unique_goals = {}
    for title, completed in rows:
        if title not in unique_goals:
            unique_goals[title] = {
                "title": title,
                "icon": detect_icon(title),
                "completed": bool(completed)
            }

    return list(unique_goals.values())

def reset_completed_goals(user_id=None):
    """
    Resets all completed goals (sets `completed` = 0) without deleting any goal titles.

    - If `user_id` is given, only that user's goals are reset.
    - If `user_id` is None, all users' goals are reset.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if user_id:
        cursor.execute('''
            UPDATE user_goals
            SET completed = 0
            WHERE user_id = ?
        ''', (user_id,))
    else:
        cursor.execute('''
            UPDATE user_goals
            SET completed = 0
        ''')

    conn.commit()
    conn.close()

def seed_default_goals(user_id="pragyan123"):
    """
    Inserts the default set of Eco Warrior goals for the user.
    Only adds if no goals exist yet for that user.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Check if goals already exist
    cursor.execute('SELECT COUNT(*) FROM user_goals WHERE user_id = ?', (user_id,))
    existing = cursor.fetchone()[0]

    if existing == 0:
        default_goals = [
            "Cycle to work 3x/week",
            "Go vegetarian 2 days/week",
            "Switch all bulbs to LED",
            "Carpool 50% of trips",
            "Install solar panels"
        ]

        for goal in default_goals:
            cursor.execute('''
                INSERT INTO user_goals (user_id, goal_title, completed)
                VALUES (?, ?, 0)
            ''', (user_id, goal))

        conn.commit()

    conn.close()


def get_current_streak(user_id="pragyan123"):
    """
    Calculate streak of days where user's carbon score is below GOAL_THRESHOLD.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DATE(timestamp), AVG(score)
        FROM carbon_scores
        WHERE user_id = ?
        GROUP BY DATE(timestamp)
        ORDER BY DATE(timestamp) DESC
    ''', (user_id,))
    
    rows = cursor.fetchall()
    conn.close()

    streak = 0
    today = datetime.now().date()

    for i, (date_str, avg_score) in enumerate(rows):
        date = datetime.strptime(date_str, "%Y-%m-%d").date()

        expected_date = today - timedelta(days=i)
        if date != expected_date:
            break  # streak broken by a missing date

        if avg_score <= GOAL_THRESHOLD:
            streak += 1
        else:
            break  # streak broken by high score

    return streak


def calculate_eco_points(user_id="pragyan123"):
    """
    Award points for CO₂ saved compared to global average over 30 days.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Total saved = global avg - user's actual score
    cursor.execute('''
        SELECT AVG(score)
        FROM carbon_scores
        WHERE user_id = ? AND DATE(timestamp) >= DATE('now', '-30 days')
    ''', (user_id,))
    user_avg = cursor.fetchone()[0] or GLOBAL_AVG

    # Saved CO₂ = (global avg - user avg) * 30
    co2_saved = max(GLOBAL_AVG - user_avg, 0) * 30
    points_from_saving = int(co2_saved * POINTS_PER_KG_SAVED)

    # Points from completed goals
    cursor.execute('''
        SELECT COUNT(*) FROM user_goals
        WHERE user_id = ? AND completed = 1
    ''', (user_id,))
    goals_completed = cursor.fetchone()[0] or 0
    goal_points = goals_completed * 100

    conn.close()
    return points_from_saving + goal_points
