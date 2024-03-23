from flask import Flask, render_template, request, redirect, url_for, session
import os
import mysql.connector
from mysql.connector import Error

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

def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='dbms',  
            database='hi'
        )
        if connection.is_connected():
            print('Connected to MySQL database')
            return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

# Homepage with login and signup buttons
@app.route('/')
def index():
    if 'username' in session:
        username = session['username']
    else:
        username = None
    cursor = mysql_connection.cursor()
    cursor.execute('SELECT username FROM users')
    users = cursor.fetchall()
    cursor.close()
    return render_template('upload.html', users=users, username=username)

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

    if user:
        session['username'] = username  # Store username in session

        cursor.close()
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
    cursor = mysql_connection.cursor()
    cursor.execute('SELECT * FROM orders WHERE usn = %s', (username,))
    orders = cursor.fetchall()
    cursor.close()
    return render_template('user_home.html', username=username, orders=orders)

# Logout route
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)  # Remove username from session
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        usn = request.form['usn']
        
        # Handle file upload
        pdf_file = request.files['file']
        if pdf_file.filename == '':
            return 'No file selected', 400
        
        # Save the uploaded file to the 'pdf' folder
        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
        pdf_file.save(pdf_path)
        
        # Handle form fields gracefully
        num_pages = request.form.get('hidden_num_pages', '0')
        num_copies = request.form.get('num_copies', '0')
        page_numbers_to_print = request.form.get('all_pages', 'all') if request.form.get('all_pages') else request.form.get('start_page', '') + '-' + request.form.get('end_page', '')
        color_page_numbers = request.form.get('all_pages_color', 'all') if request.form.get('all_pages_color') else request.form.get('start_pages', '') + '-' + request.form.get('end_pages', '')
        soft_bind = 'yes' if request.form.get('soft_bind') else 'no'
        back_to_back = 'yes' if request.form.get('back_to_back') else 'no'
        description = request.form.get('description', '')

        total_cost = request.form.get('total_cost', '0.00')

        # Store data in MySQL
        connection = connect_to_database()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("INSERT INTO orders (usn, pdf_file, num_pages, num_copies, page_numbers_to_print, color_page_numbers, soft_bind, back_to_back, description, total_cost) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                               (usn, pdf_file.filename, num_pages, num_copies, page_numbers_to_print, color_page_numbers, soft_bind, back_to_back, description, total_cost))
                connection.commit()
                cursor.close()
                print("Data inserted successfully into MySQL database")
            except Error as e:
                print(f"Error inserting data into MySQL database: {e}")
            finally:
                if connection.is_connected():
                    connection.close()
                    print('MySQL connection closed')
        else:
            print("Failed to connect to MySQL database")

        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
