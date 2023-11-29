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

def fetch_table_data(table_name, page=1, per_page=5, search_query=None):
    connection = sqlite3.connect('mydatabase.db')
    cursor = connection.cursor()

    columns = fetch_column_names(table_name)

    offset = (page - 1) * per_page

    if search_query:
        search_condition = " OR ".join([f"{column} LIKE ?" for column in columns])
        query = f"SELECT * FROM {table_name} WHERE {search_condition} LIMIT ? OFFSET ?;"
        cursor.execute(query, (f"%{search_query}%",) * len(columns) + (per_page, offset))
    else:
        query = f"SELECT * FROM {table_name} LIMIT ? OFFSET ?;"
        cursor.execute(query, (per_page, offset))

    rows = cursor.fetchall()

    # Get the total number of rows for pagination
    total_rows_query = f"SELECT COUNT(*) FROM {table_name};"
    cursor.execute(total_rows_query)
    total_rows = cursor.fetchone()[0]

    connection.close()

    # Calculate total pages
    total_pages = (total_rows + per_page - 1) // per_page

    return {'columns': columns, 'rows': rows, 'page': page, 'per_page': per_page, 'total_pages': total_pages}

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

        # Pagination parameters
        page = int(request.args.get('page', 1))
        per_page = 5

        # Fetch table data based on search query and pagination
        data = fetch_table_data(table_name, page=page, per_page=per_page, search_query=search_query)
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
