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
import random
import time
import datetime
# ? web-based applications written in flask are simply called apps are initialized in this format from the Flask base class. You may see the contents of `__name__` by hovering on it while debugging if you're curious
app = Flask(__name__)
import os
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

## Config for photos being shown in the folder
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
@app.route("/", methods = ['GET'])
def landing_page():
    cookies = request.cookies.get('session_cookies')
    listings = f"SELECT * FROM property WHERE availability = 'yes' ORDER BY room_rate LIMIT 3"
    statement = sqlalchemy.text(listings)
    res = db.execute(statement)
    db.commit()
    res_tuple = res.fetchall()
    if get_user_cookies(cookies) != None:
        return render_template('home.html', userID=get_user_cookies(cookies), preferredlisting = res_tuple)
    else:
        return render_template('landing.html', preferredlisting = res_tuple)

# Home page of the website
@app.route('/home', methods = ['GET', 'POST'])
def home():
    cookies = request.cookies.get('session_cookies')
    if get_user_cookies(cookies) != None:
        listings = f"SELECT * FROM property WHERE availability = 'yes' ORDER BY room_rate LIMIT 3"
        statement = sqlalchemy.text(listings)
        res = db.execute(statement)
        db.commit()
        res_tuple = res.fetchall()
        return render_template('home.html', userID=get_user_cookies(cookies), preferredlisting = res_tuple)
    else:
        return redirect(url_for('login'))

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
            error = Markup('''<div class="alert">
  <span class="closebtn" onclick="this.parentElement.style.display='none';">&times;</span>
  Incorrect userID or Password.
</div>''')
            return render_template('login.html', invalid = error)
        ## Implementing native sessions for users without additional plugins 
        ## Cookies are generated by using SHA256(SecretKey+UserID+TimeStamp)
        user_cookies = secret_key + str(user_id) + str(time.time())
        hashedcookies = sha256(user_cookies.encode('utf-8')).hexdigest()
        update_cookies(user_id, hashedcookies)
        ## Set cookies
        resp = redirect(url_for("home"))
        resp.set_cookie('session_cookies', hashedcookies)
        return resp
            
    return render_template('login.html')


# Create a route for the signout of user
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST' or request.method == 'GET':
        cookies = request.cookies.get('session_cookies')
        remove_command = f"UPDATE users SET session_cookies = null WHERE session_cookies = '{cookies}'"
        statement = sqlalchemy.text(remove_command)
        db.execute(statement)
        db.commit()
        ## Set cookies
        resp = redirect(url_for('landing_page'))
        resp.set_cookie('session_cookies', '0')
        return resp
    return render_template('landing.html')
    
# Create a route for the sign up page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Call the sign_up function and pass user_id and password
        ## Get current max userID, select that as the userID for the current user
        user_id_statement = "SELECT MAX(user_id) from users"
        statement = sqlalchemy.text(user_id_statement)
        res = db.execute(statement)
        db.commit()
        res_tuple = res.fetchall()
        user_id = res_tuple[0][0] + 1
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
                user_cookies = secret_key + str(user_id) + str(time.time())
                hashedcookies = sha256(user_cookies.encode('utf-8')).hexdigest()
                update_cookies(user_id, hashedcookies)
                insert_command = f"INSERT INTO users VALUES ({user_id}, '{passwordhash}', '{name}', '{email}', '{phone}', '{gender}', {age}, '{hashedcookies}');"
                statement = sqlalchemy.text(insert_command)
                db.execute(statement)
                db.commit()
                resp = redirect(url_for("home"))
                resp.set_cookie('session_cookies', hashedcookies)
                return resp
            except Exception as e:
                db.rollback()
                return Response(str(e),403)
    if request.method == 'GET':
        user_id_statement = "SELECT MAX(user_id) from users"
        statement = sqlalchemy.text(user_id_statement)
        res = db.execute(statement)
        db.commit()
        res_tuple = res.fetchall()
        user_id = res_tuple[0][0] + 1
        print(user_id)
        return render_template('signup.html', user_id = user_id)
    
@app.route('/user_profile', methods = ['GET', 'POST'])
def user_profile():
    cookies = request.cookies.get('session_cookies')
    if get_user_id(cookies) != None:
        user_id = get_user_id(cookies)
        user_query = f"SELECT * FROM users WHERE user_id = {user_id};"
        prev_bookings_query = f"""SELECT b.booking_id, p.address, p.property_type, b.start_date, b.end_date, b.booking_date, b.status
                                  FROM booking b
                                  LEFT JOIN property p
                                  ON b.property_id = p.property_id
                                  WHERE b.student_id = {user_id}
                                """
        try:
            user_res = db.execute(sqlalchemy.text(user_query))
            booking_res = db.execute(sqlalchemy.text(prev_bookings_query))
            user_tuple = user_res.fetchall()
            booking_tuple = booking_res.fetchall()
            user_name = user_tuple[0][2]
            email = user_tuple[0][3]
            phone_number = user_tuple[0][4]
            gender = user_tuple[0][5]
            age = user_tuple[0][6]
            db.commit()
            return render_template('user_profile.html', bookings = booking_tuple,
                                                        user_id = user_id,
                                                        user_name = user_name,
                                                        email = email,
                                                        phone_number = phone_number,
                                                        gender = gender,
                                                        age = age)
        except Exception as e:
            db.rollback()
            return Response(str(e), 403)
    else:
        return redirect("/login") 
@app.route('/confirmbooking', methods =['POST'])
def confbooking():
    cookies = request.cookies.get('session_cookies')
    booking_id = request.form['bookingID']
    ## Checking if the user is authorized to change the property
    user_id = get_user_id(cookies)
    if checkauthproperty(user_id, booking_id) == True:
        if getcurrstatus(booking_id) == "confirmed":
            toggleproperty(booking_id, "processing")
        elif getcurrstatus(booking_id) == "processing":
            toggleproperty(booking_id, "confirmed")
    return redirect("/user_profile")

def checkauthproperty(user_id, booking):
    # Check for the property and the user_id, ensuring that the result is not null
    user_id_statement = f"SELECT * from booking WHERE booking_id = {booking} and student_id = {user_id}"
    statement = sqlalchemy.text(user_id_statement)
    res = db.execute(statement)
    db.commit()
    res_tuple = res.fetchall()
    if res_tuple != None:
        return True
    else:
        return False
def getcurrstatus(booking):
    property_status = f"SELECT status from booking WHERE booking_id = {booking}"
    statement = sqlalchemy.text(property_status)
    res = db.execute(statement)
    db.commit()
    res_tuple = res.fetchall()
    if res_tuple[0][0] == "processing":

        return "processing"
    else:
        return "confirmed"
    
def toggleproperty(booking, status):
    property_update = f"UPDATE booking SET status = '{status}' WHERE booking_id = {booking}"
    statement = sqlalchemy.text(property_update)
    res = db.execute(statement)
    db.commit()
    return None

@app.route('/user_profile/edit', methods = ['POST'])
def edit_user_profile():
    cookies = request.cookies.get('session_cookies')
    if get_user_id(cookies) != None:
        user_id = get_user_id(cookies)
        field_to_edit = request.form['field']
        updated_field = request.form['updated']
        if field_to_edit != "password":
            update_query = f"""UPDATE users
                            SET {field_to_edit} = '{updated_field}'
                            WHERE user_id = {user_id};"""
        elif field_to_edit== "password":
            passwordhash = str(sha256(updated_field.encode('utf-8')).hexdigest())
            update_query = f"""UPDATE users
                            SET password_hash = '{passwordhash}'
                            WHERE user_id = {user_id};"""

        try:
            db.execute(sqlalchemy.text(update_query))
            db.commit()
            return redirect('/user_profile')
        except Exception as e:
            db.rollback()
            return Response(str(e), 403)
    else:
        return redirect("/login")   
    
@app.route('/user_profile/review', methods = ['GET'])
def view_reviews():
    cookies = request.cookies.get('session_cookies')
    if get_user_id(cookies) != None:
        user_id = get_user_id(cookies)
        prev_reviews_query = f"""SELECT r.review_date, p.address, p.property_type, r.rating, r.review
                                  FROM review r
                                  LEFT JOIN property p
                                  ON r.property_id = p.property_id
                                  WHERE r.reviewer_id = {user_id};
                                """
        address_query = f"""SELECT p.address
                                  FROM booking b
                                  LEFT JOIN property p
                                  ON b.property_id = p.property_id
                                  WHERE b.student_id = {user_id}
                                  AND b.status = 'confirmed';
                                """
        try:
            reviews_res = db.execute(sqlalchemy.text(prev_reviews_query))
            address_res = db.execute(sqlalchemy.text(address_query))
            reviews_tuple = reviews_res.fetchall()
            address_tuple = tuple(map(lambda x: x[0], address_res.fetchall()))
            db.commit()
            return render_template('user_reviews.html', reviews = reviews_tuple, addresses = address_tuple)
        except Exception as e:
            db.rollback()
            return Response(str(e), 403)
    else:
        return redirect("/login") 


@app.route("/user_profile/review/submit_review", methods = ['POST'])
def submit_review():
        cookies = request.cookies.get('session_cookies')
        if get_user_id(cookies) != None:
            user_id = get_user_id(cookies)
            latest_review_id = """SELECT MAX(review_id)
                                FROM review;
                                """
            address = request.form['address']
            rating = request.form['rating']
            review = request.form['review']
            property_id_query = f"SELECT property_id FROM property WHERE address = '{address}'"
            try:
                max_review_id = db.execute(sqlalchemy.text(latest_review_id))
                property_id_res = db.execute(sqlalchemy.text(property_id_query))
                max_review = max_review_id.fetchall()
                property_id = property_id_res.fetchall()
                next_review_id = max_review[0][0] + 1
                insert_review = f"""INSERT INTO review (review_id, reviewer_id, property_id, rating, review)
                                values ({next_review_id}, {user_id}, {property_id[0][0]}, {rating}, '{review}');"""
                db.execute(sqlalchemy.text(insert_review))
                db.commit()
                return redirect('/user_profile/review')
            except Exception as e:
                db.rollback()
                return Response(str(e), 403)
        return redirect('/login')
    
@app.route('/user_profile/properties', methods = ['GET'])
def view_properties():
    cookies = request.cookies.get('session_cookies')
    if get_user_id(cookies) != None:
        user_id = get_user_id(cookies)
        properties_query = f"""SELECT p.property_id, p.start_date, p.end_date, p.address, p.property_type, p.num_rooms, p.availability, p.room_rate
                                  FROM property p, users u
                                  WHERE p.owner_id = u.user_id
                                  AND u.user_id = {user_id};
                                """
        property_id_query = f"""SELECT p.property_id
                                  FROM property p, users u
                                  WHERE p.owner_id = u.user_id
                                  AND u.user_id = {user_id};
                                """
        property_cols = f"""SELECT column_name
                            FROM INFORMATION_SCHEMA.COLUMNS
                            WHERE table_name = 'property'
                            ORDER BY ordinal_position;
                            """
        try:
            properties_res = db.execute(sqlalchemy.text(properties_query))
            property_id_res = db.execute(sqlalchemy.text(property_id_query))
            property_cols_res = db.execute(sqlalchemy.text(property_cols))
            property_tuple = properties_res.fetchall()
            property_cols_tuple = tuple(map(lambda x: x[0], property_cols_res.fetchall()))
            property_id_tuple = tuple(map(lambda x: x[0], property_id_res.fetchall()))
            db.commit()
            return render_template('user_property.html', properties = property_tuple, property_ids = property_id_tuple, property_cols = property_cols_tuple)
        except Exception as e:
            db.rollback()
            return Response(str(e), 403)
    else:
        return redirect("/login") 
    
@app.route("/user_profile/properties/edit_property", methods = ['POST'])
def edit_properties():
        string_fields_list = ['start_date', 'end_date', 'address', 'property_type', 'availability']
        cookies = request.cookies.get('session_cookies')
        if get_user_id(cookies) != None:
            user_id = get_user_id(cookies)
            
            id_to_edit = request.form['edit_property']
            field_to_update = request.form['field_to_update']
            updated = request.form['updated']
            if field_to_update in string_fields_list:
                updated = f"'{updated}'"
            try:
                update_property = f"UPDATE property SET {field_to_update} = {updated} WHERE property_id = {id_to_edit}" 
                db.execute(sqlalchemy.text(update_property))
                db.commit()
                return redirect('/user_profile/properties')
            except Exception as e:
                db.rollback()
                return Response(str(e), 403)
        return redirect('/login')  

@app.route("/user_profile/properties/list_property", methods = ['POST'])
def list_properties():
        cookies = request.cookies.get('session_cookies')
        if get_user_id(cookies) != None:
            user_id = get_user_id(cookies)
            latest_property_id = """SELECT MAX(property_id)
                                FROM property;
                                """
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            address = request.form['address']
            property_type = request.form['property_type']
            num_rooms = request.form['num_rooms']
            availability = request.form['availability']
            room_rate = request.form['room_rate']
        
            try:
                max_property_id = db.execute(sqlalchemy.text(latest_property_id))
                max_review = max_property_id.fetchall()
                next_property_id = max_review[0][0] + 1
                insert_property = f"""INSERT INTO property (property_id, owner_id, start_date, 
                                            end_date, address, property_type, num_rooms, availability, room_rate) 
                                      VALUES ({next_property_id}, {user_id}, '{start_date}',
                                            '{end_date}', '{address}', '{property_type}', {num_rooms}, '{availability}', {room_rate});"""
                db.execute(sqlalchemy.text(insert_property))
                db.commit()
                return redirect('/user_profile/properties')
            except Exception as e:
                db.rollback()
                return Response(str(e), 403)
        return redirect('/login')
# Function is used to insert the cookies into the database -> Allowing for synchronious sessions within the webpages

def update_cookies(user_id, cookies):
    update_cookies = f"UPDATE users SET session_cookies = '{cookies}' WHERE user_id = {user_id}"
    statement = sqlalchemy.text(update_cookies)
    res = db.execute(statement)
    db.commit()
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
# This function returns ID from cookies
def get_user_id(cookies):
    find_user = f"SELECT user_id from users WHERE session_cookies = '{cookies}'"
    statement = sqlalchemy.text(find_user)
    res = db.execute(statement)
    db.commit()
    res_tuple = res.fetchall()
    if len(res_tuple) > 0:
        id = res_tuple[0][0]
        return id
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

# This path displays all of the property according to the filter that the user has set on the homepage
@app.route('/filter', methods = ['GET', 'POST'])
def property_list():
    if request.method == "POST":
        filter_type = request.form['type']
        if filter_type == "size":
            size = request.form['size']
            if size == "1room":
                sql_size = 1
            elif size == "2room":
                sql_size = 2
            elif size == "3room":
                sql_size = 3
            elif size == "4room":
                sql_size = 4
            elif size == "5room":
                sql_size = 5
            res = filter_size(sql_size)
        elif filter_type == "price":
            if request.form['price'] == "lowhigh":
                res = filter_price("low")
            elif request.form['price'] == "highlow":
                res = filter_price("high")
        elif filter_type == "date":
            ## Check date, whether to filter by earlier/later properties. Sufficient to group by ID, as they are sequentially inserted
            if request.form['size'] == "new":
                res = filter_age("low")
            elif request.form['size'] == "old":
                res = filter_age("high")
        elif filter_type == "senddate":
            ## Continue to work on this
            start_date = request.form['startdate']
            end_date = request.form['enddate']
            res = filter_date(start_date, end_date)
        return render_template('property_list.html', filtered = res)
    else:
        return render_template('property_list.html')


def filter_size(type):
    find_property = f"SELECT * from property WHERE num_rooms = {type}"
    statement = sqlalchemy.text(find_property)
    res = db.execute(statement)
    db.commit()
    res_tuple = res.fetchall()
    return res_tuple

def filter_price(type):
    if type == "low":
        find_property = f"SELECT * from property ORDER BY (room_rate)"
    if type == "high":
        find_property = f"SELECT * from property ORDER BY (room_rate) DESC"
    statement = sqlalchemy.text(find_property)
    res = db.execute(statement)
    db.commit()
    res_tuple = res.fetchall()
    return res_tuple

def filter_age(type):
    if type == "low":
        find_property = f"SELECT * from property ORDER BY (property_id)"
    if type == "high":
        find_property = f"SELECT * from property ORDER BY (property_id) DESC"
    statement = sqlalchemy.text(find_property)
    res = db.execute(statement)
    db.commit()
    res_tuple = res.fetchall()
    return res_tuple

def filter_date(start,end):
    ## Filter listings which fits in the timeframe selected
    find_timeframe = f"SELECT * FROM property WHERE property.property_id NOT IN(SELECT property.property_id FROM property LEFT JOIN booking on property.property_id = booking.property_id WHERE ((booking.start_date BETWEEN '{start}' AND '{end}') OR (booking.end_date BETWEEN '{start}' AND '{end}')))"
    statement = sqlalchemy.text(find_timeframe)
    res = db.execute(statement)
    db.commit()
    res_tuple = res.fetchall()
    return res_tuple
# This path displays the property that the user is looking at and displays it on the webpage
@app.route('/property', methods=['GET', 'POST'])
def Property():
    if request.method == "POST":
        property_id = request.form['getproperty']
        cookies = request.cookies.get('session_cookies')
        if get_user_cookies(cookies) != None:
            property_tuple = getProperty(property_id)
            return render_template('property.html', currlisting = property_tuple)
    else:
        redirect(url_for('/'))

def getProperty(id):
    find_property = f"SELECT * from property WHERE property_id = {id}"
    statement = sqlalchemy.text(find_property)
    res = db.execute(statement)
    db.commit()
    res_tuple = res.fetchall()
    return res_tuple

# Checks if the user can book first, through the property_booking method
# If available -> bookslot, which inserts the booking into the bookings table
# Else -> throw an error saying the property is not available 
@app.route('/book', methods = ['GET','POST'])
def book():
    if request.method == 'POST':
        cookies = request.cookies.get('session_cookies')
        property_id = request.form['property_id']
        start_time = request.form['startdate']
        end_time = request.form['enddate']
        # Find user id
        user_id = get_user_id(cookies)
        # Check for valid cookies and valid property
        if user_id != None and validbookingtime(property_id, start_time, end_time) == True:
            ## Book the property, validity check done in browser
            bookingID = bookingproperty(property_id, user_id, start_time, end_time)
            bookingdetails = getbooking(bookingID)
            ## Variables that are displayed in the bookingdetails
            bookingid = bookingdetails[0][0]
            property_id = bookingdetails[0][1]
            start_date = bookingdetails[0][3].strftime("%d/%m/%Y")
            end_date = bookingdetails[0][4].strftime("%d/%m/%Y")
            if bookingdetails != None:
                return render_template('confirmation.html', booking_id = bookingid, property_id = property_id, start_date = start_date, end_date = end_date)
        else:
            error = Markup('''<div class="alert">
  <span class="closebtn" onclick="this.parentElement.style.display='none';">&times;</span>
  Timeframe unavailable, choose another timeframe.
</div>''')
            return render_template('property.html', invalid = error)
    return redirect(url_for("home")) 



def bookingproperty(property_id, user_id, start_time, end_time):
    bookingID = random.randrange(0,999999)
    booking_date = datetime.date.today()
    book_property = f"INSERT INTO booking VALUES ({bookingID}, {property_id}, {user_id}, '{start_time}', '{end_time}', '{booking_date}', 'processing')"
    statement = sqlalchemy.text(book_property)
    res = db.execute(statement)
    db.commit()
    validbookingtime(property_id, start_time, end_time)
    return bookingID

def getbooking(bookingID):
    bookingDetails = f"SELECT * FROM booking WHERE booking_id = {bookingID}"
    statement = sqlalchemy.text(bookingDetails)
    res = db.execute(statement)
    db.commit()
    res_tuple = res.fetchall()
    return res_tuple

## Grab the unix timing of all of the booking, check which ones will conflict with the selected start_time
def validbookingtime(property_id, start_time, end_time):
    ## Initialize temp lists
    res_1 = []
    res_2 = []
    findtimings = f"SELECT start_date, end_date FROM booking WHERE property_id = {property_id}"
    statement = sqlalchemy.text(findtimings)
    res = db.execute(statement)
    db.commit()
    res_tuple = res.fetchall()
    for time1 in res_tuple:
        res_1.append(time.mktime(time1[0].timetuple()))
        res_1.append(time.mktime(time1[1].timetuple()))
        res_2.append(res_1)
        res_1 = []
    unixstartTime = time.mktime(datetime.datetime.strptime(start_time, "%Y-%m-%d").timetuple())
    unixendTime = time.mktime(datetime.datetime.strptime(end_time, "%Y-%m-%d").timetuple())
    print(unixstartTime)
    print(unixendTime)
    print(res_2)
    ## Iterate through the entire list to ensure that there are no instances where the start time and/or the end time is between the two values
    for time_list in res_2:
        if time_list[0] <= unixstartTime <= time_list[1]:
            return False
        if time_list[0] <= unixendTime <= time_list[1]:
            return False
    return True
    
# Routing to the home admin page
@app.route('/admin/home')
def admin_page():
    return render_template('admin.html')

# Landing page for admins - provides special admin sign-in
# redirects to admin homepage after completion
@app.route('/admin', methods = ['GET','POST'])
def admin_signin_page():
    if request.method == 'POST':
        # Call the sign_in function and pass user_id and password
        user_id = int(request.form['user_id'])
        password = request.form['password']
        if admin_sign_in(user_id,password) == False:
            # Show an error message if login fails
            error = 'Invalid user ID or password. Please try again.'
            print("Error")
            return render_template('admin_signin.html', error=error)
        print("redirecting....")
        return redirect('/admin/home')
    return render_template('admin_signin.html')  

# Function to assist in admin sign-in
# Checks if user is in the administrator table and if the passsword is correct
def admin_sign_in(user_id,password_hash):
    admin_check = f'SELECT user_id, password_hash FROM administrator WHERE user_id = {user_id};'
    statement = sqlalchemy.text(admin_check)
    res = db.execute(statement)
    db.commit()
    res_tuple = res.fetchall()
    print(password_hash)
    print(res_tuple[0][1])
    if len(res_tuple) > 0 and res_tuple[0][1] == password_hash:
        return True
    else:
        return False

# Admin management page
# Update the admin tables for extra permissions and displays current admins and their permissions
@app.route('/admin/update_admin', methods = ['GET','POST'])
def admin_update():
    if request.method == 'POST':
        user_id = int(request.form['user_id'])
        new_permissions = request.form['permissions']
        update_query = f"""UPDATE administrator 
                           SET permissions = '{new_permissions}'
                           WHERE user_id = {user_id};"""
        try:
            db.execute(sqlalchemy.text(update_query))
            db.commit()
            return redirect('/admin/update_admin')
        except Exception as e:
            db.rollback()
            return Response(str(e), 403)
        
    current_admins_query = "SELECT user_id, permissions FROM administrator;"
    current_admins = db.execute(sqlalchemy.text(current_admins_query))
    admins_tuple = current_admins.fetchall()
    db.commit()
    return render_template('admin_update.html', admins_tuple = admins_tuple)

# Adds an admin to the admistrator table
# uses admin_check to check validity
@app.route('/admin/add_admin', methods = ['POST'])
def add_admin():
    user_id = int(request.form['user_id'])
    password = request.form['password']
    permissions = request.form['permissions']
    if admin_check(user_id):
        print('checked!')
        insert_statement = f"""INSERT INTO administrator values (
                            {user_id}, '{password}', '{permissions}'
                            )
                            """
        try:
            db.execute(sqlalchemy.text(insert_statement))
            db.commit()
            return redirect('/admin/update_admin')
        except Exception as e:
            db.rollback()
            return Response(str(e), 403)
    return redirect('/admin/update_admin')

# Checks if the user already exists and if it is not currently already in the administrator table
def admin_check(user_id):
    user_id_check = f"""SELECT user_id 
                        FROM users 
                        WHERE user_id = {user_id}"""
    admin_exists_check = f"""SELECT user_id
                                FROM administrator
                                WHERE user_id = {user_id}"""
    user_exists = db.execute(sqlalchemy.text(user_id_check))
    admin_exists = db.execute(sqlalchemy.text(admin_exists_check))
    users_tuple = user_exists.fetchall()
    admin_tuple = admin_exists.fetchall()
    db.commit()
    if(len(users_tuple) > 0 and len(admin_tuple) == 0):
        return True
    return False

# Part of the admin management page, and remove the admin from the administrator table
@app.route('/admin/remove_admin', methods = ['POST'])
def remove_admin():
    user_id = request.form['user_id']
    remove_admin_statement = f'DELETE FROM administrator WHERE user_id = {user_id}'
    try:
        db.execute(sqlalchemy.text(remove_admin_statement))
        db.commit()
        return redirect('/admin/update_admin')
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)
        
# Table management page
# POST method allows admins to select and display specific tables
@app.route('/admin/update_tables', methods = ['GET','POST'])
def admin_update_tables():
    if request.method == 'POST':
        table = request.form['table']
        num_display = request.form['num_display']
        query = f'SELECT * FROM {table} LIMIT {num_display};'
        header_names = f"""
            SELECT column_name
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE table_name = '{table}'
            ORDER BY ordinal_position;
            """
        try:
            res = db.execute(sqlalchemy.text(query))
            headers = db.execute(sqlalchemy.text(header_names))
            res_tuple = res.fetchall()
            header_tuple = headers.fetchall()
            header_tuple = tuple(map(lambda x: x[0], header_tuple))
            db.commit()
            return render_template('admin_tables.html', table = table, header_names = header_tuple, query = res_tuple)
        except Exception as e:
            db.rollback()
            return Response(str(e), 403)
    return render_template('admin_tables.html')

# Adds a column to the specified table, part of the table management 
@app.route('/admin/add_col', methods = ['POST'])
def admin_add_col():
    table_to_alter = request.form['table_to_alter']
    column_name = request.form['column_name']
    type = request.form['type']
    contraints = request.form['constraints']
    alter_statement = f'ALTER TABLE {table_to_alter} ADD COLUMN {column_name} {type} {contraints};'
    try:
        db.execute(sqlalchemy.text(alter_statement))
        db.commit()
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)
    return redirect('/admin/update_tables')

# Removes a column from the specified table, part of table management
@app.route('/admin/drop_col', methods = ['POST'])
def admin_drop_col():
    table_to_alter = request.form['table_to_alter']
    column_name = request.form['column_name']
    alter_statement = f'ALTER TABLE {table_to_alter} DROP COLUMN {column_name};'
    try:
        db.execute(sqlalchemy.text(alter_statement))
        db.commit()
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)
    return redirect('/admin/update_tables')

# Renames the specified column, part of table management
@app.route('/admin/rename_col', methods = ['POST'])
def admin_rename_col():
    table_to_alter = request.form['table_to_alter']
    column_name = request.form['column_name']
    new_column_name = request.form['new_column_name']
    alter_statement = f'ALTER TABLE {table_to_alter} RENAME COLUMN {column_name} TO {new_column_name};'
    try:
        db.execute(sqlalchemy.text(alter_statement))
        db.commit()
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)
    return redirect('/admin/update_tables')

# Renames the specified table, part of table management
@app.route('/admin/rename_table', methods = ['POST'])
def admin_rename_table():
    table_to_alter = request.form['table_to_alter']
    new_table_name = request.form['new_table_name']
    alter_statement = f'ALTER TABLE {table_to_alter} RENAME TO {new_table_name};'
    try:
        db.execute(sqlalchemy.text(alter_statement))
        db.commit()
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)
    return redirect('/admin/update_tables')

# Drops the specified table, part of table management
@app.route('/admin/drop_table', methods = ['POST'])
def admin_drop_table():
    table_to_alter = request.form['table_to_alter']
    alter_statement =f'DROP TABLE IF EXISTS {table_to_alter};'
    try:
        db.execute(sqlalchemy.text(alter_statement))
        db.commit()
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)
    return redirect('/admin/update_tables')
    
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
    
# Update the admin page to include the data list query, part of the admin homepage
# Admins can make pre-specified queries to the database, as placed in the request_dict
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

# Allows admins to see 2 tables at once, joined, part of the admin homepage
# Does not work with 2 of the same table due to the use of natural join
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
# def bookslot(session_token, property_id):
#     if session_token in session:
#         for key, value in session.iteritems():
#             if value == session_token:
#                 user_id = key
#     property_booking = f'INSERT INTO BOOKING VALUES ({booking_id},{property_id},{user_id}, {start_date}, {end_date}, {today}, confirmed)'
#     res = db.execute(sqlalchemy.text(property_booking))
#     return res

# Checks if the property is available, by checking if the availability in the database == 'yes'
# def property_booking_check(property_id):
#     property_check = f'SELECT availibility FROM property WHERE property_id = {property_id}'
#     try:
#         res = db.execute(sqlalchemy.text(property_check))
#         res_tuple = res.fetchall()
#         db.commit()
#         availability = res_tuple[0][0]
#         if(availability == 'yes'): # just checks the availability in property for now, in the future, check the bookings table for start/end date availability as well
#             return True
#         else:
#             return False
#     except Exception as e:
#                 db.rollback()
#                 return Response(str(e),403)
        
    #return app
# ? This method can be used by waitress-serve CLI 
def create_app():
   return app
# ? The port where the debuggable DB management API is served
PORT = 5555
# ? Running the flask app on the localhost/0.0.0.0, port 2222
# ? Note that you may change the port, then update it in the view application too to make it work (don't if you don't have another application occupying it)
if __name__ == "__main__":
    app.run("0.0.0.0", PORT)
    # ? Uncomment the below lines and comment the above lines below `if __name__ == "__main__":` in order to run on the production server
    # ? Note that you may have to install waitress running `pip install waitress`
    # ? If you are willing to use waitress-serve command, please add `/home/sadm/.local/bin` to your ~/.bashrc
    # from waitress import serve
    # serve(app, host="0.0.0.0", port=PORT)
