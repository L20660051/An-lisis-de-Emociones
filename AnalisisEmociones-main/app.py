from flask import Flask, render_template, request, jsonify, session
import pyodbc

app = Flask(__name__)
app.secret_key = "clave_secreta_segura"  # Cambiar en producción

# Configuración de la conexión a la base de datos
DB_CONFIG = {
    'server': '127.0.0.1',
    'database': 'Proyecto',
    'username': 'sa',
    'password': '1234',
    'trusted_connection': 'no',
    'trust_server_certificate': 'yes'
}

def get_db_connection():
    """Establece y devuelve una conexión a la base de datos."""
    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']};"
        f"Trusted_Connection={DB_CONFIG['trusted_connection']};"
        f"TrustServerCertificate={DB_CONFIG['trust_server_certificate']};"
    )
    return pyodbc.connect(connection_string)

@app.route('/')
def home():
    """Página de inicio."""
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """Inicio de sesión."""
    data = request.form
    correo = data.get('correo')
    contrasena = data.get('contrasena')

    if not correo or not contrasena:
        return jsonify({"message": "Correo y contraseña son obligatorios"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT UsuarioID, Rol FROM Usuarios WHERE Correo = ? AND Contrasena = ?",
            (correo, contrasena)
        )
        user = cursor.fetchone()

        if not user:
            return jsonify({"message": "Correo o contraseña incorrectos"}), 401

        usuario_id, rol = user
        session['usuario_id'] = usuario_id

        # Redirigir según el rol
        if rol == 'Alumno':
            return render_template('Analisis.html')
        elif rol == 'Tutor':
            return render_template('Tutor.html')
        elif rol == 'Psicologo':
            return render_template('Psicologo.html')
        elif rol == 'Administrador':
            return render_template('Administrador.html')
        else:
            return jsonify({"message": "Rol desconocido"}), 403

    except Exception as e:
        return jsonify({"message": "Error en el servidor", "error": str(e)}), 500

    finally:
        conn.close()

@app.route('/index', methods=['GET', 'POST'])
def analisis():
    """Página de análisis de ansiedad."""
    if request.method == 'POST':
        alumno_id = session.get('usuario_id')
        if not alumno_id:
            return jsonify({"message": "Usuario no autenticado"}), 403

        # Procesar análisis (Placeholder para integrar lógica)
        puntaje = 75.0
        nivel = "Moderado"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Analisis (AlumnoID, PuntajeAnsiedad, NivelAnsiedad, Observaciones) VALUES (?, ?, ?, ?)",
            (alumno_id, puntaje, nivel, "Análisis generado automáticamente")
        )
        conn.commit()
        conn.close()

        return jsonify({"message": "Análisis registrado exitosamente", "nivel": nivel, "puntaje": puntaje}), 200

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)