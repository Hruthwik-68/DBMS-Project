from flask import Flask, render_template, request, redirect, url_for, session
import uuid
import os
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  


# Define the folder where PDF files will be saved
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'pdf')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# MySQL Configuration
mysql_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="prajwaltp",
    database="retail_shop"
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

#create_table()

def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='prajwaltp',  
            database='retail_shop'
        )
        if connection.is_connected():
            print('Connected to MySQL database')
            return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None
    
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload')
def upload_page():
    if 'username' in session:
        return render_template('upload.html')
    else:
        return redirect(url_for('login'))

# Homepage with login and signup buttons
@app.route('/upload')
def index_main():
    if 'username' in session:
        username = session['username']
    else:
        username = None
    cursor = mysql_connection.cursor()
    cursor.execute('SELECT usn FROM users')
    users = cursor.fetchall()
    cursor.close()
    return render_template('upload.html', users=users, username=username)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        usn = request.form['usn']
        email = request.form['email']
        password = request.form['password']
        security_question = request.form['security_question']
        security_answer = request.form['security_answer']

        connection = connect_to_database()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM users WHERE usn = %s", (usn,))
                user = cursor.fetchone()
                if user:
                    return render_template('login.html', message="User already exists. Please login.")
                else:
                    cursor.execute("INSERT INTO users (usn, email, password, security_question, security_answer) VALUES (%s, %s, %s, %s, %s)",
                                   (usn, email, password, security_question, security_answer))
                    connection.commit()
                    session['username'] = usn
                    cursor.close()
                    return redirect(url_for('index', username=usn))
            except Error as e:
                print(f"Error inserting data into MySQL database: {e}")
            finally:
                if connection.is_connected():
                    connection.close()
                    print('MySQL connection closed')
        else:
            print("Failed to connect to MySQL database")

    return render_template('signup.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    session['username'] = None
    if request.method == 'POST':
        usn = request.form['usn']
        password = request.form['password']

        connection = connect_to_database()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM users WHERE usn = %s AND password = %s", (usn, password))
                user = cursor.fetchone()
                if user:
                    session['username'] = usn
                    cursor.close()
                    return redirect(url_for('index', username=usn))
                else:
                    return render_template('login.html', message="Invalid credentials. Please try again.")
            except Error as e:
                print(f"Error selecting data from MySQL database: {e}")
            finally:
                if connection.is_connected():
                    connection.close()
                    print('MySQL connection closed')
        else:
            print("Failed to connect to MySQL database")

    return render_template('login.html')

# Forgot password route
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        usn = request.form['usn']
        security_answer = request.form['security_answer']

        connection = connect_to_database()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT security_question, security_answer FROM users WHERE usn = %s", (usn,))
                data = cursor.fetchone()
                if data:
                    correct_answer = data[1]
                    if security_answer == correct_answer:
                        return render_template('update_password.html', usn=usn)
                    else:
                        return render_template('forgot_password.html', message="Incorrect security answer. Please try again.")
                else:
                    return render_template('forgot_password.html', message="User not found.")
            except Error as e:
                print(f"Error selecting data from MySQL database: {e}")
            finally:
                if connection.is_connected():
                    connection.close()
                    print('MySQL connection closed')
        else:
            print("Failed to connect to MySQL database")

    return render_template('forgot_password.html')

# Update password route
@app.route('/update_password', methods=['POST'])
def update_password():
    if request.method == 'POST':
        usn = request.form['usn']
        new_password = request.form['new_password']

        connection = connect_to_database()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("UPDATE users SET password = %s WHERE usn = %s", (new_password, usn))
                connection.commit()
                cursor.close()
                return redirect(url_for('login', message="Password updated successfully. Please login with your new password."))
            except Error as e:
                print(f"Error updating password in MySQL database: {e}")
            finally:
                if connection.is_connected():
                    connection.close()
                    print('MySQL connection closed')
        else:
            print("Failed to connect to MySQL database")

    return redirect(url_for('index'))


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
    session.pop('username', None)  
    return redirect(url_for('index'))

def generate_order_number():
    # Get the latest order number from the database and increment it
    return "ORD_" + str(uuid.uuid4())[:3].upper()

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':

        usn = session.get('username')

        order_number = generate_order_number()

        session['order_number'] = order_number
        
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
                cursor.execute("INSERT INTO orders (order_number, usn, pdf_file, num_pages, num_copies, page_numbers_to_print, color_page_numbers, soft_bind, back_to_back, description, total_cost) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                               (order_number, usn, pdf_file.filename, num_pages, num_copies, page_numbers_to_print, color_page_numbers, soft_bind, back_to_back, description, total_cost))

                connection.commit()
                session['total_cost'] = total_cost
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

        return redirect(url_for('payment', order_number = order_number))
    
def get_total_cost(order_number):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT total_cost FROM orders WHERE order_number = %s", (order_number,))
            total_cost = cursor.fetchone()[0]  # Assuming total_cost is the first column
            cursor.close()
            connection.close()
            return total_cost
        except mysql.connector.Error as e:
            print(f"Error fetching total cost from database: {e}")
            return None
    else:
        return None

@app.route('/payment')
def payment():
    if 'order_number' in session:
        order_number = session['order_number']
        total_cost = get_total_cost(order_number)  
        return render_template('payment.html', total_cost=total_cost)
    else:
        # Redirect to login page if order number is not in session
        return redirect(url_for('login'))
    
@app.route('/process_payment', methods=['POST'])
def process_payment():
    # Retrieve data from form submission or session
    usn = session['username']
    order_number = session['order_number']
    total_cost = session['total_cost']
    utr = request.form.get('utr')

    # Establish database connection
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor()
            # Execute SQL INSERT statement
            cursor.execute("INSERT INTO payments (usn, order_number, transaction_id,total_cost) VALUES (%s, %s, %s,%s)",
                           (usn, order_number, utr,total_cost))
            connection.commit()
            cursor.close()
            return redirect(url_for('payment_success'))
        except Exception as e:
            print("Error inserting data into payments table:", e)
            return "Error inserting data into payments table"
        finally:
            if connection.is_connected():
                connection.close()
                print('Database connection closed')
    else:
        print("Failed to connect to database")

    return redirect(url_for('payment_failure'))


@app.route('/payment_success')
def payment_success():
    return render_template('payment_success.html')


@app.route('/order_history/<usn>')
def order_history(usn):
    # Connect to the database
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            # Execute SQL query to retrieve order history based on USN
            query = "SELECT * FROM orders WHERE usn = %s"
            cursor.execute(query, (usn,))
            orders = cursor.fetchall()
            return render_template('order_history.html', orders=orders, username=usn)
        except mysql.connector.Error as e:
            print("Error fetching order history:", e)
        finally:
            cursor.close()
            connection.close()
            print("Database connection closed")
    return "Failed to fetch order history"


if __name__ == '__main__':
    app.run(debug=True, port=5000)
