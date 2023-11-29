from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def fetch_column_names(table_name):
    connection = sqlite3.connect('mydatabase.db')
    cursor = connection.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    connection.close()
    return [column[1] for column in columns]

def fetch_table_data(table_name, search_query=None):
    connection = sqlite3.connect('mydatabase.db')
    cursor = connection.cursor()

    columns = fetch_column_names(table_name)

    if search_query:
        search_condition = " OR ".join([f"{column} LIKE ?" for column in columns])
        query = f"SELECT * FROM {table_name} WHERE {search_condition};"
        cursor.execute(query, (f"%{search_query}%",) * len(columns))
    else:
        cursor.execute(f"SELECT * FROM {table_name};")

    rows = cursor.fetchall()
    connection.close()
    return {'columns': columns, 'rows': rows}

@app.route('/')
def display_tables():
    connection = sqlite3.connect('mydatabase.db')
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    table_data = {}
    for table in tables:
        table_name = table[0]
        
        # Check if a search query is present
        search_query = request.args.get('search', '').strip()
        
        # Fetch table data based on search query
        data = fetch_table_data(table_name, search_query)
        table_data[table_name] = data

    connection.close()
    return render_template('display_tables.html', tables=table_data, search_query=search_query)

@app.route('/add_row/<table_name>', methods=['GET', 'POST'])
def add_row(table_name):
    if request.method == 'POST':
        column_names = fetch_column_names(table_name)
        values = [request.form.get(column) for column in column_names]

        with sqlite3.connect('mydatabase.db') as connection:
            cursor = connection.cursor()
            cursor.execute(f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({', '.join(['?']*len(column_names))});", values)
            connection.commit()

        return redirect(url_for('display_tables'))

    else:
        column_names = fetch_column_names(table_name)
        return render_template('add_row.html', table_name=table_name, columns=column_names)

if __name__ == '__main__':
    app.run(debug=True)
