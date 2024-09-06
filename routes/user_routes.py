from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import bcrypt

user_blueprint = Blueprint('user', __name__)
mysql = MySQL()


@user_blueprint.route('/login', methods=['POST'])
def login():
    msg = 'Please register!'
    if request.is_json:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account and bcrypt.checkpw(password.encode('utf-8'), account['password'].encode('utf-8')):
            access_token = create_access_token(identity=email)
            status_code = 200
            msg = 'Logged in successfully!'
            response = make_response(jsonify(
                {'message': msg, 'access_token': access_token, 'email': email}), status_code)
        else:
            msg = 'Incorrect username / password !'
            status_code = 401
            response = make_response(jsonify({'message': msg}), status_code)
    return response


@user_blueprint.route('/register', methods=['POST'])
def register():
    msg = ''
    if request.is_json:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        registered_type = data.get('registered_type')
        # Hash the password before storing
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt())
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            account = cursor.fetchone()
            if account:
                msg = 'Account already exists!'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Invalid email address!'
            else:
                # Store the hashed password in the database
                cursor.execute('INSERT INTO users (email, password, registered_type) VALUES (%s, %s, %s)', (
                    email, hashed_password, registered_type))
                mysql.connection.commit()
                msg = 'You have successfully been registered!'
                return make_response(jsonify({'message': msg}), 201)
        except Exception as e:
            return make_response(jsonify({'message': f'Something went wrong!'}), 500)
    else:
        msg = 'Please provide JSON data.'
    return make_response(jsonify({'message': msg}), 409)
