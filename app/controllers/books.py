from flask import Blueprint, request, jsonify, send_from_directory, current_app
from elasticsearch import Elasticsearch
from app import app
from app.models.Book import Book
from werkzeug.utils import secure_filename
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import OneHotEncoder
# Codificar Title y Authors para recomendaciones
from sklearn.feature_extraction.text import TfidfVectorizer
import requests
import random
import os
import pandas as pd
import numpy as np

book_bp = Blueprint('book_bp', __name__)

#ElasticSearch config
es = Elasticsearch('http://localhost:9200')
client_info = es.info()
print('CONNECTED TO ELASTICSEARCH')

# Crear índice con una réplica, en caso que el primer index falle
my_index = 'google_books'
es.indices.delete(index=my_index, ignore_unavailable=True)
es.indices.create(
    index=my_index,
    body={
        'mappings':{
            'properties':{
                'volumeInfo':{
                    'properties':{
                        'title': {'type': 'text'},
                        'authors': {'type': 'text'},
                        'categories': {'type': 'text'},
                    }
                }
            }
        }
    }
)

my_books_index = 'my_books'
es.indices.delete(index=my_books_index, ignore_unavailable=True)
es.indices.create(
    index=my_books_index,
    body={
        'mappings':{
            'properties':{
                'title': {'type': 'text'},
                'author': {'type': 'text'},
                'genre': {'type': 'text'},
            }
        }
    }
)

# Búsqueda de libros, tanto de Google como creados
@book_bp.route('/search/<categorie>/<query>', methods=['POST'])
def search_books(query, categorie):
    if not len(query):
        return jsonify({ "errors": 'No puede estar vacío' }), 400
        
    if categorie == 'none':
        response = requests.get('https://www.googleapis.com/books/v1/volumes?q=fiction&maxResults=40&key=AIzaSyDNQ631Qv6pa6tyXCeU1xds2mnYL1KYNg8')
        if response.status_code == 200:
            google_books = response.json()
            for i, book in enumerate(google_books['items']):
                es.index(index=my_index, id=i+1, body=book)
    # elif categorie == 'community':
        
    elif len(categorie) and categorie != 'none':
        response = requests.get(f'https://www.googleapis.com/books/v1/volumes?q=subject:{categorie}&maxResults=40&key=AIzaSyDNQ631Qv6pa6tyXCeU1xds2mnYL1KYNg8')
        if response.status_code == 200:
            google_books = response.json()
            for i, book in enumerate(google_books['items']):
                es.index(index=my_index, id=i+1, body=book)
    else:
        print(f'Error: {google_books.status_code}')

    all_books = Book.get_all_books()

    for i, book in enumerate(all_books):
        es.index(index=my_books_index, id=i+1, body=book)

    matching_books = []

    matching_google_books = es.search(
        index=my_index,
        body={
            'size': 50,
            'query':{
                'multi_match':{
                    'query': query,
                    'fields': [
                        'volumeInfo.title^3',
                        'volumeInfo.authors',
                        'volumeInfo.categories'
                    ],
                    'fuzziness': 'AUTO'
                }
            }
        }
    )
    matching_books.extend([hit['_source'] for hit in matching_google_books['hits']['hits']])

    matching_my_books = es.search(
        index=my_books_index,
        body={
            'size': 50,
            'query':{
                'multi_match':{
                    'query': query,
                    'fields': [
                        'title^3',
                        'author',
                        'genre'
                    ],
                    'fuzziness': 'AUTO'
                }
            }
        }
    )
    matching_books.extend([hit['_source'] for hit in matching_my_books['hits']['hits']])

    return jsonify({ "matching_books": matching_books }), 200

# Sist de recomendaciones
@book_bp.route('/recommend', methods=['POST'])
def recommend_books():
    book = request.get_json()
    title = book['volumeInfo'].get('title')
    categories = book['volumeInfo'].get('categories', [])
    if categories:
        categorie = categories[0]
    else:
        categorie = 'fiction'

    response = requests.get(f'https://www.googleapis.com/books/v1/volumes?q=subject:{categorie}&maxResults=40&key=AIzaSyDNQ631Qv6pa6tyXCeU1xds2mnYL1KYNg8')
    if response.status_code != 200:
        return jsonify({ "errors": 'Error al obtener libros de Google Book' }), 500

    google_books = response.json()
    books = google_books.get('items', [])
    if not books:
        return jsonify({ "errors": 'No se encontraron libros de esta categoría' }), 404

    # Creamos la lista de los datos para transformarlos a un DataFrame
    book_list = []
    for item in books:
        volumeInfo = item.get('volumeInfo', {})
        book_list.append({
            'title': volumeInfo.get('title'),
            'authors': volumeInfo.get('authors'),
             # Si no hay 1era categorie por defecto es 'unknown'
            'categories': volumeInfo.get('categories', ['unknown'])[0]
        })

    # Agregamos manualmente el libro recibido por POST al listado
    book_title = book['volumeInfo'].get('title', 'unknown')
    book_categories = book['volumeInfo'].get('categories', ['unknown'])
    book_list.append({
        'title': book_title,
        'categories': book_categories[0]
    })
    # Creamos el DataFrame
    df = pd.DataFrame(book_list).drop_duplicates(subset='title')
    # Codificador para title (tansformar texto a números según su importancia)
    tfidf_title = TfidfVectorizer()
    title_encoder = tfidf_title.fit_transform(df['title']).toarray()
    # Actualizamos la lista de authors a un string completo, si es una lista las une con un espacio ' ', si no se queda como está
    df['authors'] = df['authors'].apply(lambda author: ' '.join(author) if isinstance(author, list) else author)
    # Reemplazar un valor null por un string vacío ''
    df['authors'] = df['authors'].fillna('')
    # Codificar authors
    tfidf_authors = TfidfVectorizer()
    author_encoder = tfidf_authors.fit_transform(df['authors']).toarray()
    # Codificador categorie
    encoder = OneHotEncoder(sparse_output=False)
    categorie_encoder = encoder.fit_transform(df[['categories']])
    # Creamos la matriz juntando los valores
    matrix = np.hstack((title_encoder, author_encoder, categorie_encoder))
    similarity_matrix = cosine_similarity(matrix)
    # DataFrame ordenado por title
    similarity_df = pd.DataFrame(similarity_matrix, index=df['title'], columns=df['title'])
    if title not in similarity_df.columns:
        return jsonify({ "errors": f'El libro {title} no fue encontrado en la base de datos' }), 404
    similar_books = similarity_df[title].drop(title).sort_values(ascending=False).head(3)
    print(similar_books.to_dict())
    recommend_books = []
    # Obtener items de google_books
    books_from_google = google_books.get('items')
    added_titles = set()
    
    for book in books:
        volumeInfo = book.get('volumeInfo', {})
        title = volumeInfo.get('title', '')
        if title in similar_books and title not in added_titles:
            recommend_books.append(book)
            added_titles.add(title)

    return jsonify({ "recommend_books": recommend_books }), 200

@book_bp.route('/all_books/<user_id>', methods=['GET'])
def all_books_user(user_id):
    all_books = Book.get_all_books_from_user(user_id)
    if not len(all_books):
        return jsonify({ "errors":'No hay libros registrados' }), 404

    return jsonify({ "books":all_books }), 200

@book_bp.route('/all_books', methods=['GET'])
def all_books():
    all_books = Book.get_all_books()
    if not len(all_books):
        return jsonify({ "errors": 'No hay libros registrados' }), 404

    return jsonify({ "all_books":all_books }), 200

# Declarado en el global para ocuparlo en otras rutas
FOLDER_PDFS = 'uploads/pdfs'
FOLDER_IMAGES = 'uploads/images'

@book_bp.route('/publish', methods=['POST'])
def publicate_book():
    # Rutas donde se guardaran los archivos
    # Crear las carpetas si no existen
    os.makedirs(FOLDER_PDFS, exist_ok=True)
    os.makedirs(FOLDER_IMAGES, exist_ok=True)

    data_book = request.form
    pdf_file = request.files['pdf']
    image_file = request.files['image']
    if not pdf_file or not image_file:
        return jsonify({ "errors": 'Archivos faltantes' }), 400

    # Guardar los archivos con un nombre seguro en el disco
    pdf_filename = secure_filename(pdf_file.filename)
    image_filename = secure_filename(image_file.filename)

    # Crear rutas completas y guardar los archivos
    pdf_path = f'uploads/pdfs/{pdf_filename}'
    image_path = f"uploads/images/{image_filename}"

    pdf_file.save(pdf_path)
    image_file.save(image_path)

    book_existant = Book.get_book_by_title(data_book['title'])
    if book_existant:
        return jsonify({ "errors":'Este libro ya existe' }), 409

    errors_book = Book.validate_book(data_book)
    if len(errors_book):
        return jsonify({ "errors":errors_book }), 400


    # data_book['genre'] = data_book['genre'].replace(', ', ',')
    book_complete = {
        "title": data_book['title'],
        "author": data_book['author'],
        "genre": data_book['genre'],
        "description": data_book['description'],
        "user_id": int(data_book['user_id']),
        "pdf_path": pdf_path,
        "image_path": image_path,
    }

    new_book_id = Book.insert_book(book_complete)
    if not new_book_id:
        return jsonify({ "errors":'Error en la base de datos' }), 500

    return jsonify({ "book_id":new_book_id }), 201

@book_bp.route('/uploads/images/<filename>')
def get_image(filename):
    return send_from_directory(FOLDER_IMAGES, filename)

@book_bp.route('/uploads/pdfs/<filename>')
def get_pdf(filename):
    return send_from_directory(FOLDER_PDFS, filename)

@book_bp.route('/elim/<id>', methods=['POST'])
def elim_book(id):
    book = Book.get_book_by_id(id)
    if not book:
        return jsonify({ "errors":'Este libro no existe' }), 404

    # Construimos las rutas completas a los archivos pdf e images del proyecto
    pdf_path = os.path.join(current_app.root_path, book[0].pdf_path)
    # current_app.root_path = \Users\lucks\Desktop\LibroScope_Back\
    image_path = os.path.join(current_app.root_path, book[0].image_path)

    print("Ruta PDF:", pdf_path)
    print("Ruta imagen:", image_path)
    print("Existe PDF:", os.path.exists(pdf_path))
    print("Existe imagen:", os.path.exists(image_path))


    # Eliminar los archivos
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    if os.path.exists(image_path):
        os.remove(image_path)

    Book.delete_book(id)

    return jsonify({ "success":'Libro y archivos eliminados' }), 200