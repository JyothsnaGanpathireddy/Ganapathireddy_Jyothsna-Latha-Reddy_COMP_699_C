from flask import Flask, request, render_template

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

if __name__ == '__main__':
    app.run(debug=True)
