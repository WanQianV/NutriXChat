from flask import Flask, render_template, request, redirect, url_for, session, jsonify # type: ignore
from flask_mysqldb import MySQL # type: ignore
from datetime import datetime
import spacy
import numpy as np
import pint
import pandas as pd
import re
import joblib
from fractions import Fraction

app = Flask(__name__)

app.secret_key = 'zxcv'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'nutrixchat'

mysql = MySQL(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'login_submit' in request.form: 
            email = request.form['email']
            password = request.form['password']
        
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM users WHERE Email = %s AND Password = %s", (email, password))
            user = cur.fetchone()
            
            if user:
                # If user exists, store user information in session
                session['user_id'] = user[0]
                session['username'] = user[2]  # 'Username' attribute is the third field in the database table
                session['birthdate'] = user[3]  # 'Birthdate' attribute is the fourth field in the database table
                session['email'] = email
                session['password'] = password
                
                cur.close()

                return redirect(url_for('login_success')) # Redirect to chatbot interface when success
            else:
                # If user doesn't exist, return an error message 
                return render_template('index.html', alert_message="Invalid email or password! Please try again!")
                
        elif 'register_submit' in request.form:
            username = request.form['username']
            email = request.form['email']
            birthdate = request.form['birthdate']
            password = request.form['password']
            
            # Check if email already exists in the database
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM users WHERE Email = %s", (email,))
            existing_user = cur.fetchone()
            cur.close()

            if existing_user:
                cur.close()
                return render_template('index.html', alert_message="Email already exists. Please use different email.")

            # If email doesn't exist, proceed with registration
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users (Email, Username, Birthdate, Password) VALUES (%s, %s, %s, %s)", (email, username, birthdate, password))
            mysql.connection.commit()
            cur.close()

            # Clear trial session variable
            session.pop('try_chatbot', None)
            
            return render_template('index.html', alert_message="Registration successful. Please login.")
    
    return render_template('index.html')

@app.route('/NutriXChat')
def login_success():
    if 'user_id' in session:
        # Retrieve the user's information from the database
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE UserID = %s", (session['user_id'],))
        user = cur.fetchone()
        cur.close()

        # Store the user's information in the session
        session['username'] = user[2]
        session['email'] = user[1]
        session['birthdate'] = user[3]
        session['password'] = user[4]

        return render_template('NutriXChat.html', username=session['username'], email=session['email'], birthdate=session['birthdate'], password=session['password'])
    else:
        return redirect(url_for('index'))

@app.route('/updateprofile', methods=['POST'])
def update_profile():
    new_username = request.form['new_username']
    new_password = request.form['new_password']
    new_birthdate = request.form['new_birthdate']
    user_id = session.get('user_id')
    if user_id:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET Username = %s WHERE UserID = %s", (new_username, user_id))
        cur.execute("UPDATE users SET Password = %s WHERE UserID = %s", (new_password, user_id))
        cur.execute("UPDATE users SET Birthdate = %s WHERE UserID = %s", (new_birthdate, user_id))
        mysql.connection.commit()
        cur.close()
        session['username'] = new_username  # Update username in session
        session['password'] = new_password  # Update password in session
        session['birthdate'] = new_birthdate  # Update date of birth in session
        return redirect(url_for('login_success'))
    else:
        return redirect(url_for('index'))


@app.route('/login')
def login():
    return render_template('loginRegisterForm.html')

# @app.route('/register')
# def register():
#     return render_template('register.html')


# redirect to nutrixchat templates without login
@app.route('/NutriXChatTry')
def NutriXChatTry():
    session['try_chatbot'] = True  # Set the session variable for trying the chatbot
    return render_template('NutriXChat.html')


# reset password
@app.route('/resetPassword', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # Validate email against the database
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE Email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user:
            # Check if new password matches confirm password
            if new_password != confirm_password:
                return render_template('forgetPassword.html', alert_message="Passwords do not match!")

            # Update password in the database
            cur = mysql.connection.cursor()
            cur.execute("UPDATE users SET Password = %s WHERE Email = %s", (new_password, email))
            mysql.connection.commit()
            cur.close()
            return render_template('index.html', alert_message="Reset password successfully!")  # Redirect to login success page 
        else:
            return render_template('forgetPassword.html', alert_message="This email is not registered! Please try again!")

    return render_template('forgetPassword.html')


# Forget Password 
@app.route('/forgetPassword')
def forgetPassword():
    return render_template('forgetPassword.html')





# Load the NER model
ner_model_path = "NER MODEL1"
nlp = spacy.load(ner_model_path)

# Load the regression model 
loaded_model = joblib.load('RandomForestRegressor_best_pipeline.pkl')



ureg = pint.UnitRegistry()
ureg.define('stick = 113.4 gram')
ureg.define('package = 1 gram')
ureg.define('slice = 1 gram')

# Define a function to preprocess each ingredient text
def preprocess_ingredient(ingredient):
    # Remove commas
    ingredient = ingredient.replace(',', '')

    # Separate numbers from units (e.g., 100ml -> 100 ml)
    ingredient = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', ingredient)
    return ingredient

# Fraction and Unicode Fraction convert to decimal point
def to_decimal(quantity_str):
    # Regular expression pattern to match fractions like '1/2', '3 1/2', etc.
    fraction_pattern = r'(\d+)\s?(\d+/\d+)'

    # Function to replace regular fractions with their equivalent decimal values
    def replace_regular_fraction(match):
        whole_part = int(match.group(1)) if match.group(1) else 0
        fraction_part = Fraction(match.group(2))
        decimal_quantity = whole_part + float(fraction_part)
        return str(decimal_quantity)

    # Replace regular fractions with their decimal equivalents
    quantity_str = re.sub(fraction_pattern, replace_regular_fraction, quantity_str)

    # Handle standalone fractions
    if '/' in quantity_str:
        fraction = Fraction(quantity_str)
        return str(float(fraction))

    # Normalize unicode fractions to their decimal representation
    quantity_str = quantity_str.replace('½', '.5').replace('⅓', '.3333').replace('¼', '.25').replace('⅕', '.2').replace('⅙', '.1667').replace('⅛', '.125').replace('⅔', '.6667').replace('⅖', '.4').replace('¾', '.75').replace('⅗', '.6').replace('⅜', '.375').replace('⅘', '.8').replace('⅚', '.8333').replace('⅝', '.625').replace('⅞', '.875')

    try:
        # Try to convert directly to float (handles whole numbers and decimals)
        return float(quantity_str)
    except ValueError:
        return quantity_str



# Define a function to convert quantity to a standard unit
def convert_to_standard_unit(quantity, unit):
    try:
        if unit.lower() == 'g':
            return quantity, unit  # If the unit is already in milliliters, return the same values
            quantity_in_standard_unit = ureg(str(quantity) + ' ' + unit).to(ureg.ml)
            return quantity_in_standard_unit.magnitude, 'g'
        if unit.lower() == 'g' or unit.lower() == 'gram' or unit.lower() == 'grams':
            return quantity, 'g'
        elif unit.lower() == 'ml' or unit.lower() == 'milliliter' or unit.lower() == 'milliliters':
            return quantity, 'ml'
        elif unit.lower() == 'l' or unit.lower() == 'liter' or unit.lower() == 'liters':
            return (quantity * ureg.liter).to(ureg.milliliter).magnitude, 'ml'
        elif unit.lower() == 'oz' or unit.lower() == 'ounce' or unit.lower() == 'ounces':
            # 1 ounce (US) = 29.5735 milliliters
            quantity_in_ml = (quantity * 29.5735)
            return quantity_in_ml, 'ml'
        elif unit.lower() == 'fl oz' or unit.lower() == 'fluid ounce' or unit.lower() == 'fluid ounces':
            # 1 fluid ounce (US) = 29.5735 milliliters
            quantity_in_ml = (quantity * 29.5735)
            return quantity_in_ml, 'ml'
        elif unit.lower() == 'cup' or unit.lower() == 'cups':
            # 1 cup (US) = 236.588 milliliters
            quantity_in_ml = (quantity * 236.588)
            return quantity_in_ml, 'ml'
        elif unit.lower() == 'tbsp' or unit.lower() == 'tablespoon' or unit.lower() == 'tablespoons':
            # 1 tablespoon (US) = 14.7868 milliliters
            quantity_in_ml = (quantity * 14.7868)
            return quantity_in_ml, 'ml'
        elif unit.lower() == 'tsp' or unit.lower() == 'teaspoon' or unit.lower() == 'teaspoons':
            # 1 teaspoon (US) = 4.92892 milliliters
            quantity_in_ml = (quantity * 4.92892)
            return quantity_in_ml, 'ml'
        elif unit.lower() == 'lb' or unit.lower() == 'pound' or unit.lower() == 'pounds':
            # 1 pound = 453.592 grams
            quantity_in_g = (quantity * 453.592)
            return quantity_in_g, 'g'
        elif unit.lower() == 'kg' or unit.lower() == 'kilogram' or unit.lower() == 'kilograms':
            quantity_in_g = (quantity * 1000)
            return quantity_in_g, 'g'
        else:
            return quantity, unit
    except:
        # If conversion fails, return 0 quantity and original unit
        return 0, unit

    

# Column names representing nutritional components
column_names = [
    'Energy', 'Protein', 'Water', 'Carbohydrate, by difference', 'Fiber, total dietary',
    'Total Sugars', 'Total lipid (fat)', 'Fatty acids, total polyunsaturated',
    'Fatty acids, total monounsaturated', 'Fatty acids, total saturated', 'Cholesterol',
    'Vitamin C, total ascorbic acid', 'Folate, total', 'Thiamin', 'Riboflavin', 'Niacin',
    'Pantothenic acid', 'Vitamin B-6', 'Vitamin B-12', 'Vitamin A, IU', 'Vitamin E (alpha-tocopherol)',
    'Vitamin D (D2 + D3)', 'Vitamin K (phylloquinone)', 'Calcium, Ca', 'Magnesium, Mg', 'Phosphorus, P', 
    'Iron, Fe', 'Potassium, K', 'Sodium, Na', 'Zinc, Zn', 'Copper, Cu', 'Selenium, Se', 'Manganese, Mn'
]

# Nutritional categories and subcategories
categories = [
    'Energy', 'Protein', 'Water', 
    '---Carbohydrates---', 'Carbohydrate, by difference', 'Fiber, total dietary', 'Total Sugars', 
    '---Lipids---', 'Total lipid (fat)', 'Fatty acids, total polyunsaturated', 'Fatty acids, total monounsaturated', 'Fatty acids, total saturated', 'Cholesterol', 
    '---Vitamins---', 'Vitamin C, total ascorbic acid', 'Folate, total', 'Thiamin', 'Riboflavin', 'Niacin', 'Pantothenic acid', 'Vitamin B-6', 'Vitamin B-12', 'Vitamin A, IU', 'Vitamin E (alpha-tocopherol)', 'Vitamin D (D2 + D3)', 'Vitamin K (phylloquinone)',
    '---Minerals---', 'Calcium, Ca', 'Magnesium, Mg', 'Phosphorus, P','Iron, Fe', 'Potassium, K', 'Sodium, Na', 'Zinc, Zn', 'Copper, Cu', 'Selenium, Se', 'Manganese, Mn'
]

# Create a dictionary to map each nutrient to its corresponding unit
nutrient_units = {
    'Energy': 'Kcal', 'Protein': 'g', 'Water': 'g', 'Carbohydrate, by difference': 'g', 
    'Fiber, total dietary': 'g', 'Total Sugars': 'g', 'Total lipid (fat)': 'g', 
    'Fatty acids, total polyunsaturated': 'g', 'Fatty acids, total monounsaturated': 'g', 
    'Fatty acids, total saturated': 'g', 'Cholesterol': 'mg', 'Vitamin C, total ascorbic acid': 'mg', 
    'Folate, total': 'µg', 'Thiamin': 'mg', 'Riboflavin': 'mg', 'Niacin': 'mg', 'Pantothenic acid': 'mg', 
    'Vitamin B-6': 'mg', 'Vitamin B-12': 'µg', 'Vitamin A, IU': 'IU', 'Vitamin E (alpha-tocopherol)': 'mg', 
    'Vitamin D (D2 + D3)': 'IU', 'Vitamin K (phylloquinone)': 'µg', 'Calcium, Ca': 'mg', 'Magnesium, Mg': 'mg', 
    'Phosphorus, P': 'mg', 'Iron, Fe': 'mg', 'Potassium, K': 'mg', 'Sodium, Na': 'mg', 
    'Zinc, Zn': 'mg', 'Copper, Cu': 'mg', 'Selenium, Se': 'µg', 'Manganese, Mn': 'mg'
}


@app.route('/process-message', methods=['POST'])
def process_message():
    if session.get('try_chatbot') and not session.get('user_id'):
        if 'message_count' not in session:
            session['message_count'] = 0
        session['message_count'] += 1

        if session['message_count'] > 2:
            return jsonify({'response': 'Please register or log in to continue using the chatbot.'})


    try:
        data = request.get_json()
        user_message = data['message']

        if 'birthdate' in session:
            birthdate = session['birthdate']
            try:
                birth_date = datetime.strptime(birthdate, '%a, %d %b %Y %H:%M:%S GMT')
                birth_year = birth_date.year
                today = datetime.now()
                age = today.year - birth_year
            except ValueError:
                return jsonify({'error': 'Invalid birthdate format. Please use the format: YYYY-MM-DD.'})
        else:
            age = 0

        # Preprocess the user message to remove commas
        user_message = user_message.replace(',', '')
        
        # Split the user message by commas and newlines
        ingredients = re.split(',|\n', user_message.strip())


        servings_per_recipe = 1
        servings_match = re.search(r'Servings per recipe:\s*(\d+)', user_message)
        if servings_match:
            servings_per_recipe = int(servings_match.group(1))
            user_message = re.sub(r'Servings per recipe:\s*\d+', '', user_message)

        # Split the user message by commas and newlines
        ingredients = re.split(',|\n', user_message.strip())
        total_nutritional_values = np.zeros(len(column_names))
        total_serving_size = 0

        valid_format_ingredients = []
        invalid_format_ingredients = []

        # response_message = "Detected Ingredients:\n"
        for ingredient in ingredients:
            detected_ingredients = []
            for ent in nlp(ingredient).ents:
                if ent.label_ in ['QUANTITY', 'UNIT', 'INGREDIENT']:
                    detected_ingredients.append((ent.text, ent.label_))

            quantity, unit, ingredient_name = None, None, None
            for detected_ingredient, label in detected_ingredients:
                if label == 'QUANTITY':
                    try:
                        quantity = to_decimal(detected_ingredient)
                    except ValueError:
                        continue
                elif label == 'UNIT':
                    unit = detected_ingredient
                elif label == 'INGREDIENT':
                    ingredient_name = detected_ingredient

            if quantity is not None and unit is not None and ingredient_name is not None:
                valid_format_ingredients.append((quantity, unit, ingredient_name))
                # response_message += f"{quantity} {unit} {ingredient_name}\n"
            else:
                invalid_format_ingredients.append(ingredient)

        for quantity, unit, ingredient_name in valid_format_ingredients:
            quantity_standard, unit_standard = convert_to_standard_unit(quantity, unit)
            serving_size = quantity_standard
            total_serving_size += serving_size

            ingredient_data = {'Quantity': quantity, 'Unit': unit, 'Ingredient': ingredient_name, 'Serving Size': serving_size}
            new_data = pd.DataFrame([ingredient_data])
            new_data = new_data.fillna(0)
            new_data = new_data.apply(pd.to_numeric, errors='ignore')
            predictions = loaded_model.predict(new_data)
            predicted_values_per_serving = predictions * (serving_size / 100)
            total_nutritional_values += np.squeeze(predicted_values_per_serving)

        nutritional_values_per_serving = total_nutritional_values / servings_per_recipe

        response_message = f"Here is the nutritional breakdown of your recipe (per serving):\n"
        response_message += f"Servings per recipe: {servings_per_recipe}\n"
        response_message += f"Total Serving Size: {total_serving_size / servings_per_recipe:.2f} g\n\n"

        for nutrient in categories:
            if nutrient.startswith('---'):
                response_message += f"\n{nutrient}\n"
            else:
                if nutrient in column_names:
                    value = nutritional_values_per_serving[column_names.index(nutrient)]
                    unit = nutrient_units.get(nutrient, '')
                    response_message += f"{nutrient}: {value:.2f} {unit}\n"


        # Determine the calorie classification based on the user's age
        energy_value = nutritional_values_per_serving[column_names.index('Energy')]
        if age <= 11:
            calorie_classification = "LOW" if energy_value < 1200 else "MODERATE" if energy_value < 1800 else "HIGH"
        elif age <= 18:
            calorie_classification = "LOW" if energy_value < 1800 else "MODERATE" if energy_value < 2800 else "HIGH"
        elif age <= 30:
            calorie_classification = "LOW" if energy_value < 2000 else "MODERATE" if energy_value < 2800 else "HIGH"
        elif age <= 50:
            calorie_classification = "LOW" if energy_value < 2000 else "MODERATE" if energy_value < 2600 else "HIGH"
        else:
            calorie_classification = "LOW" if energy_value < 1800 else "MODERATE" if energy_value < 2400 else "HIGH"

        response_message += f"\nThis recipe provides approximately {energy_value:.2f} calories per serving and is classified as '{calorie_classification} CALORIE' based on your age ({age}).\n"

        initial_data = {
            'total_nutritional_values': total_nutritional_values.tolist(),
            'total_serving_size': total_serving_size,
            'servings_per_recipe': servings_per_recipe
        }

        if invalid_format_ingredients:
            response_message += f"\n\nOpps! Looks like some ingredients could not be analyzed and were excluded from the calculation for this recipe due to missing information or cannot be recognized.\n"
            for ingredient in invalid_format_ingredients:
                response_message += f"- {ingredient}\n"
            response_message += "\n"
            response_message += f"Please ensure you use the correct format: Quantity, Unit, Ingredient (e.g., 1 larges egg).\nI'm still learning to predict units or ingredients that are more challenging, and I apologize for any inconvenience caused. Rest assured, I'm continuously working to improve. Thank you for using NutriXChat!"

        return jsonify({'response': response_message, 'initialData': initial_data})

    except Exception as e:
        response = str(e)
        return jsonify({'error': str(e)})


@app.route('/recalculate-servings', methods=['POST'])
def recalculate_servings():
    try:
        data = request.get_json()
        new_servings = data['newServings']
        initial_data = data['initialNutritionalData']

        total_nutritional_values = np.array(initial_data['total_nutritional_values'])
        total_serving_size = initial_data['total_serving_size']

        nutritional_values_per_serving = total_nutritional_values / new_servings

        response_message = f"Here is the nutritional breakdown of your recipe (per serving):\n"
        response_message += f"Servings per recipe: {new_servings}\n"
        response_message += f"Total Serving Size: {total_serving_size / new_servings:.2f} g\n\n"

        for nutrient in categories:
            if nutrient.startswith('---'):
                response_message += f"\n{nutrient}\n"
            else:
                if nutrient in column_names:
                    value = nutritional_values_per_serving[column_names.index(nutrient)]
                    unit = nutrient_units.get(nutrient, '')
                    response_message += f"{nutrient}: {value:.2f} {unit}\n"

        return jsonify({'response': response_message})

    except Exception as e:
        return jsonify({'error': str(e)})




@app.route('/clear-chats', methods=['POST'])
def clear_chats():
    try:
        # Clear the chat messages stored in the session
        session.pop('chat_messages', None)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)})



# Logout route
@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run()
