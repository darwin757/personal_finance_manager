from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.model.user import User
from app.model.account import Account

account_blueprint = Blueprint('account', __name__)

@account_blueprint.route('/accounts', methods=['POST'])
@jwt_required()
def create_account():
    user_id = get_jwt_identity()
    data = request.get_json()
    account = Account(user_id=user_id, name=data['name'], account_type=data['account_type'], balance=data.get('balance', 0.0))
    db.session.add(account)
    db.session.commit()
    return jsonify({'message': 'Account created successfully.'}), 201

@account_blueprint.route('/accounts/<int:account_id>', methods=['GET'])
@jwt_required()
def get_account(account_id):
    user_id = get_jwt_identity()
    account = Account.query.filter_by(user_id=user_id, id=account_id).first()
    if account:
        return jsonify({'name': account.name, 'account_type': account.account_type, 'balance': account.balance}), 200
    return jsonify({'message': 'Account not found'}), 404

@account_blueprint.route('/accounts/<int:account_id>', methods=['PUT'])
@jwt_required()
def update_account(account_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    account = Account.query.filter_by(user_id=user_id, id=account_id).first()
    if account:
        account.name = data['name']
        account.account_type = data['account_type']
        account.balance = data.get('balance', account.balance)
        db.session.commit()
        return jsonify({'message': 'Account updated successfully.'}), 200
    return jsonify({'message': 'Account not found'}), 404

@account_blueprint.route('/accounts/<int:account_id>', methods=['DELETE'])
@jwt_required()
def delete_account(account_id):
    user_id = get_jwt_identity()
    account = Account.query.filter_by(user_id=user_id, id=account_id).first()
    if account:
        db.session.delete(account)
        db.session.commit()
        return jsonify({'message': 'Account deleted successfully.'}), 204
    return jsonify({'message': 'Account not found'}), 404

