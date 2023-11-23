from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for flash messages
DATABASE = 'mydatabase.db'

def connect_db():
    return sqlite3.connect(DATABASE)

def fetch_column_names(table_name):
    with connect_db() as connection:
        cursor = connection.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
    return [column[1] for column in columns]

def fetch_table_data(table_name, page=1, per_page=5, search_query=None):
    with connect_db() as connection:
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

        total_rows_query = f"SELECT COUNT(*) FROM {table_name};"
        cursor.execute(total_rows_query)
        total_rows = cursor.fetchone()[0]

    total_pages = (total_rows + per_page - 1) // per_page

    return {'columns': columns, 'rows': rows, 'page': page, 'per_page': per_page, 'total_pages': total_pages}

def add_column_to_table(table_name, column_name):
    with connect_db() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name};")
            flash(f"Column '{column_name}' added successfully to '{table_name}' table.", 'success')
        except sqlite3.OperationalError as e:
            flash(f"Error adding column: {e}", 'danger')

@app.route('/')
def display_tables():
    with connect_db() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

    table_data = {}
    for table in tables:
        table_name = table[0]
        search_query = request.args.get('search', '').strip()
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 5))

        data = fetch_table_data(table_name, page=page, per_page=per_page, search_query=search_query)
        table_data[table_name] = data

    return render_template('display_tables.html', tables=table_data, search_query=search_query)

@app.route('/add_column/<table_name>', methods=['GET', 'POST'])
def add_column(table_name):
    if request.method == 'POST':
        new_column_name = request.form.get('new_column_name')
        if new_column_name:
            add_column_to_table(table_name, new_column_name)

    return redirect(url_for('display_tables'))


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
    

    # Add this route to handle editing a row
@app.route('/edit_row/<table_name>/<int:row_id>', methods=['GET', 'POST'])
def edit_row(table_name, row_id):
    column_names = fetch_column_names(table_name)

    if request.method == 'POST':
        # Update the row with new values
        new_values = [request.form.get(column) for column in column_names]

        with sqlite3.connect('mydatabase.db') as connection:
            cursor = connection.cursor()
            set_values = ', '.join([f"{column} = ?" for column in column_names])
            update_query = f"UPDATE {table_name} SET {set_values} WHERE rowid = ?;"
            cursor.execute(update_query, new_values + [row_id])
            connection.commit()

        return redirect(url_for('display_tables'))

    else:
        # Retrieve the current values of the row for pre-filling the form
        with sqlite3.connect('mydatabase.db') as connection:
            cursor = connection.cursor()
            cursor.execute(f"SELECT * FROM {table_name} WHERE rowid = ?;", (row_id,))
            current_values = cursor.fetchone()

        # Pass the zip function to the template context
        return render_template('edit_row.html', table_name=table_name, row_id=row_id, columns=column_names, values=current_values, zip=zip)

    column_names = fetch_column_names(table_name)

    if request.method == 'POST':
        # Update the row with new values
        new_values = [request.form.get(column) for column in column_names]

        with sqlite3.connect('mydatabase.db') as connection:
            cursor = connection.cursor()
            set_values = ', '.join([f"{column} = ?" for column in column_names])
            update_query = f"UPDATE {table_name} SET {set_values} WHERE rowid = ?;"
            cursor.execute(update_query, new_values + [row_id])
            connection.commit()

        return redirect(url_for('display_tables'))

    else:
        # Retrieve the current values of the row for pre-filling the form
        with sqlite3.connect('mydatabase.db') as connection:
            cursor = connection.cursor()
            cursor.execute(f"SELECT * FROM {table_name} WHERE rowid = ?;", (row_id,))
            current_values = cursor.fetchone()

        return render_template('edit_row.html', table_name=table_name, row_id=row_id, columns=column_names, values=current_values)


# Add this route to handle editing a specific cell
@app.route('/edit_cell/<table_name>/<int:row_id>/<column_name>', methods=['GET', 'POST'])
def edit_cell(table_name, row_id, column_name):
    if request.method == 'POST':
        new_value = request.form.get('new_value')

        with connect_db() as connection:
            cursor = connection.cursor()
            update_query = f"UPDATE {table_name} SET {column_name} = ? WHERE rowid = ?;"
            cursor.execute(update_query, (new_value, row_id))
            connection.commit()

        return redirect(url_for('display_tables'))

    else:
        # Retrieve the current value of the cell for pre-filling the form
        with connect_db() as connection:
            cursor = connection.cursor()
            select_query = f"SELECT {column_name} FROM {table_name} WHERE rowid = ?;"
            cursor.execute(select_query, (row_id,))
            current_value = cursor.fetchone()[0]

        return render_template('edit_cell.html', table_name=table_name, row_id=row_id, column_name=column_name, current_value=current_value)


if __name__ == '__main__':
    app.run(debug=True)
