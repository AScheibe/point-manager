# Import necessary libraries and modules
import unittest
from app import app, transactions, points
from flask import json

# Define the test case class, inheriting from unittest.TestCase
class FlaskAppTestCase(unittest.TestCase):

    # Setup method to prepare for each test case
    def setUp(self):
        # Configure the Flask app for testing mode
        app.config['TESTING'] = True
        # Initialize the test client for sending requests
        self.client = app.test_client()
        # Clear any existing transactions and points before each test case
        transactions.clear()
        points.clear()

    # Test that a valid transaction can be added
    def test_add_transaction(self):
        self.client.post('/reset')
        data = {
            "payer": "DANNON",
            "points": 300,
            "timestamp": "2023-09-28T12:00:00Z"
        }
        response = self.client.post("/add", data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(transactions[0], data)
        self.assertEqual(points["DANNON"], 300)

    # Test that a transaction with a missing field is rejected
    def test_add_transaction_missing_field(self):
        self.client.post('/reset')
        data = {
            "payer": "DANNON",
            "points": 300
        }

        response = self.client.post(
            "/add", data=json.dumps(data), content_type='application/json')

        # Check that the response status is 400 (Bad Request)
        self.assertEqual(response.status_code, 400)

        # Decode the response data and assert the error message
        response_data = json.loads(response.data)
        self.assertEqual(response_data["error"], "Required field missing")

    # Test spending more points than available
    def test_spend_points_not_enough(self):
        self.client.post('/reset')
        self.test_add_transaction()
        response = self.client.post(
            "/spend", data=json.dumps({"points": 400}), content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Not enough points.", response.data)

    # Test retrieving balance
    def test_balance(self):
        self.client.post('/reset')
        self.test_add_transaction()

        response = self.client.get("/balance")
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.data)
        self.assertEqual(response_data["DANNON"], 300)

    # Test the given sequence of adding transactions, spending points, and checking the balance
    def test_given_case(self):
        self.client.post('/reset')
        # Sample transactions for the test
        transactions_data = [
            {"payer": "DANNON", "points": 300, "timestamp": "2022-10-31T10:00:00Z"},
            {"payer": "UNILEVER", "points": 200,
                "timestamp": "2022-10-31T11:00:00Z"},
            {"payer": "DANNON", "points": -200,
                "timestamp": "2022-10-31T15:00:00Z"},
            {"payer": "MILLER COORS", "points": 10000,
                "timestamp": "2022-11-01T14:00:00Z"},
            {"payer": "DANNON", "points": 1000, "timestamp": "2022-11-02T14:00:00Z"}
        ]

        # Add all the sample transactions
        for data in transactions_data:
            response = self.client.post(
                "/add", data=json.dumps(data), content_type='application/json')
            self.assertEqual(response.status_code, 200)

        # Spend 5000 points
        response = self.client.post(
            "/spend", data=json.dumps({"points": 5000}), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Check the balance after spending
        response = self.client.get("/balance")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)

        # Expected balance after all operations
        expected_balance = {
            "DANNON": 1000,
            "UNILEVER": 0,
            "MILLER COORS": 5300
        }

        # Assert that the returned balance matches the expected balance
        self.assertDictEqual(response_data, expected_balance)

    def test_points_holdover(self):
        self.client.post('/reset')

        # Add a transaction with positive points
        response = self.client.post('/add', json={
            "payer": "DANNON",
            "points": 1000,
            "timestamp": "2023-09-28T12:00:00Z"
        })
        self.assertEqual(response.status_code, 200)

        # Spend only a part of the points, resulting in a holdover
        response = self.client.post('/spend', json={
            "points": 500
        })
        data = response.get_json()
        self.assertEqual(data, [{"payer": "DANNON", "points": -500}])

        # Spend the rest of the points, expecting it to come from the holdover
        response = self.client.post('/spend', json={
            "points": 500
        })
        
        data = response.get_json()
        self.assertEqual(data, [{"payer": "DANNON", "points": -500}])

        # Check the balance to ensure it's zero
        response = self.client.get('/balance')
        data = response.get_json()
        self.assertEqual(data["DANNON"], 0)

# Run the tests when the script is executed directly
if __name__ == "__main__":
    unittest.main()
