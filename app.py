import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'randomsecretkey'
app.permanent_session_lifetime = timedelta(minutes=30)

DATABASE = 'users.db'

EMISSION_FACTORS = {
    "electricity_kwh": 0.233,
    "gasoline_liter": 2.31,
    "diesel_liter": 2.68,
    "car_mile": 0.404,
    "flight_km": 0.09,
    "natural_gas_therm": 5.3,
}

REDUCTION_SUGGESTIONS = {
    "Electricity": {
        "high": 500,
        "suggestions": [
            "Switch to LED light bulbs",
            "Use energy-efficient appliances",
            "Turn off lights and electronics when not in use",
            "Install solar panels if possible",
            "Use natural light during daytime",
            "Improve home insulation"
        ]
    },
    "Gasoline": {
        "high": 100,
        "suggestions": [
            "Consider switching to an electric or hybrid vehicle",
            "Use public transportation when possible",
            "Practice carpooling",
            "Maintain proper tire pressure",
            "Avoid aggressive driving and excessive idling"
        ]
    },
    "Diesel": {
        "high": 100,
        "suggestions": [
            "Consider switching to an electric or hybrid vehicle",
            "Optimize delivery routes",
            "Ensure regular vehicle maintenance",
            "Avoid unnecessary heavy loads"
        ]
    },
    "Car Travel": {
        "high": 500,
        "suggestions": [
            "Consider working from home when possible",
            "Use bike for short distances",
            "Plan and combine trips",
            "Consider using train for long distances",
            "Walk for short distances when possible"
        ]
    },
    "Flights": {
        "high": 1000,
        "suggestions": [
            "Consider virtual meetings instead of business travel",
            "Choose direct flights when possible",
            "Consider train travel for shorter distances",
            "Offset your flight emissions through verified programs"
        ]
    },
    "Natural Gas": {
        "high": 50,
        "suggestions": [
            "Improve home insulation",
            "Use a programmable thermostat",
            "Regular maintenance of heating system",
            "Consider switching to heat pump",
            "Lower water heater temperature"
        ]
    }
}

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def create_user_table():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.commit()

def calculate_emissions(electricity_kwh, gasoline_liters, diesel_liters, car_miles, flight_km, natural_gas_therms):
    emissions = {}
    emissions['Electricity'] = electricity_kwh * EMISSION_FACTORS["electricity_kwh"]
    emissions['Gasoline'] = gasoline_liters * EMISSION_FACTORS["gasoline_liter"]
    emissions['Diesel'] = diesel_liters * EMISSION_FACTORS["diesel_liter"]
    emissions['Car Travel'] = car_miles * EMISSION_FACTORS["car_mile"]
    emissions['Flights'] = flight_km * EMISSION_FACTORS["flight_km"]
    emissions['Natural Gas'] = natural_gas_therms * EMISSION_FACTORS["natural_gas_therm"]
    emissions['Total'] = sum(emissions.values())
    return emissions

def get_recommendations(emissions, usage_values):
    recommendations = []
    usage = {
        'Electricity': usage_values[0],
        'Gasoline': usage_values[1],
        'Diesel': usage_values[2],
        'Car Travel': usage_values[3],
        'Flights': usage_values[4],
        'Natural Gas': usage_values[5]
    }

    for category, value in usage.items():
        if value > 0:
            if value > REDUCTION_SUGGESTIONS[category]["high"]:
                recommendations.append(f"<h4>High {category} usage detected. Suggestions to reduce:</h4><ul>")
                for suggestion in REDUCTION_SUGGESTIONS[category]["suggestions"]:
                    recommendations.append(f"<li>{suggestion}</li>")
                recommendations.append("</ul>")
            elif value > REDUCTION_SUGGESTIONS[category]["high"] / 2:
                recommendations.append(f"<h4>Moderate {category} usage. Consider:</h4><ul>")
                for suggestion in REDUCTION_SUGGESTIONS[category]["suggestions"][:2]:
                    recommendations.append(f"<li>{suggestion}</li>")
                recommendations.append("</ul>")

    if not recommendations:
        recommendations.append("<h4>Your usage appears to be relatively low. Keep up the good work!</h4>")
        recommendations.append("<p>General tips to further reduce your carbon footprint:</p>")
        recommendations.append("<ul>")
        recommendations.append("<li>Continue monitoring your energy usage</li>")
        recommendations.append("<li>Consider renewable energy options</li>")
        recommendations.append("<li>Spread awareness about carbon footprint reduction</li>")
        recommendations.append("</ul>")
    return "".join(recommendations)

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('calculator'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password_hash FROM users WHERE username=?", (username,))
        row = cursor.fetchone()
        
        if row and check_password_hash(row[1], password):
            session.permanent = True
            session['user_id'] = row[0]
            session['username'] = username
            return redirect(url_for('calculator'))
        else:
            return render_template('login.html', error="Invalid username or password.")
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('calculator'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            return render_template('signup.html', error="Passwords do not match.")

        password_hash = generate_password_hash(password)
        
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?,?)", (username, password_hash))
            conn.commit()
        except sqlite3.IntegrityError:
            return render_template('signup.html', error="Username already exists.")
        
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/calculator', methods=['GET', 'POST'])
def calculator():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    result_html = None
    if request.method == 'POST':
        electricity_kwh = float(request.form.get('electricity', 0))
        gasoline_liters = float(request.form.get('gasoline', 0))
        diesel_liters = float(request.form.get('diesel', 0))
        car_miles = float(request.form.get('car_miles', 0))
        flight_km = float(request.form.get('flight_km', 0))
        natural_gas_therms = float(request.form.get('natural_gas', 0))

        emissions = calculate_emissions(electricity_kwh, gasoline_liters, diesel_liters, car_miles, flight_km, natural_gas_therms)
        usage_values = [electricity_kwh, gasoline_liters, diesel_liters, car_miles, flight_km, natural_gas_therms]
        recommendations = get_recommendations(emissions, usage_values)

        result_html = f"""
        <div class="result-box">
        <h3>Carbon Emissions Breakdown (kg CO₂e):</h3>
        <ul>
          <li>Electricity: {emissions['Electricity']:.2f}</li>
          <li>Gasoline: {emissions['Gasoline']:.2f}</li>
          <li>Diesel: {emissions['Diesel']:.2f}</li>
          <li>Car Travel: {emissions['Car Travel']:.2f}</li>
          <li>Flights: {emissions['Flights']:.2f}</li>
          <li>Natural Gas: {emissions['Natural Gas']:.2f}</li>
        </ul>
        <h3>Total Emissions: {emissions['Total']:.2f} kg CO₂e</h3>
        <h3>Recommendations for Reduction:</h3>
        {recommendations}
        </div>
        """
    
    return render_template('calculator.html', result_html=result_html)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        create_user_table()
    app.run(debug=True)
