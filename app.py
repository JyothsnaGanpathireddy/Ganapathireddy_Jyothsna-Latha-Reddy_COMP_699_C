from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
import mysql.connector
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
load_dotenv()
from flask_cors import CORS
from passlib.context import CryptContext
import json
from datetime import datetime, timedelta
import random
from flask_mail import Mail, Message
from passlib.hash import scrypt

app = Flask(__name__, static_url_path='/static')
CORS(app)

app.secret_key = 'grocery1230932rjdbsjdaskasbjkfaf'
app.config['UPLOAD_FOLDER'] = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

load_dotenv()

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')


otp_data = {}

sender_email = os.getenv("EMAIL_ADDRESS")
sender_password = os.getenv("EMAIL_PASSWORD")

def create_database_if_not_exists():
    # First connect to MySQL without specifying a database
    conn = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="root@123"
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS grocery_db")
    conn.commit()
    cursor.close()
    conn.close()
    print("Database 'grocery_db' ensured.")

def get_db_connection():
    # Now connect to the actual DB
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="root@123",
        database="grocery_db"
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

            if user['email'] == 'jyothsnalatha2002@gmail.com':
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Login successful!', 'success')
                return redirect(url_for('index'))  
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

def generate_otp(length=6):
    characters = string.digits  
    otp = ''.join(random.choice(characters) for i in range(length))
    return otp

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


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        otp = generate_otp()
        otp_data[email] = {'otp': otp, 'timestamp': datetime.now()}

        send_email_otp(email, otp)

        flash(f'OTP sent to {email}. Please verify your OTP to reset your password.', 'success')

        session['temp_email'] = email

        return redirect(url_for('verify_forgot_otp'))

    return render_template('forgot_password.html')

# Initialize the Flask-Mail object
mail = Mail(app)


def send_email_otp(to_email, otp):
    try:
        subject = "Your OTP Code"
        body = f"Your OTP code is: {otp}. It is valid for 3 minutes."
        
        msg = Message(
            subject=subject,
            recipients=[to_email],  # Recipient's email
            body=body  # Body content of the email
        )
        
        # Send the email
        mail.send(msg)
        print("OTP sent successfully!")
    except Exception as e:
        print(f"Error: {e}")

@app.before_request
def ensure_quantities_in_session():
    if 'quantities' not in session:
        session['quantities'] = {}



@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        email = session.get('temp_user', {}).get('email')  # Use email from session's temp_user
        
        if email and email in otp_data:
            stored_otp = otp_data[email]['otp']
            otp_time = otp_data[email]['timestamp']

            # Check if the entered OTP matches and if the OTP is within the allowed time
            if entered_otp == stored_otp and (datetime.now() - otp_time).seconds <= 300:  # 5 minutes window
                flash("OTP verified successfully!", "success")
                # Proceed to the next step (e.g., completing registration)
                return redirect(url_for('create_password'))
            else:
                flash("Invalid OTP or OTP expired. Please try again.", "danger")
        else:
            flash("OTP not found or session expired. Please try again.", "danger")
    
    return render_template('verify_otp.html')



@app.route('/verify-forgot-otp', methods=['GET', 'POST'])
def verify_forgot_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        email = session.get('temp_email')

        if email in otp_data:
            stored_otp = otp_data[email]['otp']
            otp_time = otp_data[email]['timestamp']

            if entered_otp == stored_otp and (datetime.now() - otp_time).seconds <= 300:
                flash('OTP verified successfully. Please create a new password.', 'success')
                return redirect(url_for('reset_password'))

            flash('Invalid or expired OTP. Please try again.', 'danger')
        else:
            flash('OTP not found. Please try again.', 'danger')

    return render_template('verify_forgot_otp.html')


@app.route('/admin')
def admin_dashboard():
    # Create a connection to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Query to fetch total users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    # Query to fetch total orders
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    # Query to fetch total inventory items
    cursor.execute("SELECT COUNT(*) FROM inventory")
    total_inventory = cursor.fetchone()[0]

    # Close the cursor and connection
    cursor.close()
    conn.close()

    # Pass the results to the template
    return render_template('admin_dashboard.html', 
                           total_users=total_users, 
                           total_orders=total_orders, 
                           total_inventory=total_inventory)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    delete_user_by_id(user_id)  # Delete user by ID
    return redirect(url_for('users'))  # Redirect to user list after deletion

def delete_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()  # Commit the changes
    cursor.close()
    conn.close()

@app.route('/total_orders')
def total_orders():
    # Fetch total orders data (replace this with actual logic)
    total_orders = get_total_orders()
    return render_template('admin_dashboard.html', total_orders=total_orders)

@app.route('/users')
def users():
    users = get_all_users()  # Get all users
    return render_template('users.html', users=users)

def get_all_users():
    conn = get_db_connection()  # Using the connection function you already have
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")  # Replace "users" with your actual table name
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = get_user_by_id(user_id)  # Fetch user by ID
    print(user)  # Check what is returned from the database
    if request.method == 'POST':
        # Get user data from form and update
        user_data = {
            'name': request.form['name'],
            'email': request.form['email'],
            'number': request.form['number']
        }
        update_user(user_id, user_data)  # Call the update function
        return redirect(url_for('users'))  # Redirect back to the user list
    return render_template('edit_user.html', user=user)  # Render the edit form

def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()  # Fetch one record
    cursor.close()
    conn.close()
    return user  # Ensure this is a dictionary or a result set containing 'user_id'

def update_user(user_id, user_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Assuming user_data is a dictionary containing the user info to update
    update_query = """
    UPDATE users 
    SET name = %s, email = %s, number = %s
    WHERE id = %s
    """
    cursor.execute(update_query, (user_data['name'], user_data['email'], user_data['number'], user_id))
    conn.commit()  # Commit the changes
    cursor.close()
    conn.close()

@app.route('/create-password', methods=['GET', 'POST'])
def create_password():
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return render_template('create_password.html')

        temp_user = session.pop('temp_user', None)
        if temp_user:
            hashed_password = generate_password_hash(password)
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)  # Using dictionary=True

            try:
                # Check if email already exists
                cursor.execute("SELECT * FROM users WHERE email = %s", (temp_user['email'],))
                if cursor.fetchone():
                    flash('Email already exists. Please use a different email or log in.', 'danger')
                    return render_template('create_password.html')

                # Check if phone number already exists
                cursor.execute("SELECT * FROM users WHERE number = %s", (temp_user['number'],))
                if cursor.fetchone():
                    flash('Phone number already exists. Please use a different number.', 'danger')
                    return render_template('create_password.html')

                # Insert new user into the database
                cursor.execute(
                    'INSERT INTO users (name, email, number, password) VALUES (%s, %s, %s, %s)',
                    (temp_user['name'], temp_user['email'], temp_user['number'], hashed_password)
                )
                conn.commit()
                flash('Registration successful. Please login.', 'success')
                return redirect(url_for('login'))

            except mysql.connector.Error as e:
                flash('Database error occurred. Please try again.', 'danger')
                print(f"MySQL Error: {e}")

            except Exception as e:
                flash('An unexpected error occurred. Please try again.', 'danger')
                print(f"Exception: {e}")

            finally:
                cursor.close()
                conn.close()

    return render_template('create_password.html')


@app.route('/update_order_status', methods=['POST'])
def update_order_status():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    try:
        order_id = request.form.get('order_id')
        new_status = request.form.get('status')

        if not order_id or not new_status:
            flash('Invalid data provided.', 'warning')
            return redirect(url_for('myorder'))
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Update the status of the order
        cursor.execute(
            """
            UPDATE orders 
            SET status = %s 
            WHERE order_id = %s
            """,
            (new_status, order_id)
        )
        
        db.commit()
        cursor.close()
        db.close()
        
        flash('Order status updated successfully!', 'success')
    except Exception as e:
        print(f"Error updating order status: {e}")
        flash('Failed to update order status.', 'danger')
    
    return redirect(url_for('myorder'))

@app.route('/filter_products', methods=['GET', 'POST'])
def filter_products():
    if request.method == 'POST':
        # Handle form data and apply the filter
        category = request.form.get('category')
        # Your filtering logic here
    return redirect(url_for('index'))

@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    temp_user = session.get('temp_user')
    if not temp_user:
        flash('No registration in progress.', 'danger')
        return redirect(url_for('register'))

    number = temp_user['number']
    email = temp_user['email']
    otp = generate_otp()

    otp_data[email] = {'otp': otp, 'timestamp': datetime.now()}
    send_email_otp(email, otp)

    flash(f'OTP resent to {email}.', 'success')
    return redirect(url_for('verify_otp'))

@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory')  # Fetching all items from inventory
    items = cursor.fetchall()  # Storing the fetched items in a variable
    conn.close()
    
    return render_template('inventory.html', inventory_items=items)

@app.route('/inventory/list')
def inventory_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory')
    inventory_items = cursor.fetchall()
    conn.close()
    return render_template('add_inventory.html')

@app.route('/inventory/add', methods=['GET', 'POST'])
def add_inventory():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        category = request.form['category']
        description = request.form['description']  # Get description
        image = request.files['image']
        
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = 'images/' + filename
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO inventory (name, price, image, category, description)
                          VALUES (%s, %s, %s, %s, %s)''', 
                       (name, price, image_path, category, description))  # Include description
        conn.commit()
        conn.close()

        return redirect(url_for('inventory_list'))

    
@app.route('/inventory/edit/<int:id>', methods=['GET', 'POST'])
def edit_inventory(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM inventory WHERE id = %s', (id,))
    item = cursor.fetchone()  # Fetch the item from the database

    if not item:  # If item doesn't exist
        return "Item not found", 404  

    if request.method == 'POST':
        price = request.form['price']
        name = request.form['name']
        category = request.form['category']
        description = request.form['description']  # Get the description from the form

        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = 'images/' + filename  
        else:
            image_path = item[4]  # If no new image is uploaded, keep the existing image path

        # Update the inventory item with the new data, including the description
        cursor.execute('''UPDATE inventory
                          SET name = %s, price = %s, image = %s, category = %s, description = %s
                          WHERE id = %s''', 
                       (name, price, image_path, category, description, id))
        conn.commit()

        conn.close()

        return redirect(url_for('inventory'))  # Redirect to inventory list page

    return render_template('edit_inventory.html', item=item)  # Pass the item data to the template
    
def get_total_inventory():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as total_inventory FROM inventory")
    total_inventory = cursor.fetchone()['total_inventory']
    cursor.close()
    db.close()
    return total_inventory

# Helper function to get expired items count
def get_expired_items():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as expired_items FROM inventory WHERE expiration_date < CURDATE()")
    expired_items = cursor.fetchone()['expired_items']
    cursor.close()
    db.close()
    return expired_items
def get_total_users():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as total_users FROM users")
    total_users = cursor.fetchone()['total_users']
    cursor.close()
    db.close()
    return total_users
@app.route('/get_inventory')
def get_inventory():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, image, category, description FROM inventory")  # Include 'description'
        items = cursor.fetchall()
        conn.close()
    
        inventory_list = [{"id": row[0], "name": row[1], "price": row[2], "category": row[3], "image": row[4], "description": row[5]} for row in items]  # Add 'description' to the dictionary
        
        print(inventory_list)  # This should print the list if the connection works
        
        return jsonify(inventory_list)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Something went wrong"}), 500


# Helper function to get total number of orders
def get_total_orders():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as total_orders FROM orders")
    total_orders = cursor.fetchone()['total_orders']
    cursor.close()
    db.close()
    return total_orders

@app.route('/inventory/delete/<int:item_id>', methods=['GET'])
def delete_inventory(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete related wishlist entries first
    cursor.execute("DELETE FROM wishlist WHERE product_id = %s", (item_id,))
    
    # Get the image path before deleting the inventory item
    cursor.execute("SELECT image FROM inventory WHERE id = %s", (item_id,))
    image_row = cursor.fetchone()
    
    if image_row:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_row[0])
        if os.path.exists(image_path):
            os.remove(image_path)

    # Delete the inventory item
    cursor.execute("DELETE FROM inventory WHERE id = %s", (item_id,))
    
    conn.commit()
    conn.close()

    return redirect(url_for('inventory_list'))

@app.route('/address')
def address():
    return render_template('address.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        subject = "New Contact Form Submission"
        body = f"Name: {name}\nEmail: {email}\nMessage:\n{message}"

        try:
            msg = Message(subject, recipients=["chandrumvp123@gmail.com"], body=body)
            mail.send(msg)
            flash('Your message has been sent successfully!', 'success')
        except Exception as e:
            flash(f'Error sending message: {str(e)}', 'danger')

        return redirect(url_for('contact'))

    return render_template('contact.html')

@app.route('/edit_order/<int:order_id>', methods=['GET', 'POST'])
def edit_order(order_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        status = request.form['status']
        delivery_date = request.form['delivery_date']
        delivery_date = datetime.strptime(delivery_date, '%Y-%m-%dT%H:%M')

        # Update the order in the database
        cursor.execute("""
            UPDATE orders 
            SET status = %s, delivery_date = %s 
            WHERE order_id = %s
        """, (status, delivery_date, order_id))
        connection.commit()

        # If status is 'Delivered', send an email notification
        if status.lower() == 'delivered':
            cursor.execute("""
                SELECT u.email, u.name, p.name AS product_name, o.order_id
                FROM orders o
                JOIN users u ON o.user_id = u.id
                JOIN inventory p ON o.product_id = p.id
                WHERE o.order_id = %s
            """, (order_id,))
            
            order_info = cursor.fetchone()
            if order_info:
                send_delivery_email(order_info['email'], order_info['name'], order_info['product_name'], order_info['order_id'])

        flash('Order updated successfully!', 'success')
        return redirect(url_for('order_list'))

    # Fetch order details for editing
    cursor.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
    order = cursor.fetchone()

    cursor.close()
    connection.close()

    return render_template('edit_order.html', order=order)

def send_delivery_email(to_email, user_name, product_name, order_id):
    try:
        msg = Message(
            f"Order #{order_id} Delivered!",
            recipients=[to_email]
        )
        msg.body = f"Hello {user_name},\n\nYour order for {product_name} has been successfully delivered!\nThank you for shopping with us.\n\nBest Regards,\nFresh Grocery"
        mail.send(msg)
        print(f"Delivery email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

@app.route('/myorder')
def myorder():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    user_id = session.get('user_id')
    
    print(f"Fetching orders for user ID: {user_id}")

    # Fetch the user's email from the database
    cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    
    if not user_data:
        flash('User not found!', 'danger')
        return redirect(url_for('index'))
    
    user_email = user_data['email']
    print(f"User email from database: {user_email}")

    # Fetching order details with product and status information
    cursor.execute("""
        SELECT 
            o.order_id,
            o.quantity,
            o.total_amount,
            o.sale_date,
            o.delivery_date,
            o.status,
            o.address,
            o.product_id,
            i.name AS product_name,
            i.price AS product_price,
            i.image AS product_image
        FROM orders o
        JOIN inventory i ON o.product_id = i.id
        WHERE o.user_id = %s
        ORDER BY o.sale_date DESC
    """, (user_id,))

    orders = cursor.fetchall()
    print("Fetched orders from DB:", orders)

    # Check if there are any orders before sending an email
    if orders:
        # Check if the latest order is newly placed
        latest_order = orders[0]
        if latest_order['status'] == 'Pending':  # Only send email for new orders
            product_name = latest_order['product_name']
            sale_date = latest_order['sale_date']
            
            # Send a confirmation email to the user's email from the database
            try:
                msg = Message('Order Confirmation - Fresh Groceries',
                              recipients=[user_email])  # Email fetched from the database
                msg.body = f"""
                Dear Customer,

                Your order for '{product_name}' placed on {sale_date} has been successfully processed.
                You will receive your order shortly.

                Thank you for shopping with us!

                Regards,
                Fresh Groceries Team
                """
                mail.send(msg)
                flash('Order confirmation email sent successfully!', 'success')
            except Exception as e:
                print("Error sending email:", e)
                flash('Failed to send order confirmation email.', 'danger')
    else:
        flash('No orders found.', 'info')  # Show a message when there are no orders

    cursor.close()
    db.close()

    return render_template('myorder.html', orders=orders)


@app.route('/user_order_list')
def order_list():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Fetch orders with product and user names
        cursor.execute("""
            SELECT 
                o.order_id, 
                u.name AS user_name, 
                p.name AS product_name, 
                o.total_amount, 
                o.status 
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN inventory p ON o.product_id = p.id
        """)
        
        orders = cursor.fetchall()
        if not orders:
            print("No orders found.")
        else:
            print("Fetched Orders:", orders)

        return render_template('order_list.html', orders=orders)

    except Exception as e:
        print(f"Error fetching orders: {e}")
        return "An error occurred while fetching orders.", 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/profile')
def profile():
    if 'email' not in session:
        return redirect(url_for('login')) 

    try:
      
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = "SELECT name, email, number FROM users WHERE email = %s"
        cursor.execute(query, (session['email'],)) 
        user = cursor.fetchone()

        if not user:
            return "User not found", 404 

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return "Failed to fetch user details", 500  

    finally:
      
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


    return render_template('profile.html', user=user)




def send_order_confirmation_email(recipient_email, order_details):
    try:
        msg = Message(
            "Order Confirmation - Fresh Groceries",
            recipients=[recipient_email]
        )
        msg.body = f"Your order {order_details} has been placed successfully!"
        mail.send(msg)
        flash("Order confirmed successfully!", "success")  # Use flash with category 'success'
        print("Email sent successfully!")
    except Exception as e:
        print("Error sending email:", e)
        flash("Failed to send order confirmation email.", "danger")

@app.route('/admin/manage-stock')
def manage_stock():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name AS product_name, stock FROM inventory")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('manage_stock.html', products=products)

@app.route('/admin/update-stock', methods=['POST'])
def update_stock():
    product_id = request.form.get('product_id')
    new_stock = request.form.get('new_stock')

    if not product_id or not new_stock.isdigit():
        flash('Invalid stock value', 'error')
        return redirect(url_for('manage_stock'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE inventory SET stock = %s WHERE id = %s", (new_stock, product_id))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Stock updated successfully', 'success')
    return redirect(url_for('manage_stock'))

@app.route('/cart')
def cart():
    if 'email' not in session:
        return redirect(url_for('login'))
    cart_items = session.get('cart', [])
    print("Session Cart Data:", session.get('cart'))

    return render_template('cart.html', cart=cart_items)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    try:
        print(f"Attempting to add product ID: {product_id} to cart...")

        if 'cart' not in session or not isinstance(session['cart'], list):
            session['cart'] = []
        cart = session['cart']

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch product by ID and check stock availability
        cursor.execute("SELECT * FROM inventory WHERE id = %s", (product_id,))
        product = cursor.fetchone()

        if not product:
            print(f"Product ID {product_id} not found in the database.")
            flash('Product not found!', 'danger')
            return redirect(url_for('index'))

        available_stock = product.get('stock', 0)
        quantity = request.form.get('quantity', 1)

        if not quantity or not str(quantity).isdigit():
            print("Invalid quantity provided:", quantity)
            flash('Invalid quantity!', 'danger')
            return redirect(url_for('index'))

        quantity = int(quantity)
        
        # Check if requested quantity exceeds available stock
        if quantity > available_stock:
            flash(f"Only {available_stock} items available in stock!", 'warning')
            return redirect(url_for('index'))

        for item in cart:
            if item['id'] == product_id:
                if item['quantity'] + quantity > available_stock:
                    flash(f"Only {available_stock} items available in stock!", 'warning')
                    return redirect(url_for('index'))
                item['quantity'] += quantity
                break
        else:
            cart.append({
                'id': product.get('id'),
                'name': product.get('name', product.get('product_name', 'Unknown Product')),
                'product_name': product.get('product_name', product.get('name', 'Unknown Product')),
                'quantity': quantity,
                'price': product.get('price', 0.0),
                'expiration_date': product.get('expiration_date', 'N/A'),
                'image': product.get('image', 'default.jpg')
            })

        session['cart'] = cart
        session.modified = True
        print("Cart updated:", session['cart'])

        flash(f"{product.get('product_name', 'Product')} added to cart!", 'success')
        return redirect(url_for('index'))

    except Exception as e:
        print(f"An error occurred while adding to cart: {e}")
        flash('Error adding product to cart.', 'danger')
        return redirect(url_for('index'))

@app.route('/remove_from_cart/<string:item_name>', methods=['POST'])
def remove_from_cart(item_name):
    try:
        print(f"Removing item: {item_name} from cart...")
        cart = session.get('cart', [])
        
        # Filter out the item by its name
        cart = [item for item in cart if item['product_name'] != item_name]
        
        session['cart'] = cart
        session.modified = True
        flash(f"{item_name} removed from cart.", 'success')
        return redirect(url_for('cart'))
    
    except Exception as e:
        print(f"An error occurred while removing from cart: {e}")
        flash('Error removing item from cart.', 'danger')
        return redirect(url_for('cart'))


@app.route('/checkout', methods=['POST'])
def checkout():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    try:
        print("Checkout process started...")
        
        cart = session.get('cart', [])
        
        if not cart:
            flash('Your cart is empty!', 'warning')
            return redirect(url_for('cart'))
        
        address = request.form.get('address')
        
        if not address:
            flash('Address is required!', 'warning')
            return redirect(url_for('cart'))
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        user_id = session.get('user_id')
        
        for item in cart:
            product_id = item['id']
            quantity = item['quantity']
            total_amount = float(item['price']) * quantity
            
            print(f"Processing product ID: {product_id} with quantity: {quantity}")
            
            cursor.execute("SELECT stock FROM inventory WHERE id = %s", (product_id,))
            stock_data = cursor.fetchone()
            available_stock = stock_data['stock'] if stock_data else 0
            
            if quantity > available_stock:
                flash(f"Not enough stock for {item['product_name']}!", 'danger')
                return redirect(url_for('cart'))
            
            cursor.execute(
                "INSERT INTO orders (product_id, quantity, total_amount, user_id, address, status) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (product_id, quantity, total_amount, user_id, address, 'Pending')
            )
            
            # Reduce stock after purchase
            cursor.execute("UPDATE inventory SET stock = stock - %s WHERE id = %s", (quantity, product_id))
            db.commit()
        
        session['cart'] = []
        session.modified = True
        
        flash('Checkout successful!', 'success')
        return redirect(url_for('myorder'))
    
    except Exception as e:
        print(f"An error occurred during checkout: {e}")
        flash('Error during checkout process.', 'danger')
        return redirect(url_for('cart'))

@app.route('/sales_report')
def sales_report():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # 🧮 **Revenue Calculation:**  
    cursor.execute("SELECT SUM(total_amount) AS total_revenue FROM orders WHERE status = 'Delivered'")
    total_revenue = cursor.fetchone().get('total_revenue', 0)

    # 📈 **Top-Selling Products:**  
    cursor.execute("""
        SELECT i.name AS product_name, SUM(o.quantity) AS total_quantity, SUM(o.total_amount) AS total_sales
        FROM orders o
        JOIN inventory i ON o.product_id = i.id
        WHERE o.status = 'Delivered'
        GROUP BY i.name
        ORDER BY total_quantity DESC
        LIMIT 5
    """)
    top_products = cursor.fetchall()

    # 📅 **Order Trends (Monthly):**  
    cursor.execute("""
        SELECT DATE_FORMAT(sale_date, '%Y-%m') AS month, SUM(total_amount) AS monthly_sales
        FROM orders
        WHERE status = 'Delivered'
        GROUP BY month
        ORDER BY month DESC
        LIMIT 12
    """)
    order_trends = cursor.fetchall()

    cursor.close()
    db.close()
    

    return render_template('sales_report.html', 
                           total_revenue=total_revenue, 
                           top_products=top_products, 
                           order_trends=order_trends)

@app.route('/wishlist', methods=['GET'])
def wishlist():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT inventory.id, inventory.name AS product_name, inventory.image, inventory.description, inventory.price 
        FROM wishlist 
        JOIN inventory ON wishlist.product_id = inventory.id 
        WHERE wishlist.user_id = %s
    """, (user_id,))
    
    wishlist_products = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('wishlist.html', wishlist_products=wishlist_products)
@app.route('/add_to_wishlist/<int:product_id>', methods=['POST'])
def add_to_wishlist(product_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Check if the product is already in the wishlist
    cursor.execute(
        "SELECT COUNT(*) as count FROM wishlist WHERE product_id = %s AND user_id = %s",
        (product_id, user_id)
    )
    result = cursor.fetchone()

    if result["count"] > 0:
        # Remove from wishlist
        cursor.execute(
            "DELETE FROM wishlist WHERE product_id = %s AND user_id = %s",
            (product_id, user_id)
        )
    else:
        # Add to wishlist
        cursor.execute(
            "INSERT INTO wishlist (user_id, product_id) VALUES (%s, %s)",
            (user_id, product_id)
        )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('index'))  # Redirect back to home page

@app.route('/remove_from_wishlist/<int:product_id>', methods=['POST'])
def remove_from_wishlist(product_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "DELETE FROM wishlist WHERE product_id = %s AND user_id = %s",
        (product_id, user_id)
    )
    conn.commit()
    
    cursor.close()
    conn.close()

    flash("Item removed from wishlist", "success")
    return redirect(url_for('wishlist'))


@app.route('/admin/reviews')
def admin_reviews():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)  # Use dictionary=True to get column names as keys
    cursor.execute("""
        SELECT r.id AS review_id, r.product_id, r.user AS user_email, 
               r.content, r.rating
        FROM reviews r
    """)
    reviews = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('admin_reviews.html', reviews=reviews)


# Route to edit a review
@app.route('/edit_review/<int:review_id>', methods=['POST'])
def edit_review(review_id):
    content = request.form['content']
    rating = request.form['rating']
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('UPDATE reviews SET content = %s, rating = %s WHERE id = %s',
                   (content, rating, review_id))
    connection.commit()
    connection.close()
    flash('Review updated successfully!', 'success')
    return redirect(url_for('admin_reviews'))

# Route to delete a review
@app.route('/delete_review/<int:review_id>', methods=['POST'])
def delete_review(review_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('DELETE FROM reviews WHERE id = %s', (review_id,))
    connection.commit()
    connection.close()
    flash('Review deleted successfully!', 'danger')
    return redirect(url_for('admin_reviews'))

def fetch_reviews_from_db():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM reviews')
    reviews = cursor.fetchall()
    conn.close()
    return reviews

@app.route('/logout')
def logout():
    session.pop('email', None)  # Remove the session variable
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/cancel_order/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    user_id = session.get('user_id')

    # Fetch the order and validate ownership
    cursor.execute("""
        SELECT o.order_id, o.status, o.product_id, o.quantity, i.name AS product_name, u.email 
        FROM orders o 
        JOIN inventory i ON o.product_id = i.id 
        JOIN users u ON o.user_id = u.id 
        WHERE o.order_id = %s AND o.user_id = %s
    """, (order_id, user_id))
    
    order = cursor.fetchone()

    if not order:
        flash('Order not found or access denied!', 'danger')
        return redirect(url_for('myorder'))
    
    if order['status'] in ['Delivered', 'Cancelled']:
        flash('Order cannot be cancelled as it is already delivered or cancelled!', 'warning')
        return redirect(url_for('myorder'))

    # Update the order status to 'Cancelled' in the database
    try:
        cursor.execute("""
            UPDATE orders SET status = 'Cancelled', delivery_date = %s WHERE order_id = %s
        """, (datetime.now(), order_id))
        db.commit()

        flash('Order cancelled successfully!', 'success')

        # Send cancellation email to the user
        try:
            msg = Message('Order Cancellation - Fresh Groceries',
                          recipients=[order['email']])
            msg.body = f"""
            Dear Customer,

            Your order for '{order['product_name']}' has been cancelled successfully.

            If you have any questions, please contact our support team.

            Regards,
            Fresh Groceries Team
            """
            mail.send(msg)
            flash('Cancellation email sent successfully!', 'success')
        except Exception as e:
            print("Error sending email:", e)
            flash('Failed to send cancellation email.', 'danger')

    except Exception as e:
        db.rollback()
        flash('Failed to cancel the order. Please try again.', 'danger')
        print("Error updating order status:", e)

    cursor.close()
    db.close()
    
    return redirect(url_for('myorder'))

@app.route('/send-email', methods=['POST'])
def send_email():
    try:
        data = request.get_json()

        name = data.get('name')
        number = data.get('number')
        email = data.get('email')
        medicine = data.get('medicine')
        cost = data.get('cost')

    
        connection = get_db_connection()
        cursor = connection.cursor()

  
        cursor.execute("""
            INSERT INTO sales (name, number, email, medicine, cost)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, number, email, medicine, cost))

 
        connection.commit()

       
        cursor.close()
        connection.close()

        subject = "Billing Details"
        body = f"""
        Dear {name},

        Here are your billing details:

        - Name: {name}
        - Number: {number}
        - Medicine Name: {medicine}
        - Cost: ₹{cost}

        Regards,
        Horsonda Pharmacy
        """

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())
            server.quit()

            return jsonify({"status": "success", "message": "Email sent successfully and sale saved!"})

        except Exception as e:
            return jsonify({"status": "error", "message": f"Email failed to send: {str(e)}"})

    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to save sale: {str(e)}"})


def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


@app.route('/get-total-inventory', methods=['GET'])
def get_total_inventory():
    try:
      
        connection = get_db_connection()
        cursor = connection.cursor()

     
        cursor.execute("SELECT COUNT(*) FROM inventory")
        result = cursor.fetchone()

       
        cursor.close()
        connection.close()

   
        return jsonify({"total_inventory": result[0]})

    except Exception as e:
        print("Error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)
