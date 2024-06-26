from flask import Flask, render_template, send_file, redirect, url_for, request,session
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

app.secret_key = 'iwebvbgsdjlfgv: TF:gai:GFAI:UGF'

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
    
def authenticate_user(username, password):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT password FROM admin WHERE admin_id = %s", (username,))
            result = cursor.fetchone()
            if result and result[0] == password:
                return True
        except Error as e:
            print(f"Error retrieving data from MySQL database: {e}")
        finally:
            if connection.is_connected():
                connection.close()
    return False

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if authenticate_user(username, password):
            session['logged_in'] = True
            return redirect(url_for('show_details'))
        else:
            return render_template('login1.html', message='Invalid username or password')

    return render_template('login1.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/show_details')
def show_details():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM orders")
            orders = cursor.fetchall()
            return render_template('show_details.html', orders=orders)
        except Error as e:
            print(f"Error retrieving data from MySQL database: {e}")
        finally:
            if connection.is_connected():
                connection.close()
                print('MySQL connection closed')
    else:
        print("Failed to connect to MySQL database")
        return "Failed to connect to MySQL database"

@app.route('/download/<filename>')
def download_pdf(filename):
    file_path = f"C:\\Users\\PRAJWAL T P\\Desktop\\DBMS-Project\\Xerox\\pdf\\"+filename  # Corrected file path
    return send_file(file_path, as_attachment=True)

@app.route('/delete/<int:order_id>')
def delete_order(order_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
            connection.commit()
            print("Order deleted successfully from database")
        except Error as e:
            print(f"Error deleting order from database: {e}")
        finally:
            if connection.is_connected():
                connection.close()
                print('MySQL connection closed')
    else:
        print("Failed to connect to MySQL database")

    return redirect(url_for('show_details'))

@app.route('/update_status', methods=['POST'])
def update_status():
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        status = request.form.get('status')

        connection = connect_to_database()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("UPDATE orders SET status = %s WHERE id = %s", (status, order_id))
                connection.commit()
                print("Status updated successfully in database")
            except Error as e:
                print(f"Error updating status in database: {e}")
            finally:
                if connection.is_connected():
                    connection.close()
                    print('MySQL connection closed')
        else:
            print("Failed to connect to MySQL database")

    return redirect(url_for('show_details'))

if __name__ == '__main__':
    app.run(debug=True, port=3000)
