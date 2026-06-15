import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

DB_PATH = 'instance/petcare.db'


def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("🗑️ Banco antigo removido")

    os.makedirs('instance', exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE pet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            species TEXT NOT NULL,
            breed TEXT,
            age INTEGER,
            weight REAL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user(id)
        );

        CREATE TABLE appointment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            vet_id INTEGER NOT NULL,
            date DATE NOT NULL,
            time TIME NOT NULL,
            duration INTEGER DEFAULT 30,
            type TEXT DEFAULT 'consulta',
            reason TEXT,
            status TEXT DEFAULT 'agendado',
            medical_record TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pet_id) REFERENCES pet(id),
            FOREIGN KEY (vet_id) REFERENCES user(id)
        );

        CREATE TABLE grooming (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            groomer_id INTEGER NOT NULL,
            date DATE NOT NULL,
            time TIME NOT NULL,
            duration INTEGER DEFAULT 60,
            service_type TEXT DEFAULT 'banho e tosa',
            notes TEXT,
            status TEXT DEFAULT 'agendado',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pet_id) REFERENCES pet(id),
            FOREIGN KEY (groomer_id) REFERENCES user(id)
        );
    ''')

    # Usuários
    users = [
        ('Admin', 'admin@petcare.com', generate_password_hash('admin123'), 'admin'),
        ('Cliente Teste', 'cliente@petcare.com', generate_password_hash('cliente123'), 'tutor'),
        ('Dra. Camila', 'camila.vet@petcare.com', generate_password_hash('veterinario123'), 'veterinario'),
        ('Dr. Roberto', 'roberto.vet@petcare.com', generate_password_hash('veterinario123'), 'veterinario'),
        ('Dra. Ana', 'ana.vet@petcare.com', generate_password_hash('veterinario123'), 'veterinario'),
        ('Bianca', 'bianca@petcare.com', generate_password_hash('funcionario123'), 'banho_tosa'),
        ('Carlos', 'carlos@petcare.com', generate_password_hash('funcionario123'), 'banho_tosa'),
        ('Mariana', 'mariana@petcare.com', generate_password_hash('funcionario123'), 'banho_tosa'),
    ]

    cursor.executemany('INSERT INTO user (name, email, password, role) VALUES (?, ?, ?, ?)', users)

    cursor.execute('SELECT id FROM user WHERE email = "cliente@petcare.com"')
    tutor_id = cursor.fetchone()[0]

    cursor.execute('SELECT id FROM user WHERE role = "veterinario"')
    vet_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute('SELECT id FROM user WHERE role = "banho_tosa"')
    groomer_ids = [row[0] for row in cursor.fetchall()]

    # Pets
    cursor.execute('''
        INSERT INTO pet (name, species, breed, age, weight, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('Rex', 'Cachorro', 'Labrador', 3, 25.5, tutor_id))

    cursor.execute('''
        INSERT INTO pet (name, species, breed, age, weight, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('Luna', 'Cachorro', 'Poodle', 2, 5.5, tutor_id))

    cursor.execute('''
        INSERT INTO pet (name, species, breed, age, weight, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('Mingau', 'Gato', 'SRD', 4, 4.2, tutor_id))

    cursor.execute('SELECT id FROM pet WHERE user_id = ? LIMIT 1', (tutor_id,))
    pet_id = cursor.fetchone()[0]

    # Agendamento passado
    past_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
    cursor.execute('''
        INSERT INTO appointment (pet_id, vet_id, date, time, duration, type, reason, status, medical_record)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (pet_id, vet_ids[0], past_date, '10:00', 30, 'consulta', 'Check-up anual', 'realizado', 'Animal saudável'))

    # Agendamento futuro
    future_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    cursor.execute('''
        INSERT INTO appointment (pet_id, vet_id, date, time, duration, type, reason, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (pet_id, vet_ids[0], future_date, '14:30', 30, 'consulta', 'Tosse persistente', 'agendado'))

    # Banho futuro
    cursor.execute('''
        INSERT INTO grooming (pet_id, groomer_id, date, time, duration, service_type, notes, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (pet_id, groomer_ids[0], future_date, '09:00', 60, 'banho e tosa', 'Pelagem longa', 'agendado'))

    conn.commit()
    conn.close()

    print("✅ Banco de dados criado com sucesso!")
    print("\n📋 Credenciais de teste:")
    print("   Tutor: cliente@petcare.com / cliente123")
    print("   Admin: admin@petcare.com / admin123")
    print(
        "   Veterinários: camila.vet@petcare.com, roberto.vet@petcare.com, ana.vet@petcare.com (senha: veterinario123)")
    print("   Banho/Tosa: bianca@petcare.com, carlos@petcare.com, mariana@petcare.com (senha: funcionario123)")


if __name__ == '__main__':
    init_db()