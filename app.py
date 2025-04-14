from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from werkzeug.utils import secure_filename

import datetime
from datetime import datetime, date

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
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

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)
