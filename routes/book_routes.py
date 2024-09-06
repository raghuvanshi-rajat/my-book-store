from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
mysql = MySQL()

book_blueprint = Blueprint('book', __name__)

# GET - Books list is accessible to everyone, so it's public route


@book_blueprint.route('/books', methods=['GET'])
def getAllBooks():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM books')
        books = cursor.fetchall()
        if len(books) > 0:
            # If there are books, return them as a JSON response
            return jsonify({'books': books})
        else:
            # If there are no books, return a message
            return make_response(jsonify(message='No books found'), 404)
    except Exception as e:
        # Handle exceptions (e.g., database connection issues)
        return make_response(jsonify({'message': 'Something went wrong!'}), 500)


# Function to check if logged in user is admin/user
def isAdmin():
    try:
        current_user = get_jwt_identity()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT registered_type FROM users WHERE email = %s', (current_user,))
        user_data = cursor.fetchone()
        if user_data and user_data['registered_type'] == 'admin':
            return True
        return False
    except Exception as e:
        return make_response(jsonify(message=f'User not authorized!'), 401)


# POST - Only 'admins' can insert the books into book store
@book_blueprint.route('/book', methods=['POST'])
@jwt_required()
def addBook():
    if request.is_json:
        if not isAdmin():
            return make_response(jsonify(message=f'You are not authorized for this!'), 401)
        data = request.get_json()
        # Validate required fields
        if 'title' in data and 'author' in data and 'ISBN' in data and 'price' in data and 'quantity' in data:
            book_title = data['title']
            book_author = data['author']
            book_ISBN = data['ISBN']
            book_price = data['price']
            book_quantity = data['quantity']
            try:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                # Check if the book already exists in the database
                cursor.execute(
                    'SELECT * FROM books WHERE ISBN = %s', (book_ISBN,))
                book = cursor.fetchone()
                if book:
                    msg = 'Book already exists in the database!'
                else:
                    # Store the book details in the database
                    cursor.execute('INSERT INTO books (title, author, ISBN, price, quantity) VALUES (%s, %s, %s, %s, %s)', (
                        book_title, book_author, book_ISBN, book_price, book_quantity))
                    mysql.connection.commit()
                    msg = f'Book with ISBN - {book_ISBN} has been added to the database!'
            except Exception as e:
                # Handle exceptions (e.g., database connection issues)
                return make_response(jsonify({'message': 'Something went wrong!'}), 500)
        else:
            msg = 'Please provide all required fields in JSON format! (title, author, ISBN, price, quantity)'
    else:
        msg = 'Please provide data in JSON format!'
    return make_response(jsonify({'message': msg}), 201)

# POST - Many books at a time


@book_blueprint.route('/books', methods=['POST'])
@jwt_required()
def addBooks():
    if request.is_json:
        if not isAdmin():
            return make_response(jsonify(message=f'You are not authorized for this!'), 401)

        data = request.get_json()

        if isinstance(data, list):
            try:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                success_messages = []
                error_messages = []

                for book_data in data:
                    if 'title' in book_data and 'author' in book_data and 'ISBN' in book_data and 'price' in book_data and 'quantity' in book_data:
                        book_title = book_data['title']
                        book_author = book_data['author']
                        book_ISBN = book_data['ISBN']
                        book_price = book_data['price']
                        book_quantity = book_data['quantity']

                        # Check if the book already exists in the database
                        cursor.execute(
                            'SELECT * FROM books WHERE ISBN = %s', (book_ISBN,))
                        book = cursor.fetchone()

                        if not book:
                            # Store the book details in the database
                            cursor.execute('INSERT INTO books (title, author, ISBN, price, quantity) VALUES (%s, %s, %s, %s, %s)', (
                                book_title, book_author, book_ISBN, book_price, book_quantity))
                            mysql.connection.commit()
                            success_messages.append(
                                f'Book with ISBN - {book_ISBN} has been added to the database!')
                        else:
                            error_messages.append(
                                f'Book with ISBN - {book_ISBN} already exists in the database!')

                    else:
                        error_messages.append(
                            'Please provide all required fields for each book in JSON format! (title, author, ISBN, price, quantity)')

                if success_messages:
                    msg = {'success_messages': success_messages}
                else:
                    msg = {'message': 'No books added.'}

                if error_messages:
                    msg['error_messages'] = error_messages

                return make_response(jsonify(msg), 200)

            except Exception as e:
                # Handle exceptions (e.g., database connection issues)
                return make_response(jsonify({'message': 'Something went wrong!'}), 500)

        else:
            return make_response(jsonify({'message': 'Please provide a list of books in JSON format!'}), 409)
    else:
        return make_response(jsonify({'message': 'Please provide data in JSON format!'}), 409)

# GET - Retrieve book by ISBN


@book_blueprint.route('/book/<isbn>', methods=['GET'])
def getBookByISBN(isbn):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM books WHERE ISBN = %s', (isbn,))
        book = cursor.fetchall()
        if len(book) > 0:
            # If there are books, return them as a JSON response
            return jsonify(book)
        else:
            # If there are no books, return a message
            return make_response(jsonify({'message': 'Book not found!'}), 404)
    except Exception as e:
        # Handle exceptions (e.g., database connection issues)
        return make_response(jsonify({'message': f'Something went wrong! {e}'}), 500)


# PUT - Update book by primaryKey - ISBN
@book_blueprint.route('/book/<isbn>', methods=['PUT'])
@jwt_required()
def updateBook(isbn):
    # Check if the user is an admin
    if not isAdmin():
        return make_response(jsonify({'message': 'You are not authorized for this!'}), 401)

    try:
        # Assuming the data comes in form format in the request
        data = request.form.to_dict()

        # Build the SET part of the query dynamically based on the provided fields
        set_query = ', '.join([
            f"{field} = %s" if field not in ['price', 'quantity'] else
            f"{field} = %s" if field == 'price' else
            f"{field} = %s" for field, value in data.items()
        ])

        # Construct the full SQL query
        update_query = f"UPDATE books SET {set_query} WHERE ISBN = %s"

        # Build the parameter tuple with appropriate data types
        params = [
            float(value) if field == 'price' else
            int(value) if field == 'quantity' else
            value for field, value in data.items()
        ] + [isbn]

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(update_query, tuple(params))
        mysql.connection.commit()

        # Check if the update was successful
        if cursor.rowcount > 0:
            # If there are updated rows, return a success message
            return make_response(jsonify({'message': 'Book updated successfully'}), 200)
        else:
            # If no rows were updated, it means the book with the provided ISBN was not found
            return make_response(jsonify({'message': 'Book not found!'}), 404)

    except Exception as e:
        # Handle exceptions (e.g., database connection issues)
        return make_response(jsonify({'message': f'Something went wrong! {e}'}), 500)


# DELETE - Book should be deleted only by the admin
@book_blueprint.route('/book/<isbn>', methods=['DELETE'])
@jwt_required()
def deleteBook(isbn):
    if not isAdmin():
        return make_response(jsonify(message='You are not authorized for this!'), 401)

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM books WHERE ISBN = %s', (isbn,))
        mysql.connection.commit()

        if cursor.rowcount > 0:
            return make_response(jsonify({'message': f'Successfully deleted the book - {isbn}!'}), 200)
        else:
            return make_response(jsonify({'message': 'Book not found!'}), 404)

    except Exception as e:
        return make_response(jsonify({'message': f'Something went wrong! {e}'}), 500)
