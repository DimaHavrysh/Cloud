import MySQLdb.cursors
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from datetime import datetime
import MySQLdb
from MySQLdb.cursors import DictCursor
# Ініціалізація Flask додатку
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Потрібно для роботи з сесіями

# Налаштування параметрів підключення до бази даних MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'dima'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'cloud'
app.config['MYSQL_PORT'] = 3306

# Ініціалізація MySQL
mysql = MySQL(app)


# Головний маршрут, який переадресовує на сторінку логіну
@app.route('/')
def home():
    return redirect(url_for('login'))
# Адмін панель
@app.route('/adminpanel', methods=['GET', 'POST'])
def adminpanel():
    message = None
    error = None
    users = None

    # Отримання ролі поточного користувача
    current_role = session.get('access_right')

    if current_role not in ['admin', 'owner']:
        return redirect('/access_denied')  # Перенаправлення, якщо доступ заборонений

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        action = request.form.get('action')

        # Адмін має доступ лише до оновлення ролі
        if current_role == 'admin' and action != 'update_role':
            error = "У вас немає доступу до цієї функції."
        else:
            if action == 'add_user' and current_role == 'owner':
                login = request.form.get('login')
                password = request.form.get('password')
                access_right = request.form.get('access_right')

                if not login or not password or not access_right:
                    error = "Будь ласка, заповніть усі поля для додавання користувача."
                else:
                    try:
                        query = """
                                    INSERT INTO UsersKeys (login, password, access_right)
                                    VALUES (%s, %s, %s)
                                """
                        cur.execute(query, (login, password, access_right))
                        mysql.connection.commit()
                        message = "Користувача успішно додано!"
                    except Exception as e:
                        error = f"Помилка при додаванні користувача: {e}"

            elif action == 'update_role':
                user_id = request.form.get('user_id')
                new_role = request.form.get('new_role')

                if not user_id or not new_role:
                    error = "Будь ласка, вкажіть ID користувача та нову роль."
                else:
                    try:
                        query = """
                                    UPDATE UsersKeys
                                    SET access_right = %s
                                    WHERE key_id = %s
                                """
                        cur.execute(query, (new_role, user_id))
                        mysql.connection.commit()
                        message = "Роль користувача успішно змінено!"
                    except Exception as e:
                        error = f"Помилка при оновленні ролі: {e}"

            elif action == 'delete_user' and current_role == 'owner':
                user_id = request.form.get('user_id')

                if not user_id:
                    error = "Будь ласка, вкажіть ID користувача для видалення."
                else:
                    try:
                        query = "DELETE FROM UsersKeys WHERE key_id = %s"
                        cur.execute(query, (user_id,))
                        mysql.connection.commit()
                        message = "Користувача успішно видалено!"
                    except Exception as e:
                        error = f"Помилка при видаленні користувача: {e}"

    # Отримання списку всіх користувачів
    try:
        cur.execute("SELECT key_id, login, password, access_right FROM UsersKeys")
        users = cur.fetchall()
    except Exception as e:
        error = f"Помилка при завантаженні користувачів: {e}"

    cur.close()

    return render_template(
        'adminpanel.html',
        users=users,
        message=message,
        error=error,
        current_role=current_role
    )

@app.route('/zaputu', methods=['GET', 'POST'])
def zaputu():
    query_type = None
    search_results = None
    total_with_garage = None
    total_drivers = None
    employee_data = None
    team_data = None
    error = None

    if request.method == 'POST':
        query_type = request.form.get('query')

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        if query_type == 'query1':
            # Обробка запиту 1
            vehicle_name = request.form.get('vehicle_name')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')

            if not vehicle_name or not start_date or not end_date:
                error = "Будь ласка, заповніть усі поля для запиту 1."
            else:
                query = """
                SELECT id, vehicle_id, vehicle_name, cargo_description, 
                       departure_date, arrival_date, departure_location, 
                       arrival_location, distance_km, weight_tons
                FROM cargo_transportations
                WHERE vehicle_name = %s AND departure_date >= %s AND arrival_date <= %s
                """
                cur.execute(query, (vehicle_name, start_date, end_date))
                search_results = cur.fetchall()

        elif query_type == 'query2':
            # Обробка запиту 2
            try:
                cur.execute("SELECT COUNT(*) AS total_with_garage FROM TransportGarage WHERE has_garage = 1")
                total_with_garage = cur.fetchone()['total_with_garage']

                query = """
                SELECT category,
                       SUM(CASE WHEN has_garage = 1 THEN 1 ELSE 0 END) AS with_garage,
                       SUM(CASE WHEN has_garage = 0 THEN 1 ELSE 0 END) AS without_garage
                FROM TransportGarage
                GROUP BY category
                """
                cur.execute(query)
                search_results = cur.fetchall()
            except Exception as e:
                error = f"Помилка при виконанні запиту: {e}"

        elif query_type == 'query3':
            # Обробка запиту 3
            vehicle_category = request.form.get('vehicle_category')
            mileage_date = request.form.get('mileage_date')
            year = request.form.get('year')

            if not vehicle_category or (not mileage_date and not year):
                error = "Будь ласка, оберіть категорію транспорту та дату або рік."
            else:
                try:
                    query = """
                    SELECT f.vehicle_category AS Category,
                           f.vehicle_brand AS Brand,
                           f.vehicle_model AS Model,
                           f.vehicle_registration_number AS RegistrationNumber,
                           m.mileage_date AS Date,
                           m.mileage_value AS Mileage
                    FROM Mileage m
                    JOIN Fleet f ON m.vehicle_id = f.id
                    WHERE f.vehicle_category = %s
                    """
                    params = [vehicle_category]

                    if mileage_date:
                        query += " AND m.mileage_date = %s"
                        params.append(mileage_date)
                    elif year:
                        query += " AND YEAR(m.mileage_date) = %s"
                        params.append(year)

                    cur.execute(query, params)
                    search_results = cur.fetchall()
                except Exception as e:
                    error = f"Помилка при виконанні запиту: {e}"

        elif query_type == 'query4':
            # Обробка запиту 4
            try:
                query = """
                        SELECT
                            vehicle_category,
                            repaired_part,
                            SUM(part_quantity) AS total_quantity
                        FROM
                            RepairDetails
                        GROUP BY
                            vehicle_category, repaired_part
                        ORDER BY
                            vehicle_category, repaired_part;
                        """
                cur.execute(query)
                search_results = cur.fetchall()
            except Exception as e:
                error = f"Помилка при виконанні запиту: {e}"

        elif query_type == 'query5':
            # Обробка запиту 5
            route_number = request.form.get('route_number')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')

            if not route_number or not start_date or not end_date:
                error = "Будь ласка, заповніть усі поля для запиту 5."
            else:
                try:
                    query = """
                            SELECT *
                            FROM TransportRoutes
                            WHERE route_number = %s AND distribution_date BETWEEN %s AND %s;
                            """
                    cur.execute(query, (route_number, start_date, end_date))
                    search_results = cur.fetchall()
                except Exception as e:
                    error = f"Помилка при виконанні запиту: {e}"

        elif query_type == 'query6':
            # Обробка запиту 6
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            car_category = request.form.get('car_category')
            car_brand = request.form.get('car_brand')
            car_id = request.form.get('car_id')

            if not start_date or not end_date:
                error = "Будь ласка, заповніть дати для запиту 6."
            else:
                try:
                    query = """
                                SELECT
                                    c.car_category,
                                    c.car_brand,
                                    c.car_model,
                                    COUNT(r.id) AS repair_count,
                                    SUM(r.repair_cost) AS total_cost
                                FROM
                                    repairs r
                                JOIN
                                    cars c ON r.car_id = c.id
                                WHERE
                                    r.repair_date BETWEEN %s AND %s
                                    AND (
                                        c.car_category = %s
                                        OR c.car_brand = %s
                                        OR c.id = %s
                                    )
                                GROUP BY
                                    c.car_category, c.car_brand, c.car_model;
                                """
                    cur.execute(query, (start_date, end_date, car_category, car_brand, car_id))
                    search_results = cur.fetchall()
                except Exception as e:
                    error = f"Помилка при виконанні запиту: {e}"

        elif query_type == 'query7':
            # Обробка запиту 7
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')

            if not start_date or not end_date:
                error = "Будь ласка, заповніть обидві дати для запиту 7."
            else:
                try:
                    query = """
                            SELECT
                                equipment_type,
                                model,
                                serial_number,
                                status,
                                date,
                                description
                            FROM
                                equipment_log
                            WHERE
                                date BETWEEN %s AND %s
                            ORDER BY
                                date ASC;
                            """
                    cur.execute(query, (start_date, end_date))
                    search_results = cur.fetchall()
                except Exception as e:
                    error = f"Помилка при виконанні запиту: {e}"

        elif query_type == 'query8':
            # Обробка запиту 8: роботи, виконані фахівцем за період
            specialist_name = request.form.get('specialist_name')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            car_license_plate = request.form.get('car_license_plate')

            if not specialist_name or not start_date or not end_date:
                error = "Будь ласка, заповніть усі обов'язкові поля для запиту 8."
            else:
                try:
                    query = """
                                SELECT
                                    specialist_name,
                                    car_license_plate,
                                    car_model,
                                    description,
                                    job_date
                                FROM
                                    jobs
                                WHERE
                                    specialist_name = %s
                                    AND job_date BETWEEN %s AND %s
                                    AND (%s IS NULL OR car_license_plate = %s)
                                ORDER BY
                                    job_date ASC;
                            """
                    # Параметри для запиту: фахівець, період та номер автомобіля (якщо вказано)
                    cur.execute(query, (specialist_name, start_date, end_date, car_license_plate, car_license_plate))
                    search_results = cur.fetchall()
                except Exception as e:
                    error = f"Помилка при виконанні запиту: {e}"

        elif query_type == 'query9':
            try:
                query = """
                                SELECT Driver.driver_id, Driver.first_name, Driver.last_name, Driver.license_number,
                                       Driver.experience, Transport.brand, Transport.model
                                FROM Driver
                                LEFT JOIN Transport ON Driver.transport_id = Transport.transport_id
                            """
                cur.execute(query)
                search_results = cur.fetchall()
            except Exception as e:
                error = f"Помилка при виконанні запиту: {e}"

        elif query_type == 'query10':
            try:
                # Отримуємо дані з таблиці Employee
                cur.execute('SELECT * FROM Employee')
                employee_data = cur.fetchall()

                # Отримуємо дані з таблиці Team
                cur.execute('SELECT * FROM Team')
                team_data = cur.fetchall()

                search_results = {
                    'employee_data': employee_data,
                    'team_data': team_data
                }

            except Exception as e:
                error = f"Помилка при виконанні запиту: {e}"


        cur.close()

    return render_template(
        'zaputu.html',
        query_type=query_type,
        search_results=search_results,
        total_with_garage=total_with_garage,
        employee_data=employee_data,
        team_data=team_data,
        error=error
    )



# Маршрут для сторінки логіну
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']

        # Перевірка логіну та пароля у базі даних
        cur = mysql.connection.cursor()
        cur.execute("SELECT login, access_right FROM UsersKeys WHERE login = %s AND password = %s", (login, password))
        user = cur.fetchone()
        cur.close()

        if user:
            # Зберігаємо логін і рівень доступу користувача в сесії
            session['logged_in'] = True
            session['login'] = user[0]  # Логін
            session['access_right'] = user[1]  # Рівень доступу (owner, admin, operator, guest)
            return redirect(url_for('home_page'))
        else:
            flash('Неправельний логін або пароль ', 'error')

    return render_template('login.html')

# Захищений маршрут для сторінки "home_page"
@app.route('/home')
def home_page():
    # Перевірка, чи користувач залогінений
    if 'logged_in' in session:
        # Отримуємо рівень доступу користувача
        user_login = session['login']
        access_right = session['access_right']
        return render_template('home_page.html', user_login=user_login, access_right=access_right)
    else:
        return redirect(url_for('login'))

# Маршрут для виходу з акаунта
@app.route('/logout')
def logout():
    # Видалення інформації про сесію
    session.pop('logged_in', None)
    session.pop('login', None)
    session.pop('access_right', None)
    return redirect(url_for('login'))

# Маршрут для сторінки відновлення пароля
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    password = None
    if request.method == 'POST':
        login = request.form['login']

        # Перевірка логіну у базі даних
        cur = mysql.connection.cursor()
        cur.execute("SELECT password FROM UsersKeys WHERE login = %s", (login,))
        result = cur.fetchone()
        cur.close()

        if result:
            password = result[0]
        else:
            password = "No such user found."

    return render_template('forgot_password.html', password=password)

# Маршрут для створення акаунта
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        access_right = request.form['access_right']  # Значення буде "guest" за замовчуванням

        # Додавання нового користувача до бази даних
        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO UsersKeys (login, password, access_right) VALUES (%s, %s, %s)",
                        (login, password, access_right))
            mysql.connection.commit()
        except Exception as e:
            print(f"Error: {e}")
            mysql.connection.rollback()
        cur.close()

        return redirect(url_for('login'))

    return render_template('register.html')

# Маршрут для відомостей про вантажоперевезення
@app.route('/trucking', methods=['GET', 'POST'])
def trucking():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Використовуємо DictCursor для повернення словників

    # Отримання всіх записів з таблиці cargo_transportations
    query = """
        SELECT id, vehicle_id, vehicle_name, cargo_description, 
               departure_date, arrival_date, departure_location, 
               arrival_location, distance_km, weight_tons
        FROM cargo_transportations
    """
    cur.execute(query)
    transport_data = cur.fetchall()  # Тепер transport_data є списком словників

    search_results = None

    # Обробка пошуку
    if request.method == 'POST':
        vehicle_name = request.form['vehicle_name']

        # Формування умов пошуку
        query_conditions = []
        query_params = [f'%{vehicle_name}%']

        # Побудова кінцевого запиту з умовами пошуку
        query = """
            SELECT id, vehicle_id, vehicle_name, cargo_description, 
                   departure_date, arrival_date, departure_location, 
                   arrival_location, distance_km, weight_tons
            FROM cargo_transportations
            WHERE vehicle_name LIKE %s
        """
        cur.execute(query, tuple(query_params))
        search_results = cur.fetchall()  # Також отримуємо як словники

    # Якщо search_results є None, задаємо йому порожній список
    search_results = search_results if search_results is not None else []

    cur.close()

    is_admin_or_owner = session.get('access_right') in ['admin', 'owner']

    return render_template(
        'trucking.html',
        transport_data=transport_data,
        search_results=search_results,
        is_admin_or_owner=is_admin_or_owner
    )


@app.route('/add_transportation', methods=['POST'])
def add_transportation():
    vehicle_id = request.form['vehicle_id']
    vehicle_name = request.form['vehicle_name']
    cargo_description = request.form['cargo_description']
    departure_date = request.form['departure_date']
    arrival_date = request.form['arrival_date']
    departure_location = request.form['departure_location']
    arrival_location = request.form['arrival_location']
    distance_km = request.form['distance_km']
    weight_tons = request.form['weight_tons']

    cur = mysql.connection.cursor()

    query = """
        INSERT INTO cargo_transportations (vehicle_id, vehicle_name, cargo_description, 
                                           departure_date, arrival_date, departure_location, 
                                           arrival_location, distance_km, weight_tons)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cur.execute(query, (vehicle_id, vehicle_name, cargo_description, departure_date,
                        arrival_date, departure_location, arrival_location,
                        distance_km, weight_tons))
    mysql.connection.commit()

    cur.close()

    flash('New transportation record added successfully!')
    return redirect(url_for('trucking'))


@app.route('/delete_transportation/<int:transport_id>')
def delete_transportation(transport_id):
    cur = mysql.connection.cursor()

    query = "DELETE FROM cargo_transportations WHERE id = %s"
    cur.execute(query, (transport_id,))
    mysql.connection.commit()

    cur.close()

    flash('Transportation record deleted successfully!')
    return redirect(url_for('trucking'))


@app.route('/edit_transportation/<int:transport_id>', methods=['GET', 'POST'])
def edit_transportation(transport_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Обробка GET-запиту для завантаження даних
    if request.method == 'GET':
        # Отримуємо дані для редагування
        query = """
            SELECT id, vehicle_id, vehicle_name, cargo_description, 
                   departure_date, arrival_date, departure_location, 
                   arrival_location, distance_km, weight_tons
            FROM cargo_transportations
            WHERE id = %s
        """
        cur.execute(query, (transport_id,))
        record = cur.fetchone()  # Отримуємо єдиний запис для редагування

        cur.close()

        if record:
            return render_template('trucking.html', record=record)
        else:
            flash('Record not found')
            return redirect(url_for('trucking'))

    # Обробка POST-запиту для оновлення даних
    if request.method == 'POST':
        vehicle_id = request.form['vehicle_id']
        vehicle_name = request.form['vehicle_name']
        cargo_description = request.form['cargo_description']
        departure_date = request.form['departure_date']
        arrival_date = request.form['arrival_date']
        departure_location = request.form['departure_location']
        arrival_location = request.form['arrival_location']
        distance_km = request.form['distance_km']
        weight_tons = request.form['weight_tons']

        # Оновлення даних в базі
        query = """
            UPDATE cargo_transportations
            SET vehicle_id = %s, vehicle_name = %s, cargo_description = %s, 
                departure_date = %s, arrival_date = %s, departure_location = %s, 
                arrival_location = %s, distance_km = %s, weight_tons = %s
            WHERE id = %s
        """
        cur.execute(query, (vehicle_id, vehicle_name, cargo_description, departure_date,
                            arrival_date, departure_location, arrival_location,
                            distance_km, weight_tons, transport_id))
        mysql.connection.commit()

        cur.close()

        flash('Transportation record updated successfully!')
        return redirect(url_for('trucking'))

# Маршрут для відомостей про наявність гаражів
@app.route('/garage', defaults={'info_type': 0}, methods=['GET', 'POST'])
@app.route('/garage/<int:info_type>', methods=['GET', 'POST'])
def garage(info_type):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Отримання всіх записів
    query = "SELECT id, name, category, has_garage FROM TransportGarage"
    cur.execute(query)
    garage_data = cur.fetchall()

    search_results = None

    if request.method == 'POST':
        search_name = request.form.get('name', '')
        search_category = request.form.get('category', '')
        search_has_garage = request.form.get('garage_status', '')

        query_conditions = []
        query_params = []

        if search_name:
            query_conditions.append("name LIKE %s")
            query_params.append(f'%{search_name}%')
        if search_category:
            query_conditions.append("category LIKE %s")
            query_params.append(f'%{search_category}%')
        if search_has_garage:
            query_conditions.append("has_garage = %s")
            query_params.append(int(search_has_garage))

        if query_conditions:
            query += " WHERE " + " AND ".join(query_conditions)

        cur.execute(query, tuple(query_params))
        search_results = cur.fetchall()

    cur.close()

    is_admin_or_owner = session.get('access_right') in ['admin', 'owner']

    return render_template(
        'garage.html',
        garage_data=garage_data,
        search_results=search_results if search_results else [],
        is_admin_or_owner=is_admin_or_owner,
        info_type=info_type
    )

@app.route('/add_garage_vehicle', methods=['POST'])
def add_garage_vehicle():
    name = request.form['name']
    category = request.form['category']
    has_garage = int(request.form['has_garage'])

    cur = mysql.connection.cursor()
    try:
        query = """
            INSERT INTO TransportGarage (name, category, has_garage)
            VALUES (%s, %s, %s)
        """
        cur.execute(query, (name, category, has_garage))
        mysql.connection.commit()
        flash('Новий транспортний засіб успішно додано!', 'success')
    except Exception as e:
        flash(f'Помилка: {str(e)}', 'danger')
    finally:
        cur.close()

    return redirect(url_for('garage', info_type=0))

@app.route('/delete_garage_vehicle/<int:id>')
def delete_garage_vehicle(id):
    cur = mysql.connection.cursor()
    try:
        query = "DELETE FROM TransportGarage WHERE id = %s"
        cur.execute(query, (id,))
        mysql.connection.commit()
        flash('Транспортний засіб успішно видалено!', 'success')
    except Exception as e:
        flash(f'Помилка: {str(e)}', 'danger')
    finally:
        cur.close()

    return redirect(url_for('garage', info_type=0))

@app.route('/edit_garage_vehicle/<int:id>', methods=['POST'])
def edit_garage_vehicle(id):
    name = request.form['name']
    category = request.form['category']
    has_garage = int(request.form['has_garage'])

    cur = mysql.connection.cursor()
    try:
        query = """
            UPDATE TransportGarage
            SET name = %s, category = %s, has_garage = %s
            WHERE id = %s
        """
        cur.execute(query, (name, category, has_garage, id))
        mysql.connection.commit()
        flash('Дані транспортного засобу успішно оновлено!', 'success')
    except Exception as e:
        flash(f'Помилка: {str(e)}', 'danger')
    finally:
        cur.close()

    return redirect(url_for('garage', info_type=0))

# Маршрут для даних про автопарк підприємства
@app.route('/avtopark', methods=['GET', 'POST'])
def avtopark():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Отримання всіх записів автопарку
    query = """
        SELECT Fleet.id, Fleet.vehicle_category, Fleet.vehicle_brand, Fleet.vehicle_model, 
               Fleet.vehicle_registration_number, 
               IFNULL(SUM(Mileage.mileage_value), 0) AS total_mileage,
               MAX(Mileage.mileage_date) AS mileage_date
        FROM Fleet
        LEFT JOIN Mileage ON Fleet.id = Mileage.vehicle_id
        GROUP BY Fleet.id
    """
    cur.execute(query)
    fleet_data = cur.fetchall()

    search_results = None

    if request.method == 'POST':
        search_category = request.form.get('vehicle_category', '')
        search_registration_number = request.form.get('vehicle_registration_number', '')
        search_date = request.form.get('mileage_date', None)

        query_conditions = []
        query_params = []

        if search_category:
            query_conditions.append("Fleet.vehicle_category LIKE %s")
            query_params.append(f'%{search_category}%')
        if search_registration_number:
            query_conditions.append("Fleet.vehicle_registration_number LIKE %s")
            query_params.append(f'%{search_registration_number}%')
        if search_date:
            query_conditions.append("Mileage.mileage_date = %s")
            query_params.append(search_date)

        query = """
            SELECT Fleet.id, Fleet.vehicle_category, Fleet.vehicle_brand, Fleet.vehicle_model, 
                   Fleet.vehicle_registration_number, 
                   IFNULL(SUM(Mileage.mileage_value), 0) AS total_mileage,
                   MAX(Mileage.mileage_date) AS mileage_date
            FROM Fleet
            LEFT JOIN Mileage ON Fleet.id = Mileage.vehicle_id
        """
        if query_conditions:
            query += " WHERE " + " AND ".join(query_conditions)
        query += " GROUP BY Fleet.id"

        cur.execute(query, tuple(query_params))
        search_results = cur.fetchall()

    cur.close()

    is_admin_or_owner = session.get('access_right') in ['admin', 'owner']

    return render_template(
        'avtopark.html',
        fleet_data=fleet_data,
        search_results=search_results if search_results else [],
        is_admin_or_owner=is_admin_or_owner
    )


@app.route('/add_vehicle', methods=['POST'])
def add_vehicle():
    vehicle_category = request.form['vehicle_category']
    vehicle_brand = request.form['vehicle_brand']
    vehicle_model = request.form['vehicle_model']
    vehicle_registration_number = request.form['vehicle_registration_number']
    mileage_date = request.form['mileage_date']

    cur = mysql.connection.cursor()
    try:
        query = """
            INSERT INTO Fleet (vehicle_category, vehicle_brand, vehicle_model, vehicle_registration_number)
            VALUES (%s, %s, %s, %s)
        """
        cur.execute(query, (vehicle_category, vehicle_brand, vehicle_model, vehicle_registration_number))
        vehicle_id = cur.lastrowid

        if mileage_date:
            mileage_query = """
                INSERT INTO Mileage (vehicle_id, mileage_date, mileage_value)
                VALUES (%s, %s, 0)
            """
            cur.execute(mileage_query, (vehicle_id, mileage_date))

        mysql.connection.commit()
        flash('Новий транспортний засіб успішно додано!', 'success')
    except Exception as e:
        flash(f'Помилка: {str(e)}', 'danger')
    finally:
        cur.close()

    return redirect(url_for('avtopark'))


@app.route('/delete_vehicle/<int:vehicle_id>')
def delete_vehicle(vehicle_id):
    cur = mysql.connection.cursor()
    query = "DELETE FROM Fleet WHERE id = %s"
    cur.execute(query, (vehicle_id,))
    mysql.connection.commit()
    cur.close()

    flash('Транспортний засіб успішно видалено!', 'success')
    return redirect(url_for('avtopark'))


@app.route('/edit_vehicle/<int:vehicle_id>', methods=['POST'])
def edit_vehicle(vehicle_id):
    vehicle_category = request.form['vehicle_category']
    vehicle_brand = request.form['vehicle_brand']
    vehicle_model = request.form['vehicle_model']
    vehicle_registration_number = request.form['vehicle_registration_number']

    cur = mysql.connection.cursor()
    try:
        query = """
            UPDATE Fleet
            SET vehicle_category = %s, vehicle_brand = %s, vehicle_model = %s, vehicle_registration_number = %s
            WHERE id = %s
        """
        cur.execute(query, (vehicle_category, vehicle_brand, vehicle_model, vehicle_registration_number, vehicle_id))
        mysql.connection.commit()
        flash('Дані транспортного засобу успішно оновлено!', 'success')
    except Exception as e:
        flash(f'Помилка: {str(e)}', 'danger')
    finally:
        cur.close()

    return redirect(url_for('avtopark'))

# Маршрут для даних про ремонт
@app.route('/remontvyzliv/<int:info_type>', methods=['GET', 'POST'])
def remontvyzliv(info_type):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Отримуємо всі записи з таблиці ремонту
    query = """
           SELECT id, vehicle_category, vehicle_brand, vehicle_model, repair_date, repair_cost, repaired_part, part_quantity
           FROM RepairDetails
       """
    cur.execute(query)
    remont_details_data = cur.fetchall()  # remont_details_data - це список словників

    search_results = None

    # Обробка пошукової функціональності
    if request.method == 'POST':
        vehicle_category = request.form.get('vehicle_category')
        repaired_part = request.form.get('repaired_part')

        # Створюємо умови для пошуку
        query_conditions = []
        query_params = []

        if vehicle_category:
            query_conditions.append("vehicle_category LIKE %s")
            query_params.append(f"%{vehicle_category}%")

        if repaired_part:
            query_conditions.append("repaired_part LIKE %s")
            query_params.append(f"%{repaired_part}%")

        # Якщо є умови для пошуку, формуємо кінцевий запит
        if query_conditions:
            query = """
                   SELECT id, vehicle_category, vehicle_brand, vehicle_model, repair_date, repair_cost, repaired_part, part_quantity
                   FROM RepairDetails
                   WHERE """ + " AND ".join(query_conditions)
            cur.execute(query, tuple(query_params))
        else:
            # Якщо немає параметрів для пошуку, виводимо всі записи
            cur.execute("""
                SELECT id, vehicle_category, vehicle_brand, vehicle_model, repair_date, repair_cost, repaired_part, part_quantity
                FROM RepairDetails
            """)

        search_results = cur.fetchall()  # Отримуємо результати пошуку як словники

    # Якщо результатів немає, встановлюємо search_results як порожній список
    search_results = search_results if search_results is not None else []

    cur.close()

    is_admin_or_owner = session.get('access_right') in ['admin', 'owner']

    return render_template('remontvyzliv.html', remont_details_data=remont_details_data,
                           search_results=search_results,
                           is_admin_or_owner=is_admin_or_owner, info_type=info_type)

@app.route('/add_remont_detail', methods=['POST'])
def add_remont_detail():
    vehicle_category = request.form['vehicle_category']
    vehicle_brand = request.form['vehicle_brand']
    vehicle_model = request.form['vehicle_model']
    repair_date = request.form['repair_date']
    repair_cost = request.form['repair_cost']
    repaired_part = request.form['repaired_part']
    part_quantity = request.form['part_quantity']

    cur = mysql.connection.cursor()

    query = """
        INSERT INTO RepairDetails (vehicle_category, vehicle_brand, vehicle_model, repair_date, repair_cost, repaired_part, part_quantity)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cur.execute(query, (vehicle_category, vehicle_brand, vehicle_model, repair_date, repair_cost, repaired_part, part_quantity))
    mysql.connection.commit()

    cur.close()

    flash('Нова деталь ремонту успішно додана!')
    return redirect(url_for('remontvyzliv', info_type=0))  # Перенаправляємо на маршрут ремонту

@app.route('/delete_remont_detail/<int:remont_id>')
def delete_remont_detail(remont_id):
    cur = mysql.connection.cursor()

    query = "DELETE FROM RepairDetails WHERE id = %s"
    cur.execute(query, (remont_id,))
    mysql.connection.commit()

    cur.close()

    flash('Деталь ремонту успішно видалена!')
    return redirect(url_for('remontvyzliv', info_type=0))  # Перенаправляємо на маршрут ремонту

@app.route('/edit_remont_detail/<int:remont_id>', methods=['GET', 'POST'])
def edit_remont_detail(remont_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'GET':
        # Отримуємо дані ремонту з бази даних
        query = """
            SELECT id, vehicle_category, vehicle_brand, vehicle_model, repair_date, repair_cost, repaired_part, part_quantity
            FROM RepairDetails
            WHERE id = %s
        """
        cur.execute(query, (remont_id,))
        remont = cur.fetchone()
        cur.close()

        # Якщо ремонт не знайдено
        if not remont:
            flash('Ремонт не знайдено!', 'danger')
            return redirect(url_for('remont', info_type=0))

        # Повертаємо дані ремонту для відображення в модальному вікні
        return render_template('remontvyzliv.html', remont=remont)

    elif request.method == 'POST':
        # Обробка форми для оновлення даних ремонту
        vehicle_category = request.form['vehicle_category']
        vehicle_brand = request.form['vehicle_brand']
        vehicle_model = request.form['vehicle_model']
        repair_date = request.form['repair_date']
        repair_cost = request.form['repair_cost']
        repaired_part = request.form['repaired_part']
        part_quantity = request.form['part_quantity']

        cur = mysql.connection.cursor()
        query = """
            UPDATE RepairDetails
            SET vehicle_category = %s, vehicle_brand = %s, vehicle_model = %s, repair_date = %s, 
                repair_cost = %s, repaired_part = %s, part_quantity = %s
            WHERE id = %s
        """
        cur.execute(query, (vehicle_category, vehicle_brand, vehicle_model, repair_date, repair_cost, repaired_part, part_quantity, remont_id))
        mysql.connection.commit()
        cur.close()

        flash('Деталь ремонту успішно оновлено!', 'success')
        return redirect(url_for('remontvyzliv', info_type=0))  # Перенаправляємо на маршрут ремонту

# Маршрут для даних про маршрути
@app.route('/marshryt/<int:info_type>', methods=['GET', 'POST'])
def marshryt(info_type):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor to return dictionaries

    # Fetch all records from the transport_routes table
    query = """
            SELECT id, route_number, vehicle_number, driver_name, passenger_count, distribution_date
            FROM TransportRoutes
        """
    cur.execute(query)
    transport_routes_data = cur.fetchall()  # transport_routes_data is a list of dictionaries

    search_results = None

    # Handle search functionality
    if request.method == 'POST':
        driver_name = request.form['driver_name']

        # Create search conditions
        query_conditions = []
        query_params = [f'%{driver_name}%']

        # Build final query with search conditions
        query = """
                SELECT id, route_number, vehicle_number, driver_name, passenger_count, distribution_date
                FROM TransportRoutes
                WHERE driver_name LIKE %s
            """
        cur.execute(query, tuple(query_params))
        search_results = cur.fetchall()  # Get the search results as dictionaries

    # If no results are found, set search_results to an empty list
    search_results = search_results if search_results is not None else []

    cur.close()

    is_admin_or_owner = session.get('access_right') in ['admin', 'owner']

    return render_template('marshryt.html', transport_routes_data=transport_routes_data,
                           search_results=search_results,
                           is_admin_or_owner=is_admin_or_owner, info_type=info_type)


@app.route('/add_transport_route', methods=['POST'])
def add_transport_route():
    route_number = request.form['route_number']
    vehicle_number = request.form['vehicle_number']
    driver_name = request.form['driver_name']
    passenger_count = request.form['passenger_count']
    distribution_date = request.form['distribution_date']

    cur = mysql.connection.cursor()

    query = """
            INSERT INTO TransportRoutes (route_number, vehicle_number, driver_name, passenger_count, distribution_date)
            VALUES (%s, %s, %s, %s, %s)
        """
    cur.execute(query, (route_number, vehicle_number, driver_name, passenger_count, distribution_date))
    mysql.connection.commit()

    cur.close()

    flash('New transport route added successfully!')
    return redirect(url_for('marshryt', info_type=0))  # Redirect to marshryt route


@app.route('/delete_transport_route/<int:route_id>')
def delete_transport_route(route_id):
    cur = mysql.connection.cursor()

    query = "DELETE FROM TransportRoutes WHERE id = %s"
    cur.execute(query, (route_id,))
    mysql.connection.commit()

    cur.close()

    flash('Transport route deleted successfully!')
    return redirect(url_for('marshryt', info_type=0))  # Redirect to marshryt route


@app.route('/edit_transport_route/<int:route_id>', methods=['GET', 'POST'])
def edit_transport_route(route_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'GET':
        # Отримуємо дані маршруту з бази даних
        query = """
            SELECT id, route_number, vehicle_number, driver_name, passenger_count, distribution_date
            FROM TransportRoutes
            WHERE id = %s
        """
        cur.execute(query, (route_id,))
        route = cur.fetchone()
        cur.close()

        # Якщо маршрут не знайдено
        if not route:
            flash('Маршрут не знайдено!', 'danger')
            return redirect(url_for('marshryt', info_type=0))

        # Повертаємо дані маршруту для відображення в модальному вікні
        return render_template('marshryt.html', route=route)

    elif request.method == 'POST':
        # Обробка форми для оновлення даних маршруту
        route_number = request.form['route_number']
        vehicle_number = request.form['vehicle_number']
        driver_name = request.form['driver_name']
        passenger_count = request.form['passenger_count']
        distribution_date = request.form['distribution_date']

        cur = mysql.connection.cursor()
        query = """
            UPDATE TransportRoutes
            SET route_number = %s, vehicle_number = %s, driver_name = %s, passenger_count = %s, 
                distribution_date = %s
            WHERE id = %s
        """
        cur.execute(query, (route_number, vehicle_number, driver_name, passenger_count, distribution_date, route_id))
        mysql.connection.commit()
        cur.close()

        flash('Маршрут успішно оновлено!', 'success')
        return redirect(url_for('marshryt', info_type=0))

# Маршрут для інформації про ремонти
@app.route('/allremont/<int:info_type>', methods=['GET', 'POST'])
def allremont(info_type):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Початковий запит для отримання всіх ремонтів
    query = """
        SELECT id, car_id, repair_date, repair_cost, repair_description, category, car_brand, car_model
        FROM repairs
    """
    cur.execute(query)
    repairs_data = cur.fetchall()

    search_results = None
    if request.method == 'POST':
        car_brand = request.form['car_brand']
        # Пошук за маркою автомобіля
        query = """
            SELECT id, car_id, repair_date, repair_cost, repair_description, category, car_brand, car_model
            FROM repairs
            WHERE car_brand LIKE %s
        """
        cur.execute(query, ('%' + car_brand + '%',))
        search_results = cur.fetchall()

    cur.close()

    # Ролі доступу
    is_operator = session.get('access_right') == 'operator'
    is_admin_or_owner = session.get('access_right') in ['admin', 'owner']

    return render_template(
        'allremont.html',
        repairs_data=repairs_data if search_results is None else search_results,  # Показуємо всі ремонти або лише пошукові результати
        search_results=search_results or [],  # Якщо немає результатів пошуку, передаємо порожній список
        is_admin_or_owner=is_admin_or_owner,
        is_operator=is_operator,
        info_type=info_type
    )

@app.route('/add_repair', methods=['POST'])
def add_repair():
    if session.get('access_right') not in ['admin', 'owner']:
        flash('У вас немає прав на додавання записів.')
        return redirect(url_for('allremont', info_type=0))

    car_id = request.form['car_id']
    repair_date = request.form['repair_date']
    repair_cost = request.form['repair_cost']
    repair_description = request.form['repair_description']
    category = request.form['category']
    car_brand = request.form['car_brand']
    car_model = request.form['car_model']

    cur = mysql.connection.cursor()
    query = """
        INSERT INTO repairs (car_id, repair_date, repair_cost, repair_description, category, car_brand, car_model)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cur.execute(query, (car_id, repair_date, repair_cost, repair_description, category, car_brand, car_model))
    mysql.connection.commit()
    cur.close()

    flash('Новий запис про ремонт успішно додано!')
    return redirect(url_for('allremont', info_type=0))

@app.route('/delete_repair/<int:repair_id>')
def delete_repair(repair_id):
    if session.get('access_right') not in ['admin', 'owner']:
        flash('У вас немає прав на видалення записів.')
        return redirect(url_for('allremont', info_type=0))

    cur = mysql.connection.cursor()
    query = "DELETE FROM repairs WHERE id = %s"
    cur.execute(query, (repair_id,))
    mysql.connection.commit()
    cur.close()

    flash('Запис про ремонт успішно видалено!')
    return redirect(url_for('allremont', info_type=0))

@app.route('/edit_repair/<int:repair_id>', methods=['POST'])
def edit_repair(repair_id):
    if session.get('access_right') not in ['admin', 'owner', 'operator']:
        flash('У вас немає прав на редагування записів.')
        return redirect(url_for('allremont', info_type=0))

    car_id = request.form['car_id']
    repair_date = request.form['repair_date']
    repair_cost = request.form['repair_cost']
    repair_description = request.form['repair_description']
    category = request.form['category']
    car_brand = request.form['car_brand']
    car_model = request.form['car_model']

    cur = mysql.connection.cursor()
    query = """
        UPDATE repairs
        SET car_id = %s, repair_date = %s, repair_cost = %s, repair_description = %s, 
            category = %s, car_brand = %s, car_model = %s
        WHERE id = %s
    """
    cur.execute(query, (car_id, repair_date, repair_cost, repair_description, category, car_brand, car_model, repair_id))
    mysql.connection.commit()
    cur.close()

    flash('Запис про ремонт успішно оновлено!')
    return redirect(url_for('allremont', info_type=0))

# Маршрут для інформації про автотехніку
@app.route('/avtotehnika/<int:info_type>', methods=['GET', 'POST'])
def avtotehnika(info_type):
    cur = mysql.connection.cursor()

    # Отримуємо всі записи з equipment_log
    query = """
                SELECT id, equipment_type, model, serial_number, status, date, description
                FROM equipment_log
            """
    cur.execute(query)
    equipment_data = cur.fetchall()

    search_results = None

    # Обробка пошуку
    if request.method == 'POST':
        equipment_type = request.form['equipment_type']
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # Формування умов пошуку
        query_conditions = []
        query_params = [f'%{equipment_type}%']

        if start_date and end_date:
            query_conditions.append("date BETWEEN %s AND %s")
            query_params.extend([start_date, end_date])
        elif start_date:
            query_conditions.append("date >= %s")
            query_params.append(start_date)
        elif end_date:
            query_conditions.append("date <= %s")
            query_params.append(end_date)

        # Побудова кінцевого запиту з умовами пошуку
        where_clause = " AND ".join(query_conditions) if query_conditions else "1"
        query = f"""
                    SELECT id, equipment_type, model, serial_number, status, date, description
                    FROM equipment_log
                    WHERE equipment_type LIKE %s
                    AND ({where_clause})
                """
        cur.execute(query, tuple(query_params))
        search_results = cur.fetchall()

    cur.close()

    is_admin_or_owner = session.get('access_right') in ['admin', 'owner']

    return render_template('avtotehnika.html', equipment_data=equipment_data, search_results=search_results,
                           is_admin_or_owner=is_admin_or_owner, info_type=info_type)


@app.route('/add_equipment', methods=['POST'])
def add_equipment():
    equipment_type = request.form['equipment_type']
    model = request.form['model']
    serial_number = request.form['serial_number']
    status = request.form['status']
    date = request.form['date']
    description = request.form['description']

    cur = mysql.connection.cursor()

    query = """
        INSERT INTO equipment_log (equipment_type, model, serial_number, status, date, description)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cur.execute(query, (equipment_type, model, serial_number, status, date, description))
    mysql.connection.commit()

    cur.close()

    flash('New equipment added successfully!')
    return redirect(url_for('avtotehnika', info_type=0))


@app.route('/delete_equipment/<int:equipment_id>')
def delete_equipment(equipment_id):
    cur = mysql.connection.cursor()

    query = "DELETE FROM equipment_log WHERE id = %s"
    cur.execute(query, (equipment_id,))
    mysql.connection.commit()

    cur.close()

    flash('Equipment record deleted successfully!')
    return redirect(url_for('avtotehnika', info_type=0))


@app.route('/edit_equipment/<int:equipment_id>', methods=['POST'])
def edit_equipment(equipment_id):
    equipment_type = request.form['equipment_type']
    model = request.form['model']
    serial_number = request.form['serial_number']
    status = request.form['status']
    date = request.form['date']
    description = request.form['description']

    cur = mysql.connection.cursor()

    query = """
        UPDATE equipment_log
        SET equipment_type = %s, model = %s, serial_number = %s, status = %s, date = %s, description = %s
        WHERE id = %s
    """
    cur.execute(query, (equipment_type, model, serial_number, status, date, description, equipment_id))
    mysql.connection.commit()

    cur.close()

    flash('Equipment record updated successfully!')
    return redirect(url_for('avtotehnika', info_type=0))

# Маршрут для інформації про роботи
@app.route('/works/<int:info_type>', methods=['GET', 'POST'])
def works(info_type):
    cur = mysql.connection.cursor()

    # Отримуємо всі роботи
    query = """
                SELECT id, specialist_name, car_license_plate, car_model, description, job_date
                FROM jobs
            """
    cur.execute(query)
    works_data = cur.fetchall()

    search_results = None

    if request.method == 'POST':
        specialist_name = request.form['specialist_name']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        car_id = request.form['car_id']

        # Формування умов пошуку
        query_conditions = []
        query_params = [f'%{specialist_name}%', f'%{car_id}%', f'%{car_id}%']

        if start_date and end_date:
            query_conditions.append("job_date BETWEEN %s AND %s")
            query_params.extend([start_date, end_date])
        elif start_date:
            query_conditions.append("job_date >= %s")
            query_params.append(start_date)
        elif end_date:
            query_conditions.append("job_date <= %s")
            query_params.append(end_date)

        # Побудова кінцевого запиту з умовами пошуку
        where_clause = " AND ".join(query_conditions) if query_conditions else "1"
        query = f"""
                    SELECT id, specialist_name, car_license_plate, car_model, description, job_date
                    FROM jobs
                    WHERE specialist_name LIKE %s
                    AND ({where_clause})
                    AND (car_license_plate LIKE %s OR car_model LIKE %s)
                """
        cur.execute(query, tuple(query_params))
        search_results = cur.fetchall()

    cur.close()

    is_admin_or_owner = session.get('access_right') in ['admin', 'owner']

    return render_template('works.html', works_data=works_data, search_results=search_results,
                           is_admin_or_owner=is_admin_or_owner, info_type=info_type)


@app.route('/add_work', methods=['POST'])
def add_work():
    cur = mysql.connection.cursor()

    # Отримуємо дані з форми
    specialist_name = request.form['specialist_name']
    car_license_plate = request.form['car_license_plate']
    car_model = request.form['car_model']
    description = request.form['description']
    job_date = request.form['job_date']

    # Перевірка, чи всі поля заповнені
    if not specialist_name or not car_license_plate or not description or not job_date:
        flash('Всі поля повинні бути заповнені.', 'danger')
        return redirect(url_for('works', info_type=0))

    # Додаємо новий запис в базу даних
    query = """
        INSERT INTO jobs (specialist_name, car_license_plate, car_model, description, job_date)
        VALUES (%s, %s, %s, %s, %s)
    """
    cur.execute(query, (specialist_name, car_license_plate, car_model, description, job_date))
    mysql.connection.commit()

    if cur.rowcount > 0:
        flash('Робота успішно додана', 'success')
    else:
        flash('Не вдалося додати роботу.', 'danger')

    cur.close()
    return redirect(url_for('works', info_type=0))

@app.route('/edit_work/<int:work_id>', methods=['POST'])
def edit_work(work_id):
    cur = mysql.connection.cursor()

    # Отримуємо дані з форми
    specialist_name = request.form['specialist']
    car_license_plate = request.form['car_license_plate']
    description = request.form['description']
    job_date = request.form['job_date']

    if not specialist_name or not car_license_plate or not description or not job_date:
        flash('Всі поля повинні бути заповнені.', 'danger')
        return redirect(url_for('works', info_type=0))

    # Оновлюємо запис в базі даних
    query = """
        UPDATE jobs
        SET specialist_name = %s, car_license_plate = %s, car_model = %s, description = %s, job_date = %s
        WHERE id = %s
    """
    cur.execute(query, (specialist_name, car_license_plate, request.form['car_model'], description, job_date, work_id))
    mysql.connection.commit()

    if cur.rowcount > 0:
        flash('Робота оновлена успішно', 'success')
    else:
        flash('Зміни не були застосовані або робота не знайдена.', 'warning')

    cur.close()
    return redirect(url_for('works', info_type=0))

@app.route('/delete_work/<int:work_id>', methods=['GET'])
def delete_work(work_id):
    cur = mysql.connection.cursor()

    # Видаляємо роботу за її ID
    query = "DELETE FROM jobs WHERE id = %s"
    cur.execute(query, (work_id,))
    mysql.connection.commit()
    cur.close()

    flash('Робота видалена успішно', 'danger')
    return redirect(url_for('works', info_type=0))

# Маршрут для переліку водіїв
@app.route('/employeecar/<int:info_type>', methods=['GET', 'POST'])
def employee(info_type):
    cur = mysql.connection.cursor()

    search_name = request.args.get('search_name', '').strip()

    # Запит для вибору водіїв з фільтрацією за ім'ям або прізвищем
    if search_name:
        cur.execute("""
                SELECT Driver.driver_id, Driver.first_name, Driver.last_name, Driver.license_number,
                       Driver.experience, Transport.brand, Transport.model
                FROM Driver
                LEFT JOIN Transport ON Driver.transport_id = Transport.transport_id
                WHERE Driver.first_name LIKE %s OR Driver.last_name LIKE %s
            """, (f"%{search_name}%", f"%{search_name}%"))
        search_result = cur.fetchone()  # Пошук тільки одного результату
    else:
        search_result = None

    # Отримання списку водіїв з закріпленим транспортом
    cur.execute("""
            SELECT Driver.driver_id, Driver.first_name, Driver.last_name, Driver.license_number,
                   Driver.experience, Transport.brand, Transport.model
            FROM Driver
            LEFT JOIN Transport ON Driver.transport_id = Transport.transport_id
        """)
    driver_data = cur.fetchall()

    # Отримання списку всього транспорту
    cur.execute('SELECT * FROM Transport')
    transport_data = cur.fetchall()

    if request.method == 'POST':
        # Додавання нового водія
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        license_number = request.form['license_number']
        experience = request.form['experience']
        transport_id = request.form.get('transport_id')  # Отримуємо ID транспорту, якщо вибрано

        cur.execute("""
                INSERT INTO Driver (first_name, last_name, license_number, experience, transport_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (first_name, last_name, license_number, experience, transport_id))
        mysql.connection.commit()
        cur.close()

        flash('Водія успішно додано!')
        return redirect(url_for('employee', info_type=info_type))

    cur.close()

    return render_template('employeecar.html', driver_data=driver_data, transport_data=transport_data, info_type=info_type,search_result=search_result, search_name=search_name)


@app.route('/edit_driver/<int:driver_id>', methods=['POST'])
def edit_driver(driver_id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        license_number = request.form.get('license_number')
        experience = request.form.get('experience')
        transport_id = request.form.get('transport_id')

    cur.execute("""
            UPDATE Driver
            SET first_name = %s, last_name = %s, license_number = %s, experience = %s, transport_id = %s
            WHERE driver_id = %s
        """, (first_name, last_name, license_number, experience, transport_id, driver_id))
    mysql.connection.commit()
    cur.close()

    flash('Дані водія успішно оновлено!')
    return redirect(url_for('employee', info_type=1))


@app.route('/delete_driver/<int:driver_id>', methods=['GET'])
def delete_driver(driver_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM Driver WHERE driver_id = %s", (driver_id,))
    mysql.connection.commit()
    cur.close()

    flash('Водія успішно видалено!')
    return redirect(url_for('employee', info_type=1))


# Маршрут для списку підлеглих
@app.route('/pidlegli/<int:info_type>', methods=['GET', 'POST'])
def pidlegli(info_type):
    # Підключення до бази даних
    cur = mysql.connection.cursor()

    # Отримання даних для employee і team
    cur.execute('SELECT * FROM Employee')
    employee_data = cur.fetchall()

    cur.execute('SELECT * FROM Team')
    team_data = cur.fetchall()

    search_results = None

    if request.method == 'POST':
        leader_name = request.form['leader_name']
        query = """
                  SELECT
                      e.first_name,
                      e.last_name,
                      e.position,
                      t.team_name
                  FROM
                      Employee e
                  JOIN
                      Team t ON e.team_id = t.team_id
                  WHERE
                      t.team_leader = %s
                      OR t.master = %s
                      OR t.site_manager = %s;
                  """
        cur.execute(query, (leader_name, leader_name, leader_name))
        search_results = cur.fetchall()

    cur.close()

    # Додати доступ до функцій редагування і видалення лише для owner або admin
    is_admin_or_owner = session.get('access_right') in ['admin', 'owner']

    return render_template('pidlegli.html', employee_data=employee_data, team_data=team_data,
                           search_results=search_results, is_admin_or_owner=is_admin_or_owner)


# Маршрут для додавання працівника
@app.route('/add_employee', methods=['POST'])
def add_employee():
    if session.get('access_right') in ['admin', 'owner']:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        position = request.form['position']
        team_id = request.form['team_id']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Employee (first_name, last_name, position, team_id) VALUES (%s, %s, %s, %s)",
                    (first_name, last_name, position, team_id))
        mysql.connection.commit()
        cur.close()

    return redirect(url_for('pidlegli', info_type=0))

# Маршрут для додавання бригади
@app.route('/add_team', methods=['POST'])
def add_team():
    if session.get('access_right') in ['admin', 'owner']:
        team_name = request.form['team_name']
        team_leader = request.form['team_leader']
        master = request.form['master']
        site_manager = request.form['site_manager']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Team (team_name, team_leader, master, site_manager) VALUES (%s, %s, %s, %s)",
                    (team_name, team_leader, master, site_manager))
        mysql.connection.commit()
        cur.close()

    return redirect(url_for('pidlegli', info_type=0))

# Маршрут для видалення працівника
@app.route('/delete_employee/<int:employee_id>', methods=['GET'])
def delete_employee(employee_id):
    cur = mysql.connection.cursor()
    query = "DELETE FROM Employee WHERE employee_id = %s"
    cur.execute(query, (employee_id,))
    mysql.connection.commit()
    cur.close()

    flash('Працівника успішно видалено')
    return redirect(url_for('pidlegli', info_type=1))

# Маршрут для видалення бригади
@app.route('/delete_team/<int:team_id>', methods=['GET'])
def delete_team(team_id):
    cur = mysql.connection.cursor()
    query = "DELETE FROM Team WHERE team_id = %s"
    cur.execute(query, (team_id,))
    mysql.connection.commit()
    cur.close()

    flash('Бригаду успішно видалено')
    return redirect(url_for('pidlegli', info_type=1))

# Маршрут для редагування працівника
@app.route('/edit_employee/<int:employee_id>', methods=['POST'])
def edit_employee(employee_id):
    # Отримуємо нові дані з форми
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    position = request.form['position']
    team_id = request.form['team_id']

    # Підключення до бази даних
    cur = mysql.connection.cursor()

    # Оновлюємо дані працівника в базі даних
    query = """
        UPDATE Employee
        SET first_name = %s, last_name = %s, position = %s, team_id = %s
        WHERE employee_id = %s
    """
    cur.execute(query, (first_name, last_name, position, team_id, employee_id))
    mysql.connection.commit()
    cur.close()

    flash('Працівника успішно оновлено')
    return redirect(url_for('pidlegli', info_type=1))

# Маршрут для редагування бригади
@app.route('/edit_team/<int:team_id>', methods=['POST'])
def edit_team(team_id):
    # Отримуємо нові дані з форми
    team_name = request.form['team_name']
    team_leader = request.form['team_leader']
    master = request.form['master']
    site_manager = request.form['site_manager']

    # Підключення до бази даних
    cur = mysql.connection.cursor()

    # Оновлюємо дані бригади в базі даних
    query = """
        UPDATE Team
        SET team_name = %s, team_leader = %s, master = %s, site_manager = %s
        WHERE team_id = %s
    """
    cur.execute(query, (team_name, team_leader, master, site_manager, team_id))
    mysql.connection.commit()
    cur.close()

    flash('Бригаду успішно оновлено')
    return redirect(url_for('pidlegli', info_type=1))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
