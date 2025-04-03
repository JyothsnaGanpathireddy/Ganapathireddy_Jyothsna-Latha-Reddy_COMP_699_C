from flask import Flask, request, render_template
from werkzeug.security import check_password_hash

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, Flask!"

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
    app.run(debug=True)
