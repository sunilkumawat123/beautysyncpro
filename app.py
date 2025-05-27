import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# MySQL configurations
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
mysql = MySQL(app)

# Email configurations
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Simplified AI scheduler
def suggest_schedule(services, preferred_date):
    available_slots = [
        {"service": "Facial", "salon": "BeautyBliss Spa", "time": "10:00 AM"},
        {"service": "Haircut", "salon": "Lookz Salon", "time": "11:30 AM"},
        {"service": "Waxing", "salon": "GlowUp Studio", "time": "1:00 PM"},
        {"service": "Manicure", "salon": "GlowUp Studio", "time": "2:30 PM"}
    ]
    return [slot for slot in available_slots if slot["service"] in services]

# Send confirmation email
def send_confirmation_email(user_email, booking_details):
    msg = MIMEText(f"Your booking is confirmed!\nDetails:\n{booking_details}")
    msg['Subject'] = 'BeautySyncPro Booking Confirmation'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = user_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, user_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

# User Routes
@app.route('/user/register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", 
                       (name, email, password))
            mysql.connection.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('user_login'))
        except:
            flash('Email already exists!', 'danger')
        finally:
            cur.close()
    return render_template('user_register.html')

@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", 
                   (email, password))
        user = cur.fetchone()
        cur.close()
        
        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_type'] = 'user'
            flash('Login successful!', 'success')
            return redirect(url_for('user_booking'))
        else:
            flash('Invalid credentials!', 'danger')
    return render_template('user_login.html')

@app.route('/user/booking', methods=['GET', 'POST'])
def user_booking():
    if 'user_id' not in session or session['user_type'] != 'user':
        flash('Please log in as a user to book services.', 'danger')
        return redirect(url_for('user_login'))
    
    if request.method == 'POST':
        services = request.form.getlist('services')
        preferred_date = request.form['preferred_date']
        email = request.form['email']
        
        # Get AI-suggested schedule
        schedule = suggest_schedule(services, preferred_date)
        
        # Save booking to database
        cur = mysql.connection.cursor()
        booking_details = f"Services: {', '.join(services)}, Date: {preferred_date}"
        cur.execute("INSERT INTO bookings (user_id, services, booking_date, details, status) VALUES (%s, %s, %s, %s, %s)",
                   (session['user_id'], ','.join(services), preferred_date, booking_details, 'pending'))
        booking_id = cur.lastrowid
        mysql.connection.commit()
        cur.close()
        
        # Send confirmation email
        send_confirmation_email(email, booking_details)
        
        return render_template('user_confirmation.html', schedule=schedule, details=booking_details)
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM salons")
    salons = cur.fetchall()
    cur.close()
    
    return render_template('user_booking.html', salons=salons)

# Vendor Routes
@app.route('/vendor/register', methods=['GET', 'POST'])
def vendor_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        salon_name = request.form['salon_name']
        location = request.form['location']
        
        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO vendors (name, email, password) VALUES (%s, %s, %s)", 
                       (name, email, password))
            vendor_id = cur.lastrowid
            cur.execute("INSERT INTO salons (vendor_id, name, location) VALUES (%s, %s, %s)",
                       (vendor_id, salon_name, location))
            mysql.connection.commit()
            flash('Vendor registration successful! Please log in.', 'success')
            return redirect(url_for('vendor_login'))
        except:
            flash('Email already exists!', 'danger')
        finally:
            cur.close()
    return render_template('vendor_register.html')

@app.route('/vendor/login', methods=['GET', 'POST'])
def vendor_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM vendors WHERE email = %s AND password = %s", 
                   (email, password))
        vendor = cur.fetchone()
        cur.close()
        
        if vendor:
            session['vendor_id'] = vendor[0]
            session['vendor_name'] = vendor[1]
            session['user_type'] = 'vendor'
            flash('Login successful!', 'success')
            return redirect(url_for('vendor_dashboard'))
        else:
            flash('Invalid credentials!', 'danger')
    return render_template('vendor_login.html')

@app.route('/vendor/dashboard')
def vendor_dashboard():
    if 'vendor_id' not in session or session['user_type'] != 'vendor':
        flash('Please log in as a vendor to access the dashboard.', 'danger')
        return redirect(url_for('vendor_login'))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT b.* FROM bookings b JOIN salons s ON b.services LIKE CONCAT('%', s.name, '%') WHERE s.vendor_id = %s",
               (session['vendor_id'],))
    bookings = cur.fetchall()
    cur.close()
    
    return render_template('vendor_dashboard.html', bookings=bookings)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)