from app.config.db_connect import connectToMySQL

class Book:
    def __init__(self, data):
        self.id_book = data['id_book']
        self.title = data['title']
        self.author = data['author']
        self.genre = data['genre']
        self.description = data['description']
        self.pdf_url = data.get('pdf_path') or data.get('pdf_url')
        self.image_url = data.get('image_path') or data.get('image_url')
        self.pdf_id = data.get('pdf_id')
        self.image_id = data.get('image_id')
        self.user_id = data['user_id']

    @staticmethod
    def validate_book(book):
        errors = []
        book_existant = Book.get_book_by_title(book['title'])

        if not len(book['title']):
            errors.append('El libro debe tener un título')
        if len(book['title']) > 50:
            errors.append('El título no puede tener más de 50 carácteres')
        if not len(book['author']):
            errors.append('El libro debe tener un autor')
        if len(book['author']) > 30:
            errors.append('El autor no puede tener más de 30 carácteres')
        if not len(book['genre']):
            errors.append('El libro debe tener un género')
        if len(book['genre']) > 50:
            errors.append('El género no puede tener mayor a 50 carácteres')

        return errors

    @classmethod
    def get_book_by_title(cls, title):
        query = 'SELECT * FROM book WHERE title = %(title)s'
        book_existant = connectToMySQL('libroscope').query_db(query, {'title': title})
        book = []
        for db_book in book_existant:
            book.append(cls(db_book))
        return book

    @classmethod
    def get_book_by_genre(cls, genre):
        query = 'SELECT * FROM book WHERE genre = %(genre)s'
        book_existant = connectToMySQL('libroscope').query_db(query, {'genre': genre})
        book = []
        for db_book in book_existant:
            book.append(cls(db_book))
        return book

    @classmethod
    def get_book_by_id(cls, id_book):
        query = 'SELECT * FROM book WHERE id_book = %(id_book)s'
        book_existant = connectToMySQL('libroscope').query_db(query, {'id_book': id_book})
        print(book_existant)
        book = []
        for db_book in book_existant:
            book.append(cls(db_book))
        return book

    @classmethod
    def get_all_books_from_user(cls, user_id):
        query = 'SELECT * FROM book LEFT JOIN user ON book.user_id = user.id_user WHERE user.id_user = %(user_id)s'
        all_books = connectToMySQL('libroscope').query_db(query, {'user_id': user_id})
        return all_books

    @classmethod
    def get_all_books(cls):
        query = 'SELECT * FROM book'
        all_books = connectToMySQL('libroscope').query_db(query)
        return all_books

    @classmethod
    def insert_book(cls, data):
        query = 'INSERT INTO book (title, author, genre, description, user_id, pdf_url, image_url, pdf_id, image_id) VALUES (%(title)s, %(author)s, %(genre)s, %(description)s, %(user_id)s, %(pdf_url)s, %(image_url)s, %(pdf_id)s, %(image_id)s)'
        new_book = connectToMySQL('libroscope').query_db(query, data)
        return new_book

    @classmethod
    def delete_book(cls, id_book):
        query_book = 'SELECT * FROM book WHERE id_book = %(id_book)s'
        book_existant = connectToMySQL('libroscope').query_db(query_book, { 'id_book':id_book })
        if not book_existant:
            return False
        query = 'DELETE FROM book WHERE id_book = %(id_book)s'
        connectToMySQL('libroscope').query_db(query, { 'id_book':id_book })
        return True