from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

@app.route('/')
def display_tables():
    # Connect to the SQLite database
    connection = sqlite3.connect('mydatabase.db')
    cursor = connection.cursor()

    # Get a list of all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Fetch and display the first few rows of each table
    table_data = {}
    for table in tables:
        table_name = table[0]

        # Fetch column names
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]

        # Fetch rows
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
        rows = cursor.fetchall()

        table_data[table_name] = {'columns': column_names, 'rows': rows}

    # Close the database connection
    connection.close()

    # Render the HTML template with the table data
    return render_template('display_tables.html', tables=table_data)

if __name__ == '__main__':
    app.run(debug=True)
