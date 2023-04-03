# ? Cross-origin Resource Sharing - here it allows the view and core applications deployed on different ports to communicate. No need to know anything about it since it's only used once
from flask_cors import CORS, cross_origin
# ? Python's built-in library for JSON operations. Here, is used to convert JSON strings into Python dictionaries and vice-versa
import json
# ? flask - library used to write REST API endpoints (functions in simple words) to communicate with the client (view) application's interactions
# ? request - is the default object used in the flask endpoints to get data from the requests
# ? Response - is the default HTTP Response object, defining the format of the returned data by this api
from flask import *
# ? sqlalchemy is the main library we'll use here to interact with PostgresQL DBMS
import sqlalchemy
# ? Just a class to help while coding by suggesting methods etc. Can be totally removed if wanted, no change
from typing import Dict
from datetime import date
from hashlib import sha256
import time
# ? web-based applications written in flask are simply called apps are initialized in this format from the Flask base class. You may see the contents of `__name__` by hovering on it while debugging if you're curious
app = Flask(__name__)

# ? Just enabling the flask app to be able to communicate with any request source
CORS(app)

# ? building our `engine` object from a custom configuration string
# ? for this project, we'll use the default postgres user, on a database called `postgres` deployed on the same machine
YOUR_POSTGRES_PASSWORD = "postgres"
connection_string = f"postgresql://postgres:{YOUR_POSTGRES_PASSWORD}@127.0.0.1/IT2002-App"
engine = sqlalchemy.create_engine(
    "postgresql://postgres:postgres@localhost/IT2002-App", pool_pre_ping=True
)

# ? `db` - the database (connection) object will be used for executing queries on the connected database named `postgres` in our deployed Postgres DBMS
db = engine.connect()
## Secret key for sessions
secret_key = "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"
today = date.today()
# ? A dictionary containing
data_types = {
    'boolean': 'BOOL',
    'integer': 'INT',
    'text': 'TEXT',
    'time': 'TIME',
}

# ? @app.get is called a decorator, from the Flask class, converting a simple python function to a REST API endpoint (function)

@app.get("/table")
def get_relation():
    # ? This method returns the contents of a table whose name (table-name) is given in the url `http://localhost:port/table?name=table-name`
    # ? Below is the default way of parsing the arguments from http url's using flask's request object
    relation_name = request.args.get('name', default="", type=str)
    # ? We use try-except statements for exception handling since any wrong query will crash the whole flow
    try:
        # ? Statements are built using f-strings - Python's formatted strings
        # ! Use cursors for better results
        statement = sqlalchemy.text(f"SELECT * FROM {relation_name};")
        # ? Results returned by the DBMS after execution are stored into res object defined in sqlalchemy (for reference)
        res = db.execute(statement)
        # ? committing the statement writes the db state to the disk; note that we use the concept of rollbacks for safe DB management
        db.commit()
        # ? Data is extracted from the res objects by the custom function for each query case
        # ! Note that you'll have to write custom handling methods for your custom queries
        data = generate_table_return_result(res)
        # ? Response object is instantiated with the formatted data and returned with the success code 200
        return Response(data, 200)
    except Exception as e:
        # ? We're rolling back at any case of failure
        db.rollback()
        # ? At any error case, the error is returned with the code 403, meaning invalid request
        # * You may customize it for different exception types, in case you may want
        return Response(str(e), 403)


# ? a flask decorator listening for POST requests at the url /table-create
@app.post("/table-create")
def create_table():
    # ? request.data returns the binary body of the POST request
    data = request.data.decode()
    try:
        # ? data is converted from stringified JSON to a Python dictionary
        table = json.loads(data)
        # ? data, or table, is an object containing keys to define column names and types of the table along with its name
        statement = generate_create_table_statement(table)
        # ? the remaining steps are the same
        db.execute(statement)
        db.commit()
        return Response(statement.text)
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)


@app.post("/table-insert")
# ? a flask decorator listening for POST requests at the url /table-insert and handles the entry insertion into the given table/relation
# * You might wonder why PUT or a similar request header was not used here. Fundamentally, they act as POST. So the code was kept simple here
def insert_into_table():
    # ? Steps are common in all of the POST behaviors. Refer to the statement generation for the explanatory
    data = request.data.decode()
    try:
        insertion = json.loads(data)
        statement = generate_insert_table_statement(insertion)
        db.execute(statement)
        db.commit()
        return Response(statement.text)
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)


@app.post("/table-update")
# ? a flask decorator listening for POST requests at the url /table-update and handles the entry updates in the given table/relation
def update_table():
    # ? Steps are common in all of the POST behaviors. Refer to the statement generation for the explanatory
    data = request.data.decode()
    try:
        update = json.loads(data)
        statement = generate_update_table_statement(update)
        db.execute(statement)
        db.commit()
        return Response(statement.text, 200)
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)


@app.post("/entry-delete")
# ? a flask decorator listening for POST requests at the url /entry-delete and handles the entry deletion in the given table/relation
def delete_row():
    # ? Steps are common in all of the POST behaviors. Refer to the statement generation for the explanatory
    data = request.data.decode()
    try:
        delete = json.loads(data)
        statement = generate_delete_statement(delete)
        db.execute(statement)
        db.commit()
        return Response(statement.text)
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)


def generate_table_return_result(res):
    # ? An empty Python list to store the entries/rows/tuples of the relation/table
    rows = []

    # ? keys of the SELECT query result are the columns/fields of the table/relation
    columns = list(res.keys())

    # ? Constructing the list of tuples/rows, basically, restructuring the object format
    for row_number, row in enumerate(res):
        rows.append({})
        for column_number, value in enumerate(row):
            rows[row_number][columns[column_number]] = value

    # ? JSON object with the relation data
    output = {}
    output["columns"] = columns  # ? Stores the fields
    output["rows"] = rows  # ? Stores the tuples

    """
        The returned object format:
        {
            "columns": ["a","b","c"],
            "rows": [
                {"a":1,"b":2,"c":3},
                {"a":4,"b":5,"c":6}
            ]
        }
    """
    # ? Returns the stringified JSON object
    return json.dumps(output)


def generate_delete_statement(details: Dict):
    # ? Fetches the entry id for the table name
    table_name = details["relationName"]
    id = details["deletionId"]
    # ? Generates the deletion query for the given entry with the id
    statement = f"DELETE FROM {table_name} WHERE id={id};"
    return sqlalchemy.text(statement)


def generate_update_table_statement(update: Dict):

    # ? Fetching the table name, entry/tuple id and the update body
    table_name = update["name"]
    id = update["id"]
    body = update["body"]

    # ? Default for the SQL update statement
    statement = f"UPDATE {table_name} SET "
    # ? Constructing column-to-value maps looping
    for key, value in body.items():
        statement += f"{key}=\'{value}\',"

    # ?Finalizing the update statement with table and row details and returning
    statement = statement[:-1]+f" WHERE {table_name}.id={id};"
    return sqlalchemy.text(statement)


def generate_insert_table_statement(insertion: Dict):
    # ? Fetching table name and the rows/tuples body object from the request
    table_name = insertion["name"]
    body = insertion["body"]
    valueTypes = insertion["valueTypes"]

    # ? Generating the default insert statement template
    statement = f"INSERT INTO {table_name}  "

    # ? Appending the entries with their corresponding columns
    column_names = "("
    column_values = "("
    for key, value in body.items():
        column_names += (key+",")
        if valueTypes[key] == "TEXT" or valueTypes[key] == "TIME":
            column_values += (f"\'{value}\',")
        else:
            column_values += (f"{value},")

    # ? Removing the last default comma
    column_names = column_names[:-1]+")"
    column_values = column_values[:-1]+")"

    # ? Combining it all into one statement and returning
    #! You may try to expand it to multiple tuple insertion in another method
    statement = statement + column_names+" VALUES "+column_values+";"
    return sqlalchemy.text(statement)


def generate_create_table_statement(table: Dict):
    # ? First key is the name of the table
    table_name = table["name"]
    # ? Table body itself is a JSON object mapping field/column names to their values
    table_body = table["body"]
    # ? Default table creation template query is extended below. Note that we drop the existing one each time. You might improve this behavior if you will
    # ! ID is the case of simplicity
    statement = f"DROP TABLE IF EXISTS {table_name}; CREATE TABLE {table_name} (id serial NOT NULL PRIMARY KEY,"
    # ? As stated above, column names and types are appended to the creation query from the mapped JSON object
    for key, value in table_body.items():
        statement += (f"{key}"+" "+f"{value}"+",")
    # ? closing the final statement (by removing the last ',' and adding ');' termination and returning it
    statement = statement[:-1] + ");"
    return sqlalchemy.text(statement)

# JUST TESTING
def insert_values_into_users(table: Dict):
    table_name = table["name"]
    # ? Table body itself is a JSON object mapping field/column names to their values
    table_body = table["body"]
    statement = f"INSERT INTO users VALUES('')"
    return sqlalchemy.text(statement)

## Create the users table
def create_users_table():
    create_users_statement = """
        CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        password_hash VARCHAR(255) NOT NULL,
        user_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        phone_number VARCHAR(20) UNIQUE NOT NULL,
        gender VARCHAR(6) CHECK(gender = 'male' or gender = 'female'),
        age INTEGER NOT NULL
        );
        """
    try:
        statement = sqlalchemy.text(create_users_statement)
        db.execute(statement)
        db.commit()
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)
    
# Landing/first page of the website
@app.route("/")
def landing_page():
    cookies = request.cookies.get('session_cookies')
    if get_user_cookies(cookies) != None:
        return render_template('home.html', userID=get_user_cookies(cookies))
    else:
        return render_template('landing.html')

# Home page of the website
@app.route("/home")
def home():
    cookies = request.cookies.get('session_cookies')
    if get_user_cookies(cookies) != None:
        return render_template('home.html', userID=get_user_cookies(cookies))
    else:
        return redirect(url_for(''))

# Create a route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Call the sign_in function and pass user_id and password
        user_id = int(request.form['user_id'])
        password = request.form['password']
        # admin_login = request.form['admin_login']
        
        passwordhash = sha256(password.encode('utf-8')).hexdigest()
        if sign_in(user_id,passwordhash) == False:
            # Show an error message if login fails
            error = 'Invalid user ID or password. Please try again.'
            print("Error")
            return render_template('login.html', error=error)
        ## Implementing native sessions for users without additional plugins 
        ## Cookies are generated by using SHA256(SecretKey+UserID+TimeStamp)
        user_cookies = secret_key + str(user_id) + str(time.time())
        hashedcookies = sha256(user_cookies.encode('utf-8')).hexdigest()
        update_cookies(user_id, hashedcookies)
        ## Set cookies
        resp = redirect(url_for("home"))
        resp.set_cookie('session_cookies', hashedcookies)
        # if admin_login == 'off':
        #     resp = redirect(url_for("home"))
        #     resp.set_cookie('session_cookies', hashedcookies)
        # elif(admin_sign_in):
        #     # check if the user is in the administrator table
        #     resp = redirect(url_for("admin"))
        #     resp.set_cookie('session_cookies', hashedcookies)
        # else:
        #     return render_template('login.html')
        # return resp
            
    return render_template('login.html')


# Create a route for the signout of user
@app.route('/logout', methods=['GET'])
def logout():
    cookies = request.cookies.get('session_cookies')
    remove_command = f"UPDATE users SET session_cookies = null WHERE session_cookies = '{cookies}'"
    statement = sqlalchemy.text(remove_command)
    db.execute(statement)
    db.commit()
    return render_template('landing.html')
        
    
# Create a route for the sign up page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Call the sign_up function and pass user_id and password
        user_id = request.form['user_id']
        password = request.form['password']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        gender = request.form['gender']
        age = request.form['age']
        passwordhash = str(sha256(password.encode('utf-8')).hexdigest())
        if sign_up(user_id):
            # Redirect to the login page after successful signup
            try:
                print("Trying")
                insert_command = f"INSERT INTO users VALUES ({user_id}, '{passwordhash}', '{name}', '{email}', '{phone}', '{gender}', {age});"
                statement = sqlalchemy.text(insert_command)
                db.execute(statement)
                db.commit()
                user_cookies = secret_key + str(user_id) + str(time.time())
                hashedcookies = sha256(user_cookies.encode('utf-8')).hexdigest()
                update_cookies(user_id, hashedcookies)
                resp = redirect(url_for("home"))
                resp.set_cookie('session_cookies', hashedcookies)
                return resp
            except Exception as e:
                db.rollback()
                return Response(str(e),403)
        else:
            # Show an error message if signup fails
            error = 'User ID already exists. Please choose a different one.'
            return render_template('signup.html', error=error)
    else:
        return render_template('signup.html')

# Function is used to insert the cookies into the database -> Allowing for synchronious sessions within the webpages

def update_cookies(user_id, cookies):
    update_cookies = f"UPDATE users SET session_cookies = '{cookies}' WHERE user_id = {user_id}"
    statement = sqlalchemy.text(update_cookies)
    res = db.execute(statement)
    db.commit()
    return True

def admin_sign_in(user_id):
    admin_check = f'SELECT user_id FROM administrators WHERE user_id = {user_id};'
    statement = sqlalchemy.text(admin_check)
    res = db.execute(statement)
    db.commit()
    res_tuple = res.fetchall()
    if res_tuple == None:
        return False
    elif len(res_tuple) > 0:
        return True

# Gets the password of the user, from the user_id
def get_password(user_id):
    password_query = f'SELECT password_hash FROM users WHERE user_id = {user_id};'
    statement = sqlalchemy.text(password_query)
    res = db.execute(statement)
    db.commit()
    res_tuple = res.fetchall()
    if res_tuple == None:
        return "jsjqwjasjsyj"
    elif len(res_tuple) > 0:
        password = res_tuple[0][0]
        print(password)
        return password

# Takes user_id and password as input and checks if the user exists in the database.
# Return True if the user exists and the password is correct otherwise, return False.
def sign_in(user_id, password):  
    stored_password= get_password(user_id)
    if password != stored_password:
        return False
    else:
        return True

# This functions checks and returns the user_name that corresponds to the cookies presented
def get_user_cookies(cookies):
    find_user = f"SELECT user_name from users WHERE session_cookies = '{cookies}'"
    statement = sqlalchemy.text(find_user)
    res = db.execute(statement)
    db.commit()
    res_tuple = res.fetchall()
    if len(res_tuple) > 0:
        name = res_tuple[0][0]
        return name
    else:
        return None

# Takes user_id and password and creates a new user
# Add fields for name, email, phone number, gender & age
# Returns false if the user exists, and true if there's no existing user
def sign_up(user_id):
    user_id_check = f'SELECT user_id FROM users WHERE user_id = {user_id}'
    res = db.execute(sqlalchemy.text(user_id_check))
    res_tuple = res.fetchall()
    db.commit()
    if(len(res_tuple) > 0): #user_id exists in the table already
        return False
    return True

# Checks if the user can book first, through the property_booking method
# If available -> bookslot, which inserts the booking into the bookings table
# Else -> throw an error saying the property is not available 
@app.route('/book', methods = ['POST'])
def booking_details(session_token, property_id):
    if request.method == 'POST':
        cookies = request.headers['cookie']
        property_id = request.form['property_id']
        if (property_booking_check(cookies, property_id)) == True: # property available
            bookslot(cookies, property_id)
            return redirect(url_for("confirmation"))
        else:
            # Show an error message if signup fails
            error = 'Property not available for booking. Please select another property'
            return render_template('booking.html', error=error)
    else:
        return render_template('booking.html')
    
    
# Routing to the home admin page
@app.route('/admin')
def admin_page():
    if 'user_id' in session:
        user_id = session['user_id']
        return render_template('admin.html', userID=user_id)
    
# Update the admin page to include the data query
@app.route("/admin/data_query", methods = ['POST'])
def admin_query():
    request_dict = {
        "num_users" : "SELECT COUNT(user_id) FROM users;",
        "num_properties" : "SELECT COUNT(property_id) FROM property;",
        "transaction_avg" : "SELECT TRUNC(AVG(t.amount), 2) FROM transaction t;",
        "transaction_stddev" : "SELECT TRUNC(STDDEV_SAMP(t.amount), 2) FROM transaction t;"
    }
    
    query_name_dict = {
                    "num_users" : "Number of Users",
                    "num_properties" : "Number of Properties",
                    "transaction_avg" : "Transaction Average",
                    "transaction_stddev" : "Transaction Standard Deviation"
    }
    
    if request.method == 'POST':
        query = request.form['query']
        res = db.execute(sqlalchemy.text(request_dict[query]))
        res_tuple = res.fetchall()
        db.commit()
        return render_template('admin.html', executed_query = query_name_dict[query], data_query_res = res_tuple[0][0])
    else:
        return render_template('admin.html', data_query_res = 'No query')
    
# Update the admin page to include the data list query
@app.route("/admin/data_list_query", methods = ['POST'])
def admin_list_query():
    request_dict = {
        "GST_room_rate" : """
                                SELECT p1.address, p1.room_rate * 1.08 AS adjusted_price
                                FROM property p1
                                WHERE p1.room_rate >= 1500
                                UNION
                                SELECT p2.address, p2.room_rate
                                FROM property p2
                                WHERE p2.room_rate < 1500;
                                """,
        "highest_spending_users" : """
                                SELECT u.user_id, u.user_name, SUM(t.amount) as total_spending
                                FROM users u, booking b, transaction t
                                WHERE u.user_id = b.student_id
                                AND b.booking_id = t.booking_id
                                AND t.status = 'paid'
                                GROUP BY u.user_id, u.user_name
                                HAVING SUM(t.amount) = (
                                SELECT MAX(total_spending)
                                FROM (
                                    SELECT u1.user_id, SUM(t1.amount) as total_spending
                                    FROM users u1, booking b1, transaction t1
                                    WHERE u1.user_id = b1.student_id
                                    AND b1.booking_id = t1.booking_id
                                    AND t1.status = 'paid'
                                    GROUP BY u1.user_id
                                ) as max_spending
                                );
                                """,
        "highest_value_transactions": """
                                SELECT u.user_name, MAX(t.amount) AS max_spend
                                FROM users u, booking b, transaction t
                                WHERE u.user_id = b.student_id
                                AND b.booking_id = t.booking_id
                                GROUP BY (u.user_name)
                                ORDER BY max_spend DESC
                                LIMIT 5;""",
        "highest_rated_properties": """
                                SELECT u.user_name, p.address, TRUNC(AVG(r.rating), 2)
                                FROM users u, property p, review r
                                WHERE u.user_id = p.owner_id
                                AND p.property_id = r.property_id
                                GROUP BY u.user_name, p.address
                                ORDER BY AVG(r.rating) DESC
                                LIMIT 5;
                                """,
        "users_no_transactions" : """
                                SELECT u.user_id, u.user_name
                                FROM users u
                                WHERE NOT EXISTS (
                                SELECT *
                                FROM booking b, transaction t
                                WHERE b.booking_id = t.booking_id
                                AND u.user_id = b.student_id 
                                AND t.status = 'paid'
                                );""",
        "unpaid_users"        : """
                                SELECT u1.user_id, u1.user_name, t1.amount 
                                FROM users u1, booking b1, transaction t1
                                WHERE u1.user_id = b1.student_id
                                AND b1.booking_id = t1.booking_id
                                AND b1.status = 'processing'
                                EXCEPT
                                SELECT u2.user_id, u2.user_name, t2.amount 
                                FROM users u2, booking b2, transaction t2
                                WHERE u2.user_id = b2.student_id
                                AND b2.booking_id = t2.booking_id
                                AND t2.status = 'paid';
                                """,
        "most_bookings_users" : """
                                SELECT u.user_id, u.user_name, COUNT(b.booking_id) as num_bookings
                                FROM users u, booking b 
                                WHERE u.user_id = b.student_id
                                GROUP BY u.user_id, u.user_name
                                HAVING COUNT(*) >= ALL(
                                SELECT COUNT(*)
                                FROM users u1, booking b1
                                WHERE u1.user_id = b1.student_id
                                GROUP BY u1.user_id
                                );"""
    }
    
    row_names_dict = {
        "GST_room_rate" : ("Address", "Adjusted Price"),
        "highest_spending_users" : ("User ID", "Username", "Total Spending"),
        "highest_value_transactions" : ("Username", "Max Spend"),
        "highest_rated_properties" : ("Owner's Name", "Address", "Avg Rating"),
        "users_no_transactions" : ("User ID", "Username"),
        "unpaid_users" : ("User ID", "Username", "Transaction amount"),
        "most_bookings_users" : ("User ID", "Username", "Booking amounts")
    }
    
    query_name_dict = {
        "GST_room_rate" : "GST applied if rate is higher than $1500",
        "highest_spending_users" : "Highest Spending Users",
        "highest_value_transactions" : "Top 5 Highest Value Transactions",
        "highest_rated_properties" : "Top 5 Highest Rated Properties",
        "users_no_transactions" : "Users who have not completed any transactions",
        "unpaid_users" : "Users who booked but not paid",
        "most_bookings_users" : "Users with the most bookings"
    }
    
    if request.method == 'POST':
        query = request.form['query']
        res = db.execute(sqlalchemy.text(request_dict[query]))
        res_tuple = res.fetchall()
        headers_tuple = row_names_dict[query]
        db.commit()
        return render_template('admin.html', executed_list_query = query_name_dict[query], list_query_res = res_tuple, query_headers = headers_tuple)


@app.route("/admin/join_tables", methods = ['POST'])
def admin_join_tables():
    pri_key_dict = {
        "users" : "user_id",
        "property" : "property_id",
        "review" : "review_id",
        "booking" : "booking_id",
        "transaction" : "transaction_id"
    }
    
    if request.method == 'POST':
        
        db1 = request.form['db1']
        db2 = request.form['db2']
        num_display = request.form['num_display']
        query = ''
        if db1 == 'users':
            """
            users & property -> user_id, owner_id
            users & review -> user_id, reviewer_id
            users & booking -> user_id, student_id
            Rest natural join
            """
            db2_key = ''
            if db2 == 'review':
                db2_key =  'reviewer_id'
            elif db2 == 'property':
                db2_key = 'owner_id'
            elif db2 == 'booking':
                db2_key = 'student_id'
            else:
                db2_key = 'user_id'
            query = f"""SELECT * 
                        FROM users, {db2}
                        WHERE user_id = {db2_key}
                        LIMIT {num_display}
                        """
        else:
            query = f"""SELECT *
                        FROM {db1}
                        NATURAL JOIN {db2}
                        LIMIT {num_display}"""
                        
        temp_table = f"CREATE TEMP TABLE temp_join AS ({query});"
        header_names = f"""
                    SELECT column_name
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE table_name = 'temp_join'
                    ORDER BY ordinal_position;
                    """
        drop_table = "DROP TABLE temp_join"
        try:
            res = db.execute(sqlalchemy.text(query + ";"))
            res_tuple = res.fetchall()
            # temp_table_creation & deletion
            db.execute(sqlalchemy.text(temp_table))
            headers = db.execute(sqlalchemy.text(header_names))
            db.execute(sqlalchemy.text(drop_table))
            
            header_tuple = headers.fetchall()
            header_tuple = tuple(map(lambda x: x[0], header_tuple))
            db.commit()
            return render_template('admin.html', header_names = header_tuple, join_query = res_tuple)
        except Exception as e:
            db.rollback()
            return Response(str(e),403)

# Creates the booking after the property is confirmed to be available, using the website cookie
def bookslot(session_token, property_id):
    if session_token in session:
        for key, value in session.iteritems():
            if value == session_token:
                user_id = key
    property_booking = f'INSERT INTO BOOKING VALUES ({booking_id},{property_id},{user_id}, {start_date}, {end_date}, {today}, confirmed)'
    res = db.execute(sqlalchemy.text(property_booking))
    return res

# Checks if the property is available, by checking if the availability in the database == 'yes'
def property_booking_check(session_token, property_id):
    if session_token in session:
        for key, value in session.iteritems():
            if value == session_token:
                user_id = key
    property_check = f'SELECT availibility FROM property WHERE property_id = {property_id}'
    try:
        res = db.execute(sqlalchemy.text(property_check))
        res_tuple = res.fetchall()
        db.commit()
        availability = res_tuple[0][0]
        if(availability == 'yes'): # just checks the availability in property for now, in the future, check the bookings table for start/end date availability as well
            return True
        else:
            return False
    except Exception as e:
                db.rollback()
                return Response(str(e),403)
        
    #return app
# ? This method can be used by waitress-serve CLI 
def create_app():
   return app
# ? The port where the debuggable DB management API is served
PORT = 80
# ? Running the flask app on the localhost/0.0.0.0, port 2222
# ? Note that you may change the port, then update it in the view application too to make it work (don't if you don't have another application occupying it)
if __name__ == "__main__":
    app.run("0.0.0.0", PORT)
    # ? Uncomment the below lines and comment the above lines below `if __name__ == "__main__":` in order to run on the production server
    # ? Note that you may have to install waitress running `pip install waitress`
    # ? If you are willing to use waitress-serve command, please add `/home/sadm/.local/bin` to your ~/.bashrc
    # from waitress import serve
    # serve(app, host="0.0.0.0", port=PORT)
