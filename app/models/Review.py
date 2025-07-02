from app.config.db_connect import connectToMySQL

class Review:
    def __init__(self, data):
        self.id_review = data['id_review']
        self.description = data['description']
        self.id_user = data['id_user']

    @staticmethod
    def validate_review(rev):
        errors = []

        if not len(rev['description']):
            errors.append('La descripción no puede estar vacía')
        if not rev['id_user']:
            errors.append('La descripción debe pertencer a un usuario')
        return errors

    @classmethod
    def get_reviews_from_user(cls):
        query = 'SELECT * FROM review LEFT JOIN user ON review.id_user = user.id_user'
        all_reviews = connectToMySQL('libroscope').query_db(query)
        return all_reviews

    @classmethod
    def get_all_reviews(cls):
        query = 'SELECT * FROM review'
        return connectToMySQL('libroscope').query_db(query)

    @classmethod
    def insert_review(cls, data):
        query = 'INSERT INTO review (description, id_user) VALUES (%(description)s, %(id_user)s)'
        return connectToMySQL('libroscope').query_db(query, data)

    @classmethod
    def delete_review(cls, id_review):
        query_review = 'SELECT * FROM review WHERE id_review = %(id_review)s'
        review_existant = connectToMySQL('libroscope').query_db(query_review, { 'id_review':id_review })
        if not review_existant:
            return False

        query = 'DELETE FROM review WHERE id_review = %(id_review)s'
        connectToMySQL('libroscope').query_db(query, { 'id_review':id_review })
        return True