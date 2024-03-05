import unittest
import json
from app import create_app, db
from app.model.user import User
from app.model.account import Account
from flask_jwt_extended import create_access_token

class AccountManagementTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Create a test user
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('test')
        db.session.add(self.user)
        db.session.commit()


        # Generate a test JWT token for the user
        self.token = create_access_token(identity=self.user.id)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_account_creation(self):
        # Send a request to create an account
        response = self.client.post('/accounts', headers={'Authorization': f'Bearer {self.token}'},
                                    data=json.dumps({'name': 'Test Account', 'account_type': 'Checking', 'balance': 100}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('Account created successfully.', response.get_data(as_text=True))

    def test_get_account(self):
        # First, create an account
        account = Account(user_id=self.user.id, name='Savings Account', account_type='Savings', balance=500)
        db.session.add(account)
        db.session.commit()

        # Send a request to retrieve the account
        response = self.client.get(f'/accounts/{account.id}', headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Savings Account', response.get_data(as_text=True))

    def test_update_account(self):
        # Create an account to update
        account = Account(user_id=self.user.id, name='Update Test', account_type='Credit', balance=250)
        db.session.add(account)
        db.session.commit()

        # Send a request to update the account
        response = self.client.put(f'/accounts/{account.id}', headers={'Authorization': f'Bearer {self.token}'},
                                   data=json.dumps({'name': 'Updated Account', 'account_type': 'Credit', 'balance': 300}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Account updated successfully.', response.get_data(as_text=True))

    def test_delete_account(self):
        # Create an account to delete
        account = Account(user_id=self.user.id, name='Delete Test', account_type='Investment', balance=1000)
        db.session.add(account)
        db.session.commit()

        # Send a request to delete the account
        response = self.client.delete(f'/accounts/{account.id}', headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(response.status_code, 204)
        # Check if the account is really deleted
        account = Account.query.filter_by(id=account.id).first()
        self.assertIsNone(account)

if __name__ == '__main__':
    unittest.main()
