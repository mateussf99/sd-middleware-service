from datetime import datetime
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
from passlib.hash import pbkdf2_sha256

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['JWT_SECRET_KEY'] = 'uma-chave-secreta-forte'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    cpf = db.Column(db.String(45), nullable=False, unique=True)
    name = db.Column(db.String(45), nullable=False)
    email = db.Column(db.String(45), nullable=False, unique=True)
    birthDate = db.Column(db.String(45), nullable=False)
    gender = db.Column(db.String(1), nullable=False)
    type = db.Column(db.String(45), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    status = db.Column(db.Boolean, default=True)

    def check_password(self, password):
        return pbkdf2_sha256.verify(password, self.password)

@app.route('/')
def index():
    return 'Hello World!'

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"msg": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if user is None or not user.check_password(password):
        return jsonify({"msg": "Bad email or password"}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token)

@app.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_data(user_id):
    current_user_id = get_jwt_identity()

    if current_user_id != user_id:
        return jsonify({"msg": "Forbidden: You can only access your own data"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "cpf": user.cpf,
        "birthDate": user.birthDate,
        "gender": user.gender,
        "type": user.type,
        "status": user.status
    }), 200
    
if __name__ == '__main__':
    app.run(debug=True)