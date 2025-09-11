from flask import Flask
from flask_cors import CORS
from app import app 
import os
import cloudinary

def configure_cloudinary():
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        secure=True
    )

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}}, supports_credentials=True) 

    from app.controllers.users import user_bp
    app.register_blueprint(user_bp, url_prefix='/user')

    from app.controllers.books import book_bp
    app.register_blueprint(book_bp, url_prefix='/books')

    from app.controllers.reviews import review_bp
    app.register_blueprint(review_bp, url_prefix='/review')
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
