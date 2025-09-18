from app import app, db, User, Doctor, Patient, pbkdf2_sha256

# Importe a classe date do datetime para usar no seed
from datetime import date

def seed_database():
    """Popula o banco de dados com dados iniciais."""
    with app.app_context():
        # Verifica se já existem dados para evitar duplicidade
        if User.query.filter_by(email="user@gmail.com").first():
            print("Dados de seed já existem. Abortando a operação.")
            return

        print("Iniciando a populacao do banco de dados...")

        # 1. Cria um usuário (médico)
        password_hash = pbkdf2_sha256.hash("123456")
        user_doctor = User(
            cpf="111.111.111-11",
            name="Dr. João Silva",
            email="doctor@gmail.com",
            birthDate="01/01/1980",
            gender="M",
            type="doctor",
            password=password_hash,
            status=True
        )
        db.session.add(user_doctor)
        db.session.commit() # Commit para que o user_doctor tenha um ID

        # 2. Cria o perfil de médico associado ao usuário
        doctor_profile = Doctor(
            user_id=user_doctor.id,
            clinic="Clínica Saúde Plena",
            speciality="Ortopedia"
        )
        db.session.add(doctor_profile)
        db.session.commit()

        # 3. Cria um usuário (paciente)
        user_patient = User(
            cpf="222.222.222-22",
            name="Maria Oliveira",
            email="patient@gmail.com",
            birthDate="15/05/1992",
            gender="F",
            type="patient",
            password=password_hash,
            status=True
        )
        db.session.add(user_patient)
        db.session.commit() # Commit para que o user_patient tenha um ID

        # 4. Cria o perfil de paciente associado ao usuário
        patient_profile = Patient(user_id=user_patient.id)
        db.session.add(patient_profile)
        db.session.commit()

        print("Banco de dados populado com sucesso!")
        print(f"Médico criado com ID: {doctor_profile.id}")
        print(f"Paciente criado com ID: {patient_profile.id}")


if __name__ == '__main__':
    seed_database()