import sqlite3
import os
import random
from datetime import datetime

def init_db():
    conn = sqlite3.connect('delivery_robot.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            wallet_balance REAL DEFAULT 0.0
        )
    ''')
    
    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            rfid_number TEXT UNIQUE NOT NULL,
            price REAL NOT NULL,
            image_path TEXT NOT NULL
        )
    ''')
    
    # Cart table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            pin_code TEXT,
            pin_generated_at DATETIME,
            is_verified BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            pin_code TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # Insert default products
    products = [
        ('Sharpener', '10005F071850', 5.0, 'sharpener.jpg'),
        ('Eraser', '0F008A88C5C8', 5.0, 'eraser.jpg'),
        ('Scale', '1000476B80BC', 10.0, 'scale.jpg'),
        ('Pencil', '12000F0F2D3F', 10.0, 'pencil.jpg')
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO products (name, rfid_number, price, image_path)
        VALUES (?, ?, ?, ?)
    ''', products)
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('delivery_robot.db')
    conn.row_factory = sqlite3.Row
    return conn

def generate_pin():
    return str(random.randint(1000, 9999))