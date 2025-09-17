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
    type = db.Column(db.String(45), nullable=False)  # "patient" ou "doctor"
    password = db.Column(db.String(256), nullable=False)
    status = db.Column(db.Boolean, default=True)

    patient = db.relationship("Patient", uselist=False, back_populates="user")
    doctor = db.relationship("Doctor", uselist=False, back_populates="user")

    def check_password(self, password):
        return pbkdf2_sha256.verify(password, self.password)


class Patient(db.Model):
    __tablename__ = 'patient'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    user = db.relationship("User", back_populates="patient")
    sessions = db.relationship("Session", back_populates="patient")


class Doctor(db.Model):
    __tablename__ = 'doctor'
    id = db.Column(db.Integer, primary_key=True)
    clinic = db.Column(db.String(45), nullable=False)
    speciality = db.Column(db.String(45), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    user = db.relationship("User", back_populates="doctor")
    sessions = db.relationship("Session", back_populates="doctor")


class Session(db.Model):
    __tablename__ = 'session'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    vital_signs_avg = db.Column(db.JSON, nullable=True)

    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)

    doctor = db.relationship("Doctor", back_populates="sessions")
    patient = db.relationship("Patient", back_populates="sessions")
    movements = db.relationship("Movement", back_populates="session")


class Movement(db.Model):
    __tablename__ = 'movement'
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.JSON, nullable=False)

    session_id = db.Column(db.Integer, db.ForeignKey("session.id"), nullable=False)

    session = db.relationship("Session", back_populates="movements")

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

@app.route('/sessions', methods=['POST'])
@jwt_required()
def create_session_and_receive_data():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"msg": "No data provided"}), 400

    doctor_id = data.get("doctor_id")
    patient_id = data.get("patient_id")
    movements_data = data.get("movements")
    vital_signs_avg = data.get("vital_signs_avg")

    if not doctor_id or not patient_id or not movements_data:
        return jsonify({"msg": "doctor_id, patient_id and movements are required"}), 400

    doctor = Doctor.query.get(doctor_id)
    patient = Patient.query.get(patient_id)
    if not doctor or not patient:
        return jsonify({"msg": "Doctor or patient not found"}), 404

    if doctor.user_id != current_user_id and patient.user_id != current_user_id:
        return jsonify({"msg": "Forbidden: You cannot create a session for others"}), 403

    session = Session(
        date=datetime.date.today(),
        doctor_id=doctor_id,
        patient_id=patient_id,
        vital_signs_avg=vital_signs_avg
    )
    db.session.add(session)
    db.session.commit()

    movement = Movement(session_id=session.id, data=movements_data)
    db.session.add(movement)
    db.session.commit()

    try:
        payload = {
            "session_id": session.id,
            "date": str(session.date),
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "vital_signs_avg": vital_signs_avg,
            "movements": movements_data
        }
        print(f"Enviando para a nuvem: {payload}")
        # Para envio real, use:
        # cloud_url = "https://example-cloud.com/api/sessions"
        # response = requests.post(cloud_url, json=payload)
        # print("Cloud response:", response.status_code, response.text)
    except Exception as e:
        print(f"Erro ao enviar para a nuvem: {e}")

    return jsonify({
        "msg": "Session created, movement saved and sent to cloud",
        "session_id": session.id,
        "movement_id": movement.id
    }), 201
    
if __name__ == '__main__':
    app.run(debug=True)