from flask import Blueprint, request, jsonify, send_from_directory
from elasticsearch import Elasticsearch
from app import app
from app.models.Book import Book
from werkzeug.utils import secure_filename
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import OneHotEncoder
import requests
import random
import os
import pandas as pd

book_bp = Blueprint('book_bp', __name__)

#ElasticSearch config
es = Elasticsearch('http://localhost:9200')
client_info = es.info()
print('CONNECTED TO ELASTICSEARCH')
print(client_info.body)

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

@book_bp.route('/search/<query>/<categorie>', methods=['POST'])
def search_books(query, categorie):
    if categorie == 'none':
        response = requests.get('https://www.googleapis.com/books/v1/volumes?q=fiction&maxResults=40&key=AIzaSyDNQ631Qv6pa6tyXCeU1xds2mnYL1KYNg8')
        if response.status_code == 200:
            google_books = response.json()
            for i, book in enumerate(google_books['items']):
                es.index(index=my_index, id=i+1, body=book)
    elif len(categorie) and categorie != 'none':
        response = requests.get(f'https://www.googleapis.com/books/v1/volumes?q=subject:{categorie}&maxResults=40&key=AIzaSyDNQ631Qv6pa6tyXCeU1xds2mnYL1KYNg8')
        if response.status_code == 200:
            google_books = response.json()
            for i, book in enumerate(google_books['items']):
                es.index(index=my_index, id=i+1, body=book)
    else:
        print(f'Error: {google_books.status_code}')
    if query:
        res = es.search(
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
        return jsonify({ "matching_books": [hit['_source'] for hit in res['hits']['hits']] }), 200
    else:
        return jsonify({ "errors":'La query no se obtuvo o no existe' }), 400

@book_bp.route('/all_books/<user_id>', methods=['GET'])
def all_books(user_id):
    all_books = Book.get_all_books(user_id)
    if not len(all_books):
        return jsonify({ "errors":'No hay libros registrados' }), 404

    return jsonify({ "books":all_books }), 200

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
        "user_id": int(data_book['user_id']),
        "favorite": 1 if data_book['favorite'].lower() == 'true' else 0,
        "pdf_path": pdf_path,
        "image_path": image_path
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

@book_bp.route('/favorite/<id>', methods=['GET', 'POST'])
def favorite(id):
    Book.favorite(id)

    book_favorite = Book.get_book_by_id(id)
    if book_favorite[0].favorite != 1:
        return jsonify({ "errors":'Error al volver libro favorito' }), 500
        
    return jsonify({ "message":'Libro favorito' }), 200

@book_bp.route('/not_favorite/<id>', methods=['GET', 'POST'])
def not_favorite(id):
    Book.not_favorite(id)

    book_not_favorite = Book.get_book_by_id(id)
    if book_not_favorite[0].favorite != 0:
        return jsonify({ "errors":'Error al quitar libro favorito' }), 500
        
    return jsonify({ "message":'Libro no favorito' }), 200

@book_bp.route('/favorites', methods=['GET'])
def favorites():
    favorite_books = Book.get_favorite_books()
    if not len(favorite_books):
        return jsonify({ "errors":'No hay libros favoritos' }), 404

    return jsonify({ "favorite_books":favorite_books }), 200

@book_bp.route('/elim/<id>', methods=['POST'])
def elim_book(id):
    elim_book = Book.delete_book(id)
    if not elim_book:
        return jsonify({ "errors":'Este libro no existe' }), 404

    return jsonify({ "message":'Libro eliminado' }), 200 