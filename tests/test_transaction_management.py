import unittest
import json
from app import create_app, db
from app.model.user import User
from app.model.account import Account
from app.model.transaction import Transaction
from flask_jwt_extended import create_access_token
from datetime import datetime, timedelta

class TransactionManagementTestCase(unittest.TestCase):
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

        # Create a test account
        self.account = Account(user_id=self.user.id, name='Test Account', account_type='Checking', balance=1000.0)
        db.session.add(self.account)
        db.session.commit()

        # Generate a test JWT token for the user
        self.token = create_access_token(identity=self.user.id)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_income_transaction(self):
        """Test creating an income transaction."""
        response = self.client.post('/transactions',
                                    headers={'Authorization': f'Bearer {self.token}'},
                                    data=json.dumps({
                                        'account_id': self.account.id,
                                        'amount': 500.0,
                                        'transaction_type': 'income',
                                        'category': 'Salary',
                                        'description': 'Monthly salary'
                                    }),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('Transaction created successfully', data['message'])

        # Check that account balance was updated
        updated_account = Account.query.get(self.account.id)
        self.assertEqual(updated_account.balance, 1500.0)

    def test_create_expense_transaction(self):
        """Test creating an expense transaction."""
        response = self.client.post('/transactions',
                                    headers={'Authorization': f'Bearer {self.token}'},
                                    data=json.dumps({
                                        'account_id': self.account.id,
                                        'amount': 150.0,
                                        'transaction_type': 'expense',
                                        'category': 'Groceries',
                                        'description': 'Weekly groceries'
                                    }),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # Check that account balance was updated
        updated_account = Account.query.get(self.account.id)
        self.assertEqual(updated_account.balance, 850.0)

    def test_create_transaction_invalid_type(self):
        """Test creating a transaction with invalid type."""
        response = self.client.post('/transactions',
                                    headers={'Authorization': f'Bearer {self.token}'},
                                    data=json.dumps({
                                        'account_id': self.account.id,
                                        'amount': 100.0,
                                        'transaction_type': 'invalid',
                                        'category': 'Test'
                                    }),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_create_transaction_missing_fields(self):
        """Test creating a transaction with missing required fields."""
        response = self.client.post('/transactions',
                                    headers={'Authorization': f'Bearer {self.token}'},
                                    data=json.dumps({
                                        'account_id': self.account.id,
                                        'amount': 100.0
                                    }),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_create_transaction_negative_amount(self):
        """Test creating a transaction with negative amount."""
        response = self.client.post('/transactions',
                                    headers={'Authorization': f'Bearer {self.token}'},
                                    data=json.dumps({
                                        'account_id': self.account.id,
                                        'amount': -100.0,
                                        'transaction_type': 'income',
                                        'category': 'Test'
                                    }),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_create_transaction_invalid_account(self):
        """Test creating a transaction with non-existent account."""
        response = self.client.post('/transactions',
                                    headers={'Authorization': f'Bearer {self.token}'},
                                    data=json.dumps({
                                        'account_id': 99999,
                                        'amount': 100.0,
                                        'transaction_type': 'income',
                                        'category': 'Test'
                                    }),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_get_transaction(self):
        """Test retrieving a specific transaction."""
        # Create a transaction
        transaction = Transaction(
            user_id=self.user.id,
            account_id=self.account.id,
            amount=200.0,
            transaction_type='income',
            category='Freelance',
            description='Freelance work'
        )
        db.session.add(transaction)
        db.session.commit()

        response = self.client.get(f'/transactions/{transaction.id}',
                                   headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['amount'], 200.0)
        self.assertEqual(data['category'], 'Freelance')

    def test_get_nonexistent_transaction(self):
        """Test retrieving a non-existent transaction."""
        response = self.client.get('/transactions/99999',
                                   headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(response.status_code, 404)

    def test_list_transactions(self):
        """Test listing all transactions."""
        # Create multiple transactions
        for i in range(5):
            transaction = Transaction(
                user_id=self.user.id,
                account_id=self.account.id,
                amount=100.0 * (i + 1),
                transaction_type='income' if i % 2 == 0 else 'expense',
                category=f'Category {i}',
                description=f'Test transaction {i}'
            )
            db.session.add(transaction)
        db.session.commit()

        response = self.client.get('/transactions',
                                   headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['transactions']), 5)
        self.assertEqual(data['total'], 5)

    def test_list_transactions_with_filters(self):
        """Test listing transactions with filters."""
        # Create transactions
        income_transaction = Transaction(
            user_id=self.user.id,
            account_id=self.account.id,
            amount=500.0,
            transaction_type='income',
            category='Salary'
        )
        expense_transaction = Transaction(
            user_id=self.user.id,
            account_id=self.account.id,
            amount=100.0,
            transaction_type='expense',
            category='Food'
        )
        db.session.add_all([income_transaction, expense_transaction])
        db.session.commit()

        # Filter by transaction type
        response = self.client.get('/transactions?transaction_type=income',
                                   headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['transactions']), 1)
        self.assertEqual(data['transactions'][0]['transaction_type'], 'income')

        # Filter by category
        response = self.client.get('/transactions?category=Food',
                                   headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['transactions']), 1)
        self.assertEqual(data['transactions'][0]['category'], 'Food')

    def test_update_transaction(self):
        """Test updating a transaction."""
        # Create a transaction
        transaction = Transaction(
            user_id=self.user.id,
            account_id=self.account.id,
            amount=200.0,
            transaction_type='income',
            category='Freelance'
        )
        db.session.add(transaction)
        db.session.commit()

        initial_balance = self.account.balance

        # Update the transaction
        response = self.client.put(f'/transactions/{transaction.id}',
                                   headers={'Authorization': f'Bearer {self.token}'},
                                   data=json.dumps({
                                       'amount': 300.0,
                                       'category': 'Consulting'
                                   }),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Verify update
        updated_transaction = Transaction.query.get(transaction.id)
        self.assertEqual(updated_transaction.amount, 300.0)
        self.assertEqual(updated_transaction.category, 'Consulting')

    def test_update_transaction_type(self):
        """Test updating a transaction type (income to expense)."""
        # Create an income transaction
        transaction = Transaction(
            user_id=self.user.id,
            account_id=self.account.id,
            amount=200.0,
            transaction_type='income',
            category='Test'
        )
        db.session.add(transaction)
        self.account.balance += 200.0
        db.session.commit()

        initial_balance = self.account.balance

        # Change to expense
        response = self.client.put(f'/transactions/{transaction.id}',
                                   headers={'Authorization': f'Bearer {self.token}'},
                                   data=json.dumps({
                                       'transaction_type': 'expense'
                                   }),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Balance should be initial - 200 (revert income) - 200 (apply expense) = initial - 400
        updated_account = Account.query.get(self.account.id)
        self.assertEqual(updated_account.balance, initial_balance - 400.0)

    def test_delete_transaction(self):
        """Test deleting a transaction."""
        # Create a transaction
        transaction = Transaction(
            user_id=self.user.id,
            account_id=self.account.id,
            amount=100.0,
            transaction_type='expense',
            category='Test'
        )
        db.session.add(transaction)
        self.account.balance -= 100.0
        db.session.commit()

        initial_balance = self.account.balance

        # Delete the transaction
        response = self.client.delete(f'/transactions/{transaction.id}',
                                      headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(response.status_code, 200)

        # Verify deletion
        deleted_transaction = Transaction.query.get(transaction.id)
        self.assertIsNone(deleted_transaction)

        # Verify balance was reverted
        updated_account = Account.query.get(self.account.id)
        self.assertEqual(updated_account.balance, initial_balance + 100.0)

    def test_transaction_summary(self):
        """Test getting transaction summary."""
        # Create multiple transactions
        transactions_data = [
            {'amount': 1000.0, 'type': 'income', 'category': 'Salary'},
            {'amount': 500.0, 'type': 'income', 'category': 'Freelance'},
            {'amount': 200.0, 'type': 'expense', 'category': 'Groceries'},
            {'amount': 150.0, 'type': 'expense', 'category': 'Transport'},
            {'amount': 100.0, 'type': 'expense', 'category': 'Groceries'}
        ]

        for data in transactions_data:
            transaction = Transaction(
                user_id=self.user.id,
                account_id=self.account.id,
                amount=data['amount'],
                transaction_type=data['type'],
                category=data['category']
            )
            db.session.add(transaction)
        db.session.commit()

        response = self.client.get('/transactions/summary',
                                   headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertEqual(data['total_income'], 1500.0)
        self.assertEqual(data['total_expenses'], 450.0)
        self.assertEqual(data['net'], 1050.0)
        self.assertEqual(data['transaction_count'], 5)

        # Check category breakdown
        self.assertIn('Groceries', data['category_breakdown'])
        self.assertEqual(data['category_breakdown']['Groceries']['expense'], 300.0)

    def test_transaction_summary_with_date_filter(self):
        """Test getting transaction summary with date filters."""
        # Create transactions with different dates
        today = datetime.utcnow()
        yesterday = today - timedelta(days=1)

        old_transaction = Transaction(
            user_id=self.user.id,
            account_id=self.account.id,
            amount=500.0,
            transaction_type='income',
            category='Old',
            date=yesterday
        )
        new_transaction = Transaction(
            user_id=self.user.id,
            account_id=self.account.id,
            amount=300.0,
            transaction_type='income',
            category='New',
            date=today
        )
        db.session.add_all([old_transaction, new_transaction])
        db.session.commit()

        # Get summary for today only
        start_date = today.strftime('%Y-%m-%d')
        response = self.client.get(f'/transactions/summary?start_date={start_date}',
                                   headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total_income'], 300.0)
        self.assertEqual(data['transaction_count'], 1)

if __name__ == '__main__':
    unittest.main()
