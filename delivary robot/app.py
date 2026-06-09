from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_db, get_db_connection, generate_pin
from telegram_bot import telegram_bot
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Initialize database
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                (username, email, hashed_password)
            )
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'error')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    user = conn.execute(
        'SELECT wallet_balance FROM users WHERE id = ?', (session['user_id'],)
    ).fetchone()
    
    # Get cart count
    cart_count = conn.execute(
        'SELECT COUNT(*) FROM cart WHERE user_id = ? AND is_verified = FALSE',
        (session['user_id'],)
    ).fetchone()[0]
    conn.commit()
    conn.close()
    
    return render_template('dashboard.html', 
                         products=products, 
                         user=user, 
                         cart_count=cart_count)

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Check if product already in cart (not verified)
    existing_item = conn.execute(
        'SELECT * FROM cart WHERE user_id = ? AND product_id = ? AND is_verified = FALSE',
        (session['user_id'], product_id)
    ).fetchone()
    
    if existing_item:
        flash('Item already in cart!', 'warning')
    else:
        # Get product details
        product = conn.execute(
            'SELECT * FROM products WHERE id = ?', (product_id,)
        ).fetchone()
        
        # Generate PIN
        pin_code = generate_pin()
        
        # Add to cart
        conn.execute(
            'INSERT INTO cart (user_id, product_id, pin_code, pin_generated_at) VALUES (?, ?, ?, ?)',
            (session['user_id'], product_id, pin_code, datetime.now())
        )
        
        if product['rfid_number'] == '10005F071850':
            num = 'A'
        
        if product['rfid_number'] == '0F008A88C5C8':
            num = 'B'

        if product['rfid_number'] == '1000476B80BC':
            num = 'C'

        if product['rfid_number'] == '12000F0F2D3F':
            num = 'D'
        from serial_test import Send
        Send(num)

        # Send Telegram notification
        telegram_bot.send_pin_notification(
            session['username'],
            product['name'],
            pin_code
        )
        
        conn.commit()
        flash(f'{product["name"]} added to cart! PIN sent to delivery team.', 'success')
    
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cart_items = conn.execute('''
        SELECT c.*, p.name, p.price, p.rfid_number, p.image_path 
        FROM cart c 
        JOIN products p ON c.product_id = p.id 
        WHERE c.user_id = ? AND c.is_verified = FALSE
    ''', (session['user_id'],)).fetchall()
    
    total_amount = sum(item['price'] for item in cart_items)
    user = conn.execute(
        'SELECT wallet_balance FROM users WHERE id = ?', (session['user_id'],)
    ).fetchone()
    
    conn.close()
    
    return render_template('cart.html', 
                         cart_items=cart_items, 
                         total_amount=total_amount, 
                         user=user)

@app.route('/remove_from_cart/<int:cart_id>')
def remove_from_cart(cart_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute(
        'DELETE FROM cart WHERE id = ? AND user_id = ?', 
        (cart_id, session['user_id'])
    )
    conn.commit()
    conn.close()
    
    flash('Item removed from cart!', 'success')
    return redirect(url_for('cart'))

@app.route('/verify_pin', methods=['GET', 'POST'])
def verify_pin():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        pin_code = request.form['pin_code']
        
        conn = get_db_connection()
        
        # Find cart item with this PIN
        cart_item = conn.execute('''
            SELECT c.*, p.name, p.price, p.rfid_number 
            FROM cart c 
            JOIN products p ON c.product_id = p.id 
            WHERE c.user_id = ? AND c.pin_code = ? AND c.is_verified = FALSE
        ''', (session['user_id'], pin_code)).fetchone()
        
        if cart_item:
            # Check wallet balance
            user = conn.execute(
                'SELECT wallet_balance FROM users WHERE id = ?', 
                (session['user_id'],)
            ).fetchone()
            
            if user['wallet_balance'] >= cart_item['price']:
                # Process payment
                new_balance = user['wallet_balance'] - cart_item['price']
                conn.execute(
                    'UPDATE users SET wallet_balance = ? WHERE id = ?',
                    (new_balance, session['user_id'])
                )
                
                # Record transaction
                conn.execute(
                    'INSERT INTO transactions (user_id, product_id, amount, pin_code) VALUES (?, ?, ?, ?)',
                    (session['user_id'], cart_item['product_id'], cart_item['price'], pin_code)
                )
                
                # Mark as verified
                conn.execute(
                    'UPDATE cart SET is_verified = TRUE WHERE id = ?',
                    (cart_item['id'],)
                )
                
                from serial_test import Send
                Send('S')
                
                # Send success notification to Telegram
                telegram_bot.send_pin_verification(
                    session['username'],
                    cart_item['name'],
                    pin_code, 
                    True
                )
                
                conn.commit()
                conn.close()
                
                flash('PIN verified successfully! Item delivered.', 'success')
                return redirect(url_for('success'))
            else:
                conn.close()

                from serial_test import Send
                Send('F')

                # Send failed notification to Telegram
                telegram_bot.send_pin_verification(
                    session['username'],
                    cart_item['name'],
                    pin_code,
                    False
                )
                flash('Insufficient balance!', 'error')
        else:
            conn.close()
            # Send failed notification to Telegram for wrong PIN
            telegram_bot.send_pin_verification(
                session['username'],
                "Unknown Product",
                pin_code,
                False
            )
            flash('Invalid PIN! Please try again.', 'error')
    
    return render_template('pin_verification.html')

@app.route('/success')
def success():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('success.html')

@app.route('/wallet', methods=['GET', 'POST'])
def wallet():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        amount = float(request.form['amount'])
        
        # Update wallet balance
        user = conn.execute(
            'SELECT wallet_balance FROM users WHERE id = ?', (session['user_id'],)
        ).fetchone()
        
        new_balance = user['wallet_balance'] + amount
        conn.execute(
            'UPDATE users SET wallet_balance = ? WHERE id = ?',
            (new_balance, session['user_id'])
        )
        conn.commit()
        flash(f'₹{amount} added to wallet successfully!', 'success')
    
    user = conn.execute(
        'SELECT wallet_balance FROM users WHERE id = ?', (session['user_id'],)
    ).fetchone()
    
    # Get cart count
    cart_count = conn.execute(
        'SELECT COUNT(*) FROM cart WHERE user_id = ? AND is_verified = FALSE',
        (session['user_id'],)
    ).fetchone()[0]
    
    conn.close()
    
    return render_template('wallet.html', user=user, cart_count=cart_count)

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    transactions = conn.execute('''
        SELECT t.*, p.name as product_name, p.price 
        FROM transactions t 
        JOIN products p ON t.product_id = p.id 
        WHERE t.user_id = ? 
        ORDER BY t.timestamp DESC
    ''', (session['user_id'],)).fetchall()
    
    # Get cart count
    cart_count = conn.execute(
        'SELECT COUNT(*) FROM cart WHERE user_id = ? AND is_verified = FALSE',
        (session['user_id'],)
    ).fetchone()[0]
    
    conn.close()
    
    return render_template('history.html', transactions=transactions, cart_count=cart_count)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)