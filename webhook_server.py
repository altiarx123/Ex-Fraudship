from flask import Flask, request, Response
import os
import sys
from datetime import datetime
import pandas as pd
import pymysql  # MySQL database module
// Import React and necessary components
import React, { useState } from 'react';

const SliderComponent = () => {
  const [value, setValue] = useState(50);

  const handleSliderChange = (event) => {
    setValue(event.target.value);
  };

  return (
    <div>
      <label htmlFor="slider">Adjust Value:</label>
      <input
        type="range"
        id="slider"
        min="0"
        max="100"
        value={value}
        onChange={handleSliderChange}
      />
      <p>Selected Value: {value}</p>
    </div>
  );
};

export default SliderComponent;
# make sure project root is on path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
# Placeholder for database name
DB_NAME = None  # Replace with actual database name if using a database

# Function to create a database connection using PyMySQL
def create_connection(db_name):
    try:
        connection = pymysql.connect(
            host='localhost',  # Replace with your MySQL host
            user='root',       # Replace with your MySQL username
            password='',       # Replace with your MySQL password
            database=db_name,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except pymysql.MySQLError as e:
        print(f"Error connecting to database: {e}")
        return None

# Function to initialize the database schema
def initialize_db():
    if DB_NAME:
        connection = create_connection(DB_NAME)
        if connection:
            cursor = connection.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS replies (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME NOT NULL,
                    contact VARCHAR(255) NOT NULL,
                    reply VARCHAR(255) NOT NULL
                )
            ''')
            connection.commit()
            connection.close()

# Function to record customer reply in a database
def record_reply_in_db(contact, reply):
    if DB_NAME:
        connection = create_connection(DB_NAME)
        if connection:
            cursor = connection.cursor()
            cursor.execute('''
                INSERT INTO replies (timestamp, contact, reply)
                VALUES (NOW(), %s, %s)
            ''', (contact, reply))
            connection.commit()
            connection.close()

# Updated record_customer_reply function to support both CSV and database
def record_customer_reply(contact, reply):
    if DB_NAME:
        record_reply_in_db(contact, reply)
        return {"status": "recorded", "detail": "database"}
    else:
        file = 'fraudshield_replies.csv'
        note = pd.DataFrame([{"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                              "contact": contact,
                              "reply": reply}])
        if os.path.exists(file):
            note.to_csv(file, mode='a', header=False, index=False)
        else:
            note.to_csv(file, index=False)
        return {"status": "recorded", "detail": file}

app = Flask(__name__)

@app.route('/sms_reply', methods=['POST'])
def sms_reply():
    # Twilio posts 'From' and 'Body'
    from_num = request.form.get('From') or request.values.get('From')
    body = request.form.get('Body') or request.values.get('Body')
    if not from_num or not body:
        return Response("Missing parameters", status=400)
    # normalize reply
    reply = body.strip().upper()
    if reply.startswith('Y'):
        r = 'YES'
    elif reply.startswith('N'):
        r = 'NO'
    else:
        r = reply
    try:
        res = record_customer_reply(from_num, r)
    except Exception as e:
        return Response(f"Error recording reply: {e}", status=500)
    # Respond with a simple TwiML acknowledgement
    twiml = f"<?xml version='1.0' encoding='UTF-8'?><Response><Message>Thanks — your response ({r}) has been recorded.</Message></Response>"
    return Response(twiml, mimetype='application/xml')

if __name__ == '__main__':
    port = int(os.getenv('WEBHOOK_PORT', 5000))
    app.run(host='0.0.0.0', port=port)
