from flask import Flask, request, render_template
from werkzeug.security import check_password_hash
import mysql.connector


app = Flask(__name__)


import mysql.connector

def create_database_if_not_exists():
    # First connect to MySQL without specifying a database
    conn = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="root@123"
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS grocery_db1")
    conn.commit()
    cursor.close()
    conn.close()
    print("Database 'grocery_db1' ensured.")

def get_db_connection():
    # Now connect to the actual DB
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="root@123",
        database="grocery_db1"
    )

def initialize_database():
    create_database_if_not_exists()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Read SQL file
    with open('grocery_db.sql', 'r') as file:
        sql_commands = file.read()

    for command in sql_commands.split(';'):
        if command.strip():
            try:
                cursor.execute(command)
            except mysql.connector.Error as err:
                print(f"SQL error: {err}")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Tables created if not exist.")


 # @app.route('/')
 # def home():
    # return "Hello, Flask!"

@app.route('/', methods=['GET'])
def index():
    search_query = request.args.get('search', '').lower()
    category = request.args.get('category', 'all')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Build the query for products
    query = """
        SELECT id, name AS product_name, image, description, price, category, stock 
        FROM inventory
    """
    params = []

    # Apply search and category filters
    if search_query:
        query += " WHERE LOWER(name) LIKE %s"
        params.append(f'%{search_query}%')
    elif category != 'all':
        query += " WHERE category = %s"
        params.append(category)

    cursor.execute(query, params)
    products = cursor.fetchall()

    # Fetch wishlist status for each product
    user_id = session.get('user_id')  # Check if user is logged in
    for product in products:
        if user_id:
            cursor.execute(
                "SELECT COUNT(*) as count FROM wishlist WHERE product_id = %s AND user_id = %s",
                (product['id'], user_id)
            )
            result = cursor.fetchone()
            product['in_wishlist'] = result['count'] > 0  # True if in wishlist
        else:
            product['in_wishlist'] = False  # Default if no user is logged in

    # Fetch reviews for each product (do NOT close connection before this)
    for product in products:
        cursor.execute(
            "SELECT content, user, rating FROM reviews WHERE product_id = %s", 
            (product['id'],)
        )
        product['reviews'] = cursor.fetchall()

    # Now, close cursor and connection after all queries are done
    cursor.close()
    conn.close()

    return render_template('index.html', products=products)

################ Login  #######################

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']  
            session['username'] = user['name']  # Store username in session
            session['email'] = user['email']
            session.modified = True
            
            print(f"User {user['email']} logged in with ID {user['id']} and Username {user['name']}")

            if user['email'] == 'kandranaveen650@gmail.com':
                return redirect(url_for('admin_dashboard'))  
            else:
                flash('Login successful!', 'success')
                return redirect(url_for('home'))  
        else:
            flash('Invalid credentials. Please try again.', 'danger')

        cursor.close()
        conn.close()

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        number = request.form['number']
        
        otp = generate_otp()
        otp_data[email] = {'otp': otp, 'timestamp': datetime.now()}

        send_email_otp(email, otp)

        flash(f'OTP sent to {email}. Please verify your OTP.', 'success')

        # Store temporary user data before OTP verification
        session['temp_user'] = {'name': name, 'email': email, 'number': number}

        return redirect(url_for('verify_otp'))

    return render_template('register.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password == confirm_password:
            hashed_password = generate_password_hash(new_password)

            email = session.get('temp_email')
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET password = %s WHERE email = %s', (hashed_password, email))
            conn.commit()
            cursor.close()
            conn.close()

            flash('Your password has been successfully reset. You can now log in.', 'success')
            session.pop('temp_email', None) 
            return redirect(url_for('login'))

        flash('Passwords do not match. Please try again.', 'danger')

    return render_template('reset_password.html')



if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)
