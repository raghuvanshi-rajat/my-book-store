import unittest
from app import app
import requests
import os
from dotenv import load_dotenv

load_dotenv()


def get_auth_token():
    login_data = {
        'email': os.getenv('USER_EMAIL'),
        'password': os.getenv('USER_PASSWORD')
    }
    login_response = requests.post(
        'http://localhost:3000/api/login', json=login_data)

    # Check if the login was successful
    if login_response.status_code == 200:
        # Extract the authentication token from the response
        auth_token = login_response.json().get('access_token')
        return auth_token
    else:
        # Handle authentication failure
        raise Exception(
            f'Authentication failed. Status code: {login_response.status_code}')


class BookStoreAPITests(unittest.TestCase):

    def setUp(self):
        # Set up a test client
        self.app = app.test_client()

        # Get an authentication token
        self.auth_token = get_auth_token()

    # Ensure that tests are executed in a specific order
    def test_01_create_book(self):
        # Add headers with the authentication token to the request
        response = self.app.post('/api/book', headers={'Authorization': f'Bearer {self.auth_token}'}, json={
            'title': 'Test Book',
            'author': 'Test Author',
            'ISBN': '1234567890',
            'price': 19.99,
            'quantity': 10
        })
        self.assertEqual(response.status_code, 201)

    def test_02_get_book_by_isbn(self):
        isbn = "1234567890"
        response = self.app.get(f'http://localhost:3000/api/book/{isbn}')
        self.assertEqual(response.status_code, 200)
        # Add more assertions based on the expected response

    def test_03_update_book_by_isbn(self):
        isbn = "1234567890"
        update_data = {
            "price": 25.0,
            "quantity": 60
        }

        # Use the 'data' parameter instead of 'json' for form data
        response = self.app.put(
            f'http://localhost:3000/api/book/{isbn}',
            headers={'Authorization': f'Bearer {self.auth_token}'},
            data=update_data
        )

        self.assertEqual(response.status_code, 200)

    def test_04_delete_book_by_isbn(self):
        isbn = "1234567890"

        # Send a DELETE request with the authentication token
        response = self.app.delete(f'http://localhost:3000/api/book/{isbn}', headers={
                                   'Authorization': f'Bearer {self.auth_token}'})

        # Assert the response status code
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
