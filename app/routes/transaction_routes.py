from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.model.user import User
from app.model.account import Account
from app.model.transaction import Transaction
from datetime import datetime

transaction_blueprint = Blueprint('transaction', __name__)

@transaction_blueprint.route('/transactions', methods=['POST'])
@jwt_required()
def create_transaction():
    """Create a new transaction (income or expense)."""
    user_id = get_jwt_identity()
    data = request.get_json()

    # Validate required fields
    required_fields = ['account_id', 'amount', 'transaction_type', 'category']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400

    # Validate transaction type
    if data['transaction_type'] not in ['income', 'expense']:
        return jsonify({'message': 'Transaction type must be either "income" or "expense"'}), 400

    # Verify account belongs to user
    account = Account.query.filter_by(id=data['account_id'], user_id=user_id).first()
    if not account:
        return jsonify({'message': 'Account not found or does not belong to user'}), 404

    # Validate amount is positive
    if data['amount'] <= 0:
        return jsonify({'message': 'Amount must be greater than 0'}), 400

    # Parse date if provided, otherwise use current datetime
    transaction_date = datetime.utcnow()
    if 'date' in data and data['date']:
        try:
            transaction_date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'message': 'Invalid date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)'}), 400

    # Create transaction
    transaction = Transaction(
        user_id=user_id,
        account_id=data['account_id'],
        amount=data['amount'],
        transaction_type=data['transaction_type'],
        category=data['category'],
        description=data.get('description', ''),
        date=transaction_date
    )

    # Update account balance
    if transaction.transaction_type == 'income':
        account.balance += transaction.amount
    else:  # expense
        account.balance -= transaction.amount

    db.session.add(transaction)
    db.session.commit()

    return jsonify({
        'message': 'Transaction created successfully.',
        'transaction': transaction.to_dict()
    }), 201

@transaction_blueprint.route('/transactions/<int:transaction_id>', methods=['GET'])
@jwt_required()
def get_transaction(transaction_id):
    """Get a specific transaction by ID."""
    user_id = get_jwt_identity()
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=user_id).first()

    if not transaction:
        return jsonify({'message': 'Transaction not found'}), 404

    return jsonify(transaction.to_dict()), 200

@transaction_blueprint.route('/transactions', methods=['GET'])
@jwt_required()
def list_transactions():
    """List all transactions for the authenticated user with optional filters."""
    user_id = get_jwt_identity()

    # Start with base query
    query = Transaction.query.filter_by(user_id=user_id)

    # Apply filters from query parameters
    account_id = request.args.get('account_id', type=int)
    if account_id:
        query = query.filter_by(account_id=account_id)

    transaction_type = request.args.get('transaction_type')
    if transaction_type:
        if transaction_type not in ['income', 'expense']:
            return jsonify({'message': 'Invalid transaction_type. Must be "income" or "expense"'}), 400
        query = query.filter_by(transaction_type=transaction_type)

    category = request.args.get('category')
    if category:
        query = query.filter_by(category=category)

    # Date range filters
    start_date = request.args.get('start_date')
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Transaction.date >= start_dt)
        except ValueError:
            return jsonify({'message': 'Invalid start_date format. Use ISO format (YYYY-MM-DD)'}), 400

    end_date = request.args.get('end_date')
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Transaction.date <= end_dt)
        except ValueError:
            return jsonify({'message': 'Invalid end_date format. Use ISO format (YYYY-MM-DD)'}), 400

    # Order by date (most recent first)
    query = query.order_by(Transaction.date.desc())

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    if per_page > 100:
        per_page = 100

    paginated_transactions = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'transactions': [t.to_dict() for t in paginated_transactions.items],
        'total': paginated_transactions.total,
        'page': page,
        'per_page': per_page,
        'total_pages': paginated_transactions.pages
    }), 200

@transaction_blueprint.route('/transactions/<int:transaction_id>', methods=['PUT'])
@jwt_required()
def update_transaction(transaction_id):
    """Update an existing transaction."""
    user_id = get_jwt_identity()
    data = request.get_json()

    transaction = Transaction.query.filter_by(id=transaction_id, user_id=user_id).first()
    if not transaction:
        return jsonify({'message': 'Transaction not found'}), 404

    # Get the account
    account = Account.query.filter_by(id=transaction.account_id, user_id=user_id).first()
    if not account:
        return jsonify({'message': 'Account not found'}), 404

    # Revert the old transaction from account balance
    if transaction.transaction_type == 'income':
        account.balance -= transaction.amount
    else:  # expense
        account.balance += transaction.amount

    # Update transaction fields
    if 'amount' in data:
        if data['amount'] <= 0:
            return jsonify({'message': 'Amount must be greater than 0'}), 400
        transaction.amount = data['amount']

    if 'transaction_type' in data:
        if data['transaction_type'] not in ['income', 'expense']:
            return jsonify({'message': 'Transaction type must be either "income" or "expense"'}), 400
        transaction.transaction_type = data['transaction_type']

    if 'category' in data:
        transaction.category = data['category']

    if 'description' in data:
        transaction.description = data['description']

    if 'date' in data and data['date']:
        try:
            transaction.date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'message': 'Invalid date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)'}), 400

    # Apply the updated transaction to account balance
    if transaction.transaction_type == 'income':
        account.balance += transaction.amount
    else:  # expense
        account.balance -= transaction.amount

    db.session.commit()

    return jsonify({
        'message': 'Transaction updated successfully.',
        'transaction': transaction.to_dict()
    }), 200

@transaction_blueprint.route('/transactions/<int:transaction_id>', methods=['DELETE'])
@jwt_required()
def delete_transaction(transaction_id):
    """Delete a transaction."""
    user_id = get_jwt_identity()
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=user_id).first()

    if not transaction:
        return jsonify({'message': 'Transaction not found'}), 404

    # Get the account and revert the transaction
    account = Account.query.filter_by(id=transaction.account_id, user_id=user_id).first()
    if account:
        if transaction.transaction_type == 'income':
            account.balance -= transaction.amount
        else:  # expense
            account.balance += transaction.amount

    db.session.delete(transaction)
    db.session.commit()

    return jsonify({'message': 'Transaction deleted successfully.'}), 200

@transaction_blueprint.route('/transactions/summary', methods=['GET'])
@jwt_required()
def get_transaction_summary():
    """Get a summary of transactions (total income, total expenses, net)."""
    user_id = get_jwt_identity()

    # Apply optional filters
    query = Transaction.query.filter_by(user_id=user_id)

    account_id = request.args.get('account_id', type=int)
    if account_id:
        query = query.filter_by(account_id=account_id)

    start_date = request.args.get('start_date')
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Transaction.date >= start_dt)
        except ValueError:
            return jsonify({'message': 'Invalid start_date format'}), 400

    end_date = request.args.get('end_date')
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Transaction.date <= end_dt)
        except ValueError:
            return jsonify({'message': 'Invalid end_date format'}), 400

    # Calculate totals
    all_transactions = query.all()
    total_income = sum(t.amount for t in all_transactions if t.transaction_type == 'income')
    total_expenses = sum(t.amount for t in all_transactions if t.transaction_type == 'expense')
    net = total_income - total_expenses

    # Category breakdown
    category_breakdown = {}
    for transaction in all_transactions:
        if transaction.category not in category_breakdown:
            category_breakdown[transaction.category] = {
                'income': 0,
                'expense': 0
            }
        if transaction.transaction_type == 'income':
            category_breakdown[transaction.category]['income'] += transaction.amount
        else:
            category_breakdown[transaction.category]['expense'] += transaction.amount

    return jsonify({
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net': net,
        'transaction_count': len(all_transactions),
        'category_breakdown': category_breakdown
    }), 200
