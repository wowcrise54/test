from flask import Flask, render_template, request, send_file, session, redirect, url_for, flash
import psycopg2
import logging
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a more secure key

if not os.path.exists('reports'):
    os.makedirs('reports')

# Database connection
def connect_db():
    try:
        conn = psycopg2.connect(
            dbname="auto_parts_store",
            user="postgres",
            password="Tusson112",
            host="127.0.0.1",
            port="5432"
        )
        return conn
    except Exception as e:
        app.logger.error(f"Error connecting to the database: {e}")
        return None

# Configure logging
log_folder = 'logs'
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

logging.basicConfig(level=logging.DEBUG, filename=os.path.join(log_folder, 'db_operations.log'),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

translations = {
    'ru': {
        'username': 'Имя пользователя:',
        'password': 'Пароль:',
        'email': 'Email:',
        'phone': 'Телефон:',
        'register': 'Зарегистрироваться',
        'login': 'Войти',
        'register_success': 'Регистрация прошла успешно!',
        'register_error': 'Не удалось зарегистрироваться: {}',
        'login_success': 'Добро пожаловать, {}!',
        'login_error': 'Неверное имя пользователя или пароль',
        'db_connect_error': 'Не удалось подключиться к базе данных',
        'view_data': 'Просмотреть данные',
        'add_data': 'Добавить данные',
        'update_data': 'Обновить данные',
        'delete_data': 'Удалить данные',
        'export_to_excel': 'Экспорт в WPS Office',
        'view_log': 'Просмотреть логи',
        'change_language': 'Сменить язык',
        'table': 'Выберите таблицу:',
        'search': 'Поиск:',
        'column': 'Колонка:',
        'already_have_account': 'Уже есть аккаунт?',
        'no_account': 'Нет аккаунта?',
        'update': 'Обновить',
        'delete': 'Удалить',
        'back_to_dashboard': 'Вернуться на панель управления',
        'add_new_data': 'Добавить новые данные',
        'actions': 'Действия',
        'logout': 'Выйти',
    },
    'en': {
        'username': 'Username:',
        'password': 'Password:',
        'email': 'Email:',
        'phone': 'Phone:',
        'register': 'Register',
        'login': 'Login',
        'register_success': 'Registration successful!',
        'register_error': 'Registration failed: {}',
        'login_success': 'Welcome, {}!',
        'login_error': 'Invalid username or password',
        'db_connect_error': 'Failed to connect to the database',
        'view_data': 'View Data',
        'add_data': 'Add Data',
        'update_data': 'Update Data',
        'delete_data': 'Delete Data',
        'export_to_excel': 'Export to Excel',
        'view_log': 'View Logs',
        'change_language': 'Change Language',
        'table': 'Select Table:',
        'search': 'Search:',
        'column': 'Column:',
        'already_have_account': 'Already have an account?',
        'no_account': 'No account?',
        'update': 'Update',
        'delete': 'Delete',
        'back_to_dashboard': 'Back to Dashboard',
        'add_new_data': 'Add New Data',
        'actions': 'Actions',
        'logout': 'Logout',
    }
}

current_language = 'ru'

def get_translation(key):
    return translations[current_language].get(key, key)

def get_primary_key(table):
    primary_keys = {
        'customers': 'customer_id',
        'orders': 'order_id',
        'products': 'product_id',
        'categories': 'category_id',
        'orderdate': 'date_id'
    }
    return primary_keys.get(table, 'id')

def log_db_action(username, action, table_name, record_id):
    conn = connect_db()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO logs (username, action, table_name, record_id) VALUES (%s, %s, %s, %s)",
            (username, action, table_name, record_id)
        )
        conn.commit()
    except Exception as e:
        app.logger.error(f"Error logging action to the database: {e}")
    finally:
        cursor.close()
        conn.close()

def check_privileges(required_level):
    privilege = session.get('privilege')
    if privilege is None:
        flash('You do not have the required privileges.', 'error')
        return redirect(url_for('index'))
    elif privilege < required_level:
        flash('You do not have the required privileges.', 'error')
        return redirect(url_for('dashboard'))
    return True

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html', translations=get_translation)

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    phone = request.form['phone']

    conn = connect_db()
    if not conn:
        flash(get_translation('db_connect_error'), 'error')
        return redirect(url_for('index'))

    cursor = conn.cursor()
    try:
        cursor.execute(
            "CALL register_customer(%s, %s, %s, %s, %s)",
            (username, email, phone, password, 0)
        )
        conn.commit()
        log_db_action(username, 'register', 'customers', None)
        flash(get_translation('register_success'), 'success')
    except Exception as e:
        flash(get_translation('register_error').format(e), 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = connect_db()
    if not conn:
        flash(get_translation('db_connect_error'), 'error')
        return redirect(url_for('index'))

    cursor = conn.cursor()
    try:
        cursor.execute("CALL login_customer(%s, %s, %s)", (username, password, None))
        result = cursor.fetchone()
        if result and len(result) > 0 and result[0] is not None:
            session['username'] = username
            session['privilege'] = result[0]  # Assuming the privilege is returned by the procedure
            log_db_action(username, 'login', 'customers', None)
            flash(get_translation('login_success').format(username), 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(get_translation('login_error'), 'error')
    except Exception as e:
        flash(get_translation('login_error').format(e), 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html', translations=get_translation)

@app.route('/logout')
def logout():
    username = session.get('username')
    session.pop('username', None)
    session.pop('privilege', None)
    if username:
        log_db_action(username, 'logout', 'customers', None)
    return redirect(url_for('index'))

@app.route('/change_language')
def change_language():
    global current_language
    current_language = 'en' if current_language == 'ru' else 'ru'
    return redirect(url_for('index'))

# View data route
@app.route('/view/<table>')
def view_data(table):
    privilege = check_privileges(0)
    if privilege is not True:
        return privilege

    if session.get('privilege') == 0 and table == 'customers':
        flash('You do not have the required privileges.', 'error')
        return redirect(url_for('dashboard'))

    conn = connect_db()
    if not conn:
        flash(get_translation('db_connect_error'), 'error')
        return redirect(url_for('dashboard'))

    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return render_template('view_data.html', table=table, rows=rows, columns=columns, translations=get_translation)
    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        conn.close()

# Add data route
@app.route('/add/<table>', methods=['GET', 'POST'])
def add_data(table):
    privilege = check_privileges(1)
    if privilege is not True:
        return privilege

    conn = connect_db()
    if not conn:
        flash(get_translation('db_connect_error'), 'error')
        return redirect(url_for('dashboard'))

    cursor = conn.cursor()
    cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'")
    columns = [row[0] for row in cursor.fetchall()]

    primary_key = get_primary_key(table)
    columns = [col for col in columns if col != primary_key]  # Remove the primary key from the columns list

    if request.method == 'POST':
        data = request.form.to_dict()
        try:
            columns_str = ', '.join(data.keys())
            values_str = ', '.join([f"%({key})s" for key in data.keys()])
            cursor.execute(f"INSERT INTO {table} ({columns_str}) VALUES ({values_str})", data)
            conn.commit()
            record_id = cursor.lastrowid  # Get the ID of the last inserted row
            log_db_action(session['username'], 'add', table, record_id)
            flash('Data added successfully!', 'success')
            return redirect(url_for('view_data', table=table))
        except Exception as e:
            flash(str(e), 'error')
            return redirect(url_for('add_data', table=table))

    return render_template('add_data.html', table=table, columns=columns, translations=get_translation)

# Update data route
@app.route('/update/<table>/<int:id>', methods=['GET', 'POST'])
def update_data(table, id):
    privilege = check_privileges(1)
    if privilege is not True:
        return privilege

    conn = connect_db()
    if not conn:
        flash(get_translation('db_connect_error'), 'error')
        return redirect(url_for('dashboard'))

    cursor = conn.cursor()
    cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'")
    columns = [row[0] for row in cursor.fetchall()]

    primary_key = get_primary_key(table)
    columns = [col for col in columns if col != primary_key]  # Remove the primary key from the columns list

    if request.method == 'POST':
        data = request.form.to_dict()
        try:
            set_clause = ', '.join([f"{key} = %({key})s" for key in data.keys()])
            cursor.execute(f"UPDATE {table} SET {set_clause} WHERE {primary_key} = %({primary_key})s", {**data, primary_key: id})
            conn.commit()
            log_db_action(session['username'], 'update', table, id)
            flash('Data updated successfully!', 'success')
            return redirect(url_for('view_data', table=table))
        except Exception as e:
            flash(str(e), 'error')
            return redirect(url_for('update_data', table=table, id=id))

    cursor.execute(f"SELECT * FROM {table} WHERE {primary_key} = %s", (id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('update_data.html', table=table, columns=columns, row=row, translations=get_translation)

# Delete data route
@app.route('/delete/<table>/<int:id>', methods=['POST'])
def delete_data(table, id):
    privilege = check_privileges(1)
    if privilege is not True:
        return privilege

    conn = connect_db()
    if not conn:
        flash(get_translation('db_connect_error'), 'error')
        return redirect(url_for('dashboard'))

    cursor = conn.cursor()
    primary_key = get_primary_key(table)
    try:
        cursor.execute(f"DELETE FROM {table} WHERE {primary_key} = %s", (id,))
        conn.commit()
        log_db_action(session['username'], 'delete', table, id)
        flash('Data deleted successfully!', 'success')
    except Exception as e:
        flash(str(e), 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('view_data', table=table))

# Export data to Excel
@app.route('/export/<table>')
def export_table_data(table):
    privilege = check_privileges(1)
    if privilege is not True:
        return privilege

    conn = connect_db()
    if not conn:
        flash(get_translation('db_connect_error'), 'error')
        return redirect(url_for('dashboard'))

    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)

        # Save the Excel file in the reports directory
        file_path = os.path.join('reports', f"{table}.xlsx")
        with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name=table)

        log_db_action(session['username'], 'export', table, None)
        flash(f"Data from {table} has been exported to {file_path}", 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        conn.close()

# View logs
@app.route('/view_log')
def view_log():
    privilege = check_privileges(1)
    if privilege is not True:
        return privilege

    conn = connect_db()
    if not conn:
        flash(get_translation('db_connect_error'), 'error')
        return redirect(url_for('dashboard'))

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM logs")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return render_template('view_log.html', logs=rows, columns=columns, translations=get_translation)
    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
