from app.config.db_connect import connectToMySQL
import re

class User:
    def __init__(self, data):
        self.id_user = data['id_user']
        self.name = data['name']
        self.email = data['email']
        self.password = data['password']
        self.google_id = data['google_id']
        self.admin = data['admin']

    @staticmethod
    def validate_register(user):
        errors = []
        regex_email = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        regex_password = r"^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,15}$"

        if not len(user['name']):
            errors.append('El nombre no puede estar vacío')
        if len(user['name']) < 2:
            errors.append('El nombre debe tener el menos 2 carácteres')
        if not re.fullmatch(regex_email, user['email']):
            errors.append('El email debe ser válido')
        if User.get_user_by_email(user['email']):
            errors.append('Este usuario ya existe')
        if 'password' in user and user['password']:
            if not len(user['password']):
                errors.append('Debes tener una contraseña')
            if len(user['password']) < 8 or len(user['password']) > 15:
                errors.append('La contraseña debe tener de 8 a 15 carácteres')
            if not re.fullmatch(regex_password, user['password']):
                errors.append('La contraseña debe tener al menos: una letra mayúscula, una letra minúscula y al menos un carácter especial')
        return errors

    @staticmethod
    def validate_login(user):
        errors = []
        regex_email = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        regex_password = r"^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,15}$"

        if not re.fullmatch(regex_email, user['email']):
            errors.append('El email debe ser válido')
        if not len(user['email']):
            errors.append('El email no puede estar vacío')
        if 'password' in user and user['password']:
            if not len(user['password']):
                errors.append('La contraseña no puede estar vacía')
        return errors

    @classmethod
    def insert_user(cls, data):
        data.setdefault('password', None)
        data.setdefault('google_id', None)
        data.setdefault('admin', False)
        query = 'INSERT INTO user (name, email, password, google_id, admin) VALUES (%(name)s, %(email)s, %(password)s, %(google_id)s, %(admin)s)'
        new_user = connectToMySQL('libroscope').query_db(query, data)
        return new_user

    @classmethod
    def get_user_by_email(cls, email):
        query = 'SELECT * FROM user WHERE email = %(email)s'
        db_user = connectToMySQL('libroscope').query_db(query, {'email': email})
        user = []
        for user_existant in db_user:
            user.append(cls(user_existant))
        return user
        
    @classmethod
    def get_user_by_id(cls, id_user):
        query = 'SELECT * FROM user WHERE id_user = %(id_user)s'
        db_user = connectToMySQL('libroscope').query_db(query, {'id_user': id_user})
        user = []
        for user_existant in db_user:
            user.append(cls(user_existant))
        return user

    @classmethod
    def get_all_users(cls):
        query = 'SELECT * FROM user'
        db_users = connectToMySQL('libroscope').query_db(query)
        return db_users

    @classmethod
    def elim_all_users(cls):
        query = 'DELETE FROM user'
        elim_users = connectToMySQL('libroscope').query_db(query)
        return elim_users