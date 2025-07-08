from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
import numpy as np
import joblib
import sqlite3
from datetime import datetime
from sklearn.preprocessing import MultiLabelBinarizer
from database import (
    insert_score, init_db, get_daily_averages, insert_activity, get_recent_activities,
    generate_ai_recommendations, get_current_streak, calculate_eco_points,fetch_user_goals,reset_completed_goals,seed_default_goals
)
from flask import make_response
from xhtml2pdf import pisa
from io import BytesIO
from flask import render_template_string
import csv
from flask import Response



DB_NAME = 'carbon_scores.db'
app = Flask(__name__)

init_db()


# Load joblib files
pipeline = joblib.load("./notebooks/best_carbon_emission_model.joblib")

recycling_labels = joblib.load("./notebooks/recycling_labels.joblib")
cooking_labels = joblib.load("./notebooks/cooking_labels.joblib")
ordinal_map = joblib.load("./notebooks/ordinal_map_energy_efficiency.joblib")

mlb_recycling = MultiLabelBinarizer(classes=recycling_labels)
mlb_cooking = MultiLabelBinarizer(classes=cooking_labels)

mlb_recycling.fit([[]])  # Fit with empty set using known classes
mlb_cooking.fit([[]])

# Input columns (original clean names after preprocessing)
input_columns = [
    'BodyType', 'Sex', 'Diet', 'HowOftenShower', 'HeatingEnergySource',
    'Transport', 'VehicleType', 'SocialActivity', 'MonthlyGroceryBill',
    'FrequencyofTravelingbyAir', 'VehicleMonthlyDistanceKm',
    'WasteBagSize', 'WasteBagWeeklyCount', 'HowLongTVPCDailyHour',
    'HowManyNewClothesMonthly', 'HowLongInternetDailyHour',
    'Energyefficiency', 'Recycling', 'Cooking_With'
]

# Dropdown options for categorical features
dropdown_options = {
    'BodyType': ['underweight', 'normal', 'overweight', 'obese'],
    'Sex': ['male', 'female'],
    'Diet': ['vegan', 'vegetarian', 'pescatarian', 'omnivore'],
    'HowOftenShower': ['daily', 'twice a day', 'more frequently', 'less frequently'],
    'HeatingEnergySource': ['coal', 'natural gas', 'wood', 'electricity'],
    'Transport': ['walk/bicycle', 'public', 'private'],
    'VehicleType': ['none', 'petrol', 'diesel', 'hybrid', 'lpg', 'electric', 'bus'],
    'SocialActivity': ['never', 'sometimes', 'often'],
    'FrequencyofTravelingbyAir': ['never', 'rarely', 'frequently', 'very frequently'],
    'WasteBagSize': ['small', 'medium', 'large', 'extra large'],
    'Energyefficiency': ['no', 'sometimes', 'yes'],
    'Recycling': ['Paper', 'Plastic', 'Glass', 'Metal'],
    'Cooking_With': ['Stove', 'Oven', 'Microwave', 'Grill', 'Airfryer']
}

@app.route('/')
def root():
    return redirect(url_for('dashboard'))

@app.route('/input')
def input_form():
    return render_template('input_form.html', columns=input_columns, dropdown_options=dropdown_options)

@app.route('/dashboard')
def dashboard():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    cursor.execute('SELECT score FROM carbon_scores ORDER BY timestamp DESC LIMIT 1')
    latest_score = cursor.fetchone()
    connection.close()

    if latest_score:
        try:
            score_value = float(latest_score[0])
            latest_score = round(score_value, 2)
        except Exception as e:
            print("Error converting score:", e)
            latest_score = 0
    else:
        latest_score = 0

    daily_scores = get_daily_averages()
    if daily_scores:
        values = [row[1] for row in daily_scores]
        user_avg = round(sum(values) / len(values), 2)
    else:
        user_avg = 0

    global_avg = 16.4
    goal = 10.0
    try:
        diff_percent = round(((global_avg - user_avg) / global_avg) * 100)
    except:
        diff_percent = 0

    # ✅ Fetch recent activities
    recent_activities = get_recent_activities()

    return render_template(
        'dashboard.html',
        latest_score=latest_score,
        user_avg=user_avg,
        global_avg=global_avg,
        goal=goal,
        diff_percent=diff_percent,
        recent_activities=recent_activities
    )

@app.route('/log-activity', methods=['POST'])
def log_activity():
    activity_type = request.form.get("activity_type")
    details = request.form.get("details").lower()

    carbon_impact = 0.0

    try:
        if activity_type == "Transport":
            if "car" in details:
                distance = float(''.join(filter(str.isdigit, details)))
                carbon_impact = round(distance * 0.271, 2)  # avg petrol car = 271g/km
            elif "bus" in details:
                distance = float(''.join(filter(str.isdigit, details)))
                carbon_impact = round(distance * 0.103, 2)  # bus ~103g/km
            elif "bike" in details or "cycle" in details:
                carbon_impact = 0.0
            elif "train" in details:
                distance = float(''.join(filter(str.isdigit, details)))
                carbon_impact = round(distance * 0.041, 2)  # train ~41g/km
            elif "flight" in details or "plane" in details:
                distance = float(''.join(filter(str.isdigit, details)))
                carbon_impact = round(distance * 0.255, 2)  # flight short-haul avg

        elif activity_type == "Food":
            if "beef" in details:
                carbon_impact = 27.0  # kg CO₂ per kg beef
            elif "chicken" in details:
                carbon_impact = 6.9
            elif "cheese" in details:
                carbon_impact = 13.5
            elif "vegetarian" in details:
                carbon_impact = 2.0
            elif "vegan" in details:
                carbon_impact = 1.5
            else:
                carbon_impact = 2.5  # default average food item

        elif activity_type == "Energy":
            if "ac" in details or "air conditioner" in details:
                hours = float(''.join(filter(str.isdigit, details)))
                carbon_impact = round(hours * 0.5, 2)  # ~0.5 kg/h
            elif "heater" in details:
                hours = float(''.join(filter(str.isdigit, details)))
                carbon_impact = round(hours * 0.7, 2)
            elif "fan" in details:
                hours = float(''.join(filter(str.isdigit, details)))
                carbon_impact = round(hours * 0.05, 2)
            else:
                carbon_impact = 1.5  # default avg

        else:
            carbon_impact = 2.0  # fallback

    except Exception as e:
        print("Error in estimating carbon impact:", e)
        carbon_impact = 2.5  # fallback

    insert_activity("pragyan123", activity_type, details, carbon_impact)
    return redirect('/dashboard')

@app.route('/predict-form')
def predict_form():
    return render_template('input_form.html', columns=input_columns, dropdown_options=dropdown_options)

@app.route('/predict', methods=['POST'])
def predict():
    input_data = {}

    for col in input_columns:
        val = request.form.getlist(col) if col in ['Recycling', 'Cooking_With'] else request.form.get(col)

        if col in ['Recycling', 'Cooking_With']:
            input_data[col] = val if isinstance(val, list) else [val]
        elif col == 'Energyefficiency':
            input_data[col] = ordinal_map.get(val.lower(), 0) if val else 0
        elif col in dropdown_options:
            input_data[col] = val.lower() if val else ''
        else:
            try:
                input_data[col] = float(val)
            except:
                input_data[col] = 0.0

    # Create base DataFrame
    input_df = pd.DataFrame([input_data])

    # Multi-label binarization
    recycle_array = mlb_recycling.transform([input_data['Recycling']])
    recycle_df = pd.DataFrame(recycle_array, columns=[f"Recycle_{cls}" for cls in mlb_recycling.classes_])

    cook_array = mlb_cooking.transform([input_data['Cooking_With']])
    cook_df = pd.DataFrame(cook_array, columns=[f"Cook_{cls}" for cls in mlb_cooking.classes_])

    # Drop original multi-label columns and add new encoded ones
    input_df.drop(columns=['Recycling', 'Cooking_With'], inplace=True)
    input_df = pd.concat([input_df.reset_index(drop=True), recycle_df, cook_df], axis=1)

    # Predict using pipeline
    prediction = pipeline.predict(input_df)[0]
    prediction = round(prediction/1000, 2)

    user_id = "pragyan123"
    insert_score(user_id, prediction)
    print(f"Saved score {prediction} for user {user_id}")
    return redirect('/dashboard')

@app.route('/api/daily-scores')
def api_daily_scores():
    data = get_daily_averages()
    return jsonify([
        {"date": row[0], "score": round(row[1], 2)}
        for row in data
    ])

@app.route('/api/emissions-by-category')
def emissions_by_category():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Query the total carbon impact grouped by activity type
    cur.execute("""
        SELECT activity_type, SUM(carbon_impact)
        FROM activity_logs
        GROUP BY activity_type
    """)

    data = cur.fetchall()
    conn.close()

    # Convert query result to dictionary
    emissions = {row[0]: round(row[1], 2) for row in data}

    # ✅ Ensure all categories appear even if 0
    default_categories = ["Transport", "Food", "Energy", "Shopping"]
    for cat in default_categories:
        emissions.setdefault(cat, 0.0)

    # ✅ Sort the dictionary (optional for visual consistency)
    emissions = dict(sorted(emissions.items()))

    return jsonify(emissions)

@app.route('/api/weekly-trends')
def weekly_trends():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Fetch last 7 days of scores
    cur.execute("""
        SELECT DATE(timestamp), AVG(score)
        FROM carbon_scores
        GROUP BY DATE(timestamp)
        ORDER BY DATE(timestamp) DESC
        LIMIT 7
    """)
    data = cur.fetchall()
    conn.close()

    # Convert to dict sorted by weekday order (Mon to Sun)
    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    trend_map = {datetime.strptime(row[0], '%Y-%m-%d').strftime('%a'): round(row[1], 2) for row in data}

    # Ensure all weekdays are present
    final_data = [{"day": day, "score": trend_map.get(day, 0)} for day in weekdays]

    return jsonify(final_data)

@app.route('/api/ai-recommendations')
def api_ai_recommendations():
    recs = generate_ai_recommendations("pragyan123")
    return jsonify(recs)

@app.route('/api/eco-warrior-stats')
def eco_warrior_stats():
    user_id = "pragyan123"
    streak = get_current_streak(user_id)
    points = calculate_eco_points(user_id)
    print("📊 EcoWarrior -> Streak:", streak, "| Points:", points)

    # Dynamic goal evaluation (replace with DB-driven if needed)
    goals = fetch_user_goals(user_id)


    completed_goals = sum(1 for g in goals if g["completed"])
    total_goals = len(goals)

    return jsonify({
        "streak": streak,
        "points": points,
        "completed_goals": completed_goals,
        "total_goals": total_goals,
        "goals": goals
    })

@app.route('/api/toggle-goal', methods=['POST'])
def toggle_goal():
    user_id = request.form.get("user_id")
    goal_title = request.form.get("goal_title")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE user_goals
        SET completed = 1 - completed
        WHERE user_id = ? AND goal_title = ?
    ''', (user_id, goal_title))

    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/report-metrics')
def report_metrics():
    user_id = "pragyan123"
    report_type = request.args.get('type', 'weekly')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if report_type == "monthly":
        cursor.execute('''
            SELECT SUM(score)
            FROM carbon_scores
            WHERE user_id = ? AND DATE(timestamp) >= DATE('now', '-30 days')
        ''', (user_id,))
        baseline = 1800.0  # monthly average baseline (e.g., 60kg/day × 30)
    else:
        cursor.execute('''
            SELECT SUM(score)
            FROM carbon_scores
            WHERE user_id = ? AND DATE(timestamp) >= DATE('now', '-7 days')
        ''', (user_id,))
        baseline = 450.0  # weekly average baseline

    total_emissions = cursor.fetchone()[0] or 0
    total_emissions = round(total_emissions, 2)

    reduction_percent = round(((baseline - total_emissions) / baseline) * 100)
    money_saved = round(reduction_percent * 2, 2)  # Simplified logic
    trees_equivalent = round(total_emissions / 25)

    conn.close()

    return jsonify({
        "total_emissions": total_emissions,
        "reduction_percent": reduction_percent,
        "money_saved": money_saved,
        "trees_equivalent": trees_equivalent
    })

@app.route('/download-report')
def download_report():
    user_id = "pragyan123"
    report_type = request.args.get("type", "weekly")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if report_type == "monthly":
        cursor.execute('''
            SELECT SUM(score)
            FROM carbon_scores
            WHERE user_id = ? AND DATE(timestamp) >= DATE('now', '-30 days')
        ''', (user_id,))
        baseline = 1800.0
        title = "Monthly Carbon Report"
    else:
        cursor.execute('''
            SELECT SUM(score)
            FROM carbon_scores
            WHERE user_id = ? AND DATE(timestamp) >= DATE('now', '-7 days')
        ''', (user_id,))
        baseline = 450.0
        title = "Weekly Carbon Report"

    total_emissions = cursor.fetchone()[0] or 0
    total_emissions = round(total_emissions, 2)
    reduction_percent = round(((baseline - total_emissions) / baseline) * 100)
    money_saved = round(reduction_percent * 2, 2)
    trees_equivalent = round(total_emissions / 25)

    conn.close()

    html = render_template_string(f"""
    <h2>{title}</h2>
    <ul>
      <li><strong>Total Emissions:</strong> {{ e }} kg CO₂</li>
      <li><strong>Reduction Achieved:</strong> {{ r }}%</li>
      <li><strong>Money Saved:</strong> ${{ m }}</li>
      <li><strong>Trees Equivalent:</strong> {{ t }} trees</li>
    </ul>
    """, e=total_emissions, r=reduction_percent, m=money_saved, t=trees_equivalent)

    result = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)

    if pisa_status.err:
        return "PDF generation failed", 500

    response = make_response(result.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=eco_report_{report_type}.pdf'
    return response

@app.route('/download-csv')
def download_csv():
    user_id = "pragyan123"

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT timestamp, score
        FROM carbon_scores
        WHERE user_id = ?
        ORDER BY timestamp DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()

    def generate():
        data = [["Date", "Carbon Score (kg CO₂)"]] + rows
        output = csv.StringIO()
        writer = csv.writer(output)
        writer.writerows(data)
        return output.getvalue()

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=carbon_report.csv"}
    )



@app.route('/reset-goals')
def reset_user_goals():
    reset_completed_goals("pragyan123")  # Replace or generalize as needed
    return "✅ All goals reset to incomplete!"

@app.route('/seed-goals')
def seed_goals_route():
    seed_default_goals("pragyan123")
    return "✅ Default goals inserted!"

@app.route('/clear-db')
def clear_db():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    cursor.execute('DELETE FROM carbon_scores')
    connection.commit()
    connection.close()
    return "✅ All entries cleared from the database!"

@app.route('/clear-activity')
def clear_activity():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('DELETE FROM activity_logs')
    conn.commit()
    conn.close()
    return "✅ Activity log cleared!"


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
