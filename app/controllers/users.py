from flask import Blueprint, jsonify, request
from flask_bcrypt import Bcrypt
from app import app
from app.models.User import User

bcrypt = Bcrypt(app)

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/register', methods=['POST'])
def register():
    data_user = request.get_json()
    print(data_user)

    errors_user = User.validate_register(data_user)
    if len(errors_user):
        return jsonify({ "errors":errors_user }), 400

    user_existant = User.get_user_by_email(data_user['email'])
    if user_existant:
        return jsonify({ "errors":'Este usuario ya existe' }), 409

    if 'password' in data_user and data_user['password']:
        data_user['password'] = bcrypt.generate_password_hash(data_user['password'])

    new_user_id = User.insert_user(data_user)
    if not new_user_id:
        return jsonify({ "errors":'Error en base de datos' }), 500

    return jsonify({ "user_id": new_user_id }), 201

@user_bp.route('/login', methods=['POST'])
def login():
    data_user = request.get_json()

    errors_user = User.validate_login(data_user)
    if len(errors_user):
        return jsonify({ "errors":errors_user }), 400

    user_existant = User.get_user_by_email(data_user['email'])
    if not user_existant:
        return jsonify({ "errors": 'Este usuario no existe' }), 404

    if 'password' in data_user and data_user['password']:
        validate_password = bcrypt.check_password_hash(user_existant[0].password, data_user['password'])
        if not validate_password:
            return jsonify({ "errors": 'Contraseña incorrecta' }), 409


    user = {
        "id_user": user_existant[0].id_user,
        "name": user_existant[0].name,
        "email": user_existant[0].email,
    }

    return jsonify({ "user":user }), 200

@user_bp.route('/elim', methods=['POST'])
def elim_all_users():
    elim_users = User.elim_all_users()
    return jsonify({ "message":"TODOS los usuarios eliminados", "elim_users":elim_users }), 200

@user_bp.route('/all_users', methods=['GET'])
def all_users():
    all_users = User.get_all_users()
    return jsonify({ "users": all_users }), 200