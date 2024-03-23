from flask import Flask, render_template, request, redirect, url_for, session
import os
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Set a secret key for session management

# Define the folder where PDF files will be saved
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'pdf')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# MySQL Configuration
mysql_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="dbms",
    database="hi"
)

# Create a MySQL table for users if not exists
def create_table():
    cursor = mysql_connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (id INT AUTO_INCREMENT PRIMARY KEY,
                       username VARCHAR(255) NOT NULL,
                       password VARCHAR(255) NOT NULL)''')
    mysql_connection.commit()
    cursor.close()

create_table()

# Homepage with login and signup buttons
@app.route('/')
def index():
    cursor = mysql_connection.cursor()
    cursor.execute('SELECT username FROM users')
    users = cursor.fetchall()
    cursor.close()
    return render_template('history.html', users=users)

# Login page
@app.route('/login')
def login():
    return render_template('login.html')

# Signup page
@app.route('/signup')
def signup():
    return render_template('signup.html')

# Handling login form submission
@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']

    cursor = mysql_connection.cursor()
    cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
    user = cursor.fetchone()
    cursor.close()

    if user:
        session['username'] = username  # Store username in session
        return redirect(url_for('user_home', username=username))
    else:
        return 'Invalid username or password'

# Handling signup form submission
@app.route('/signup', methods=['POST'])
def signup_post():
    username = request.form['username']
    password = request.form['password']

    cursor = mysql_connection.cursor()
    cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, password))
    mysql_connection.commit()
    cursor.close()

    return redirect(url_for('login'))

# User homepage
@app.route('/user/<username>')
def user_home(username):
    return render_template('user_home.html', username=username)

# Logout route
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)  # Remove username from session
    return redirect(url_for('index'))

# Handling orders retrieval
@app.route('/get_orders', methods=['POST'])
def retrieve_orders():
    usn = request.form['usn']
    orders = get_orders(usn)
    return render_template('orders.html', orders=orders)

# Function to get orders from MySQL database
def get_orders(usn):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",  # Replace with your MySQL username
        password="dbms",  # Replace with your MySQL password
        database="hi"
    )

    mycursor = mydb.cursor(dictionary=True)
    mycursor.execute("SELECT * FROM orders WHERE usn = %s", (usn,))
    orders = mycursor.fetchall()
    mydb.close()

    return orders

if __name__ == '__main__':
    app.run(debug=True, port=1000)
