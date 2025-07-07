from flask import Blueprint, request, jsonify
from elasticsearch import Elasticsearch
from app import app
from app.models.Book import Book
import requests
import random

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

@book_bp.route('/publish', methods=['POST'])
def publicate_book():
    data_book = request.get_json()

    book_existant = Book.get_book_by_title(data_book['title'])
    if book_existant:
        return jsonify({ "errors":'Este libro ya existe' }), 409

    errors_book = Book.validate_book(data_book)
    if len(errors_book):
        return jsonify({ "errors":errors_book }), 400

    # data_book['genre'] = data_book['genre'].replace(', ', ',')

    new_book_id = Book.insert_book(data_book)
    if not new_book_id:
        return jsonify({ "errors":'Error en la base de datos' }), 500

    return jsonify({ "book_id":new_book_id }), 201

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