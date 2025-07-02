from flask import Blueprint, request, jsonify
from app import app
from app.models.Review import Review

review_bp = Blueprint('review_bp', __name__)

@review_bp.route('/from_user', methods=['GET'])
def reviews_from_user():
    all_reviews = Review.get_reviews_from_user()

    if not len(all_reviews):
        return jsonify({ "errors":'No hay reviews registradas' }), 404

    return jsonify({ "reviews":all_reviews }), 200

@review_bp.route('/all_reviews', methods=['GET'])
def all_reviews():
    all_reviews = Review.get_all_reviews()

    if not len(all_reviews):
        return jsonify({ "errors":'No hay reviews registradas' }), 404

    return jsonify({ "reviews":all_reviews }), 200

@review_bp.route('/publish', methods=['POST'])
def publicate_review():
    data_review = request.get_json()

    errors_review = Review.validate_review(data_review)
    if len(errors_review):
        return jsonify({ "errors":errors_review }), 400

    new_review_id = Review.insert_review(data_review)
    if not new_review_id:
        return jsonify({ "errors":'Error en la base de datos' }), 500

    return jsonify({ "review_id":new_review_id }), 201

@review_bp.route('/elim/<id>', methods=['POST'])
def elim_review(id):
    elim_review = Review.delete_review(id)
    if not elim_review:
        return jsonify({ "errors":'Esta review no existe' }), 404

    return jsonify({ "message":'Review eliminada' }), 200