from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import cv2
import mediapipe as mp
from fer import FER
import numpy as np
import pyodbc
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_para_sesiones'

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configuración de la base de datos
DB_SERVER = '127.0.0.1'
DB_USER = 'sa'
DB_PASSWORD = '1234'
DB_NAME = 'Proyecto'

# Conexión a la base de datos
def connect_to_database():
    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
    )
    return pyodbc.connect(connection_string)

# Rutas para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')  # Muestra el formulario de login

    elif request.method == 'POST':
        correo = request.form['correo']
        contrasena = request.form['contrasena']

        try:
            conn = connect_to_database()
            cursor = conn.cursor()

            # Verifica si el usuario existe en la base de datos
            query = "SELECT UsuarioID, Rol FROM Usuarios WHERE Correo = ? AND Contrasena = ?"
            cursor.execute(query, (correo, contrasena))
            user = cursor.fetchone()

            if user:
                # Inicia la sesión del usuario
                session['usuario_id'] = user[0]
                session['rol'] = user[1]

                # Redirige según el rol
                if user[1] == 'Alumno':
                    return redirect(url_for('indexAlumno'))  # Redirige al análisis para Alumno
                elif user[1] == 'Administrador':
                    return redirect(url_for('indexAdmin'))  # Redirige al análisis para Administrador
                elif user[1] == 'Psicologo':
                    return redirect(url_for('indexPsicologo')) 

                else:
                    return jsonify({'message': 'Rol no reconocido'}), 403
            else:
                return jsonify({'message': 'Credenciales incorrectas'}), 401
        except Exception as e:
            print(f"Error al iniciar sesión: {e}")
            return jsonify({'message': 'Error del servidor'}), 500
        finally:
            conn.close()


@app.route('/logout')
def logout():
    session.clear()  
    return redirect(url_for('login'))

# Decorador para verificar si el usuario está autenticado
def login_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper

# Ruta protegida por login
# Función auxiliar para obtener el nombre completo del alumno
def obtener_nombre_alumno(alumno_id):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        query = """
        SELECT CONCAT(Nombre, ' ', ApellidoPaterno, ' ', ApellidoMaterno) AS NombreCompleto
        FROM Alumno
        WHERE AlumnoID = ?
        """
        cursor.execute(query, (alumno_id,))
        datos = cursor.fetchone()
        return datos[0] if datos else None
    except Exception as e:
        print(f"Error al obtener el nombre del alumno: {e}")
        return None
    finally:
        conn.close()

# Función auxiliar para obtener el último análisis del alumno
def obtener_ultimo_analisis(alumno_id):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        query = """
        SELECT TOP(1) FechaAnalisis, NivelAnsiedad
        FROM Analisis
        WHERE AlumnoID = ?
        ORDER BY FechaAnalisis DESC
        """
        cursor.execute(query, (alumno_id,))
        datos = cursor.fetchone()
        if datos:
            fecha = datos[0].strftime('%d/%m/%Y') if isinstance(datos[0], datetime) else None
            nivel = datos[1]
            return fecha, nivel
        return None, None
    except Exception as e:
        print(f"Error al obtener el último análisis: {e}")
        return None, None
    finally:
        conn.close()

# Función auxiliar para obtener el historial de análisis
def obtener_historial_analisis(alumno_id):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        query = """
        SELECT FechaAnalisis, NivelAnsiedad, PuntajeAnsiedad
        FROM Analisis
        WHERE AlumnoID = ?
        ORDER BY FechaAnalisis DESC
        """
        cursor.execute(query, (alumno_id,))
        registros = cursor.fetchall()
        historial = [
            {
                'fecha': r[0].strftime('%d/%m/%Y'),
                'hora': r[0].strftime('%H:%M'),
                'nivel': r[1],
                'puntaje': r[2]
            }
            for r in registros
        ]
        return historial
    except Exception as e:
        print(f"Error al obtener el historial: {e}")
        return []
    finally:
        conn.close()

# Ruta principal
@app.route('/')
@login_required
def indexAlumno():
    alumno_id = session.get('usuario_id')
    nombreAlumno = obtener_nombre_alumno(alumno_id)
    fechaAnalisis, puntaje_ansiedad = obtener_ultimo_analisis(alumno_id)
    return render_template(
        'Alumno/index.html',
        nombreAlumno=nombreAlumno,
        fechaAnalisis=fechaAnalisis,
        puntaje_ansiedad=puntaje_ansiedad
    )





@app.route('/recursosAlumno')
@login_required
def recursosAlumno():
    alumno_id = session.get('usuario_id')
    nombreAlumno = obtener_nombre_alumno(alumno_id)
    return render_template('Alumno/recursos.html', nombreAlumno=nombreAlumno)


@app.route('/configuracionAlumno')
@login_required
def configuracionAlumno():
    alumno_id = session.get('usuario_id')
    nombreAlumno = obtener_nombre_alumno(alumno_id)
    return render_template('Alumno/configuracion.html', nombreAlumno=nombreAlumno)

@app.route('/encuestasAlumno')
@login_required
def encuestasAlumno():
    alumno_id = session.get('usuario_id')
    nombreAlumno = obtener_nombre_alumno(alumno_id)
    return render_template('Alumno/encuestas.html', nombreAlumno=nombreAlumno)

@app.route('/historialAlumno')
@login_required
def historialAlumno():
    alumno_id = session.get('usuario_id')
    nombreAlumno = obtener_nombre_alumno(alumno_id)
    historial = obtener_historial_analisis(alumno_id)
    return render_template('Alumno/historial.html', historial=historial, nombreAlumno = nombreAlumno)

@app.route('/analisis')
@login_required
def analisis():
    return render_template('Alumno/Analisis.html')


# Otras rutas reutilizando la lógica
@app.route('/mensajesAlumno')
@login_required
def mensajesAlumno():
    alumno_id = session.get('usuario_id')
    nombreAlumno = obtener_nombre_alumno(alumno_id)

    # Conexión única a la base de datos
    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        # Obtener los mensajes para el alumno
        query_mensaje = """
        SELECT * FROM Mensajes
        WHERE Destinatario = ?
        ORDER BY Fecha DESC
        """
        cursor.execute(query_mensaje, (alumno_id,))
        mensajes = cursor.fetchall()  # Obtener todos los mensajes

        # Obtener los alumnos
        query_psicologo = """
        SELECT CONCAT(Nombre, ' ', ApellidoPaterno, ' ', ApellidoMaterno) AS NombreCompleto, PsicologoID
        FROM Psicologo
        """
        cursor.execute(query_psicologo)
        psicologo = cursor.fetchall()

    except Exception as e:
        print(f"Error al obtener los datos: {e}")
        mensajes = []  # En caso de error, devolver una lista vacía
    finally:
        # Cerrar la conexión a la base de datos
        cursor.close()
        conn.close()

    return render_template('Alumno/mensajes.html', nombreAlumno=nombreAlumno, mensajes=mensajes, psicologo = psicologo)



@app.route('/marcar_leido', methods=['POST'])
@login_required
def marcar_leido():
    mensaje_id = request.json.get('idmensaje')
    if not mensaje_id:
        return jsonify({'error': 'Falta el ID del mensaje'}), 400

    # Conexión a la base de datos
    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        # Actualizar el campo 'Leido' a 1
        query_update = """
        UPDATE Mensajes
        SET Leido = 1
        WHERE IDMensaje = ?
        """
        cursor.execute(query_update, (mensaje_id,))
        conn.commit()

    except Exception as e:
        print(f"Error al marcar el mensaje como leído: {e}")
        return jsonify({'error': 'No se pudo marcar el mensaje como leído'}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({'success': True})






@app.route('/indexAdmin')
@login_required
def indexAdmin():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))  # Redirige al login si no está autenticado

    admin_id = session['usuario_id']  # Obtiene el AdminID de la sesión

    try:
        # Conexión única a la base de datos
        conn = connect_to_database()
        cursor = conn.cursor()

        # Obtener el nombre del administrador
        query_admin = """
        SELECT CONCAT(Nombre, ' ', ApellidoPaterno, ' ', ApellidoMaterno) AS NombreAdmin 
        FROM Administrador
        WHERE AdminID = ?
        """
        cursor.execute(query_admin, (admin_id,))
        datosAdmin = cursor.fetchone()  # Usar fetchone ya que solo esperamos un resultado
        nombreAdmin = datosAdmin[0] if datosAdmin else "Admin desconocido"

        # Obtener estadísticas en una sola transacción
        query_stats = """
        SELECT 
            (SELECT count(*) FROM Alumno) AS totalAlumnos,
            (SELECT count(*) FROM Analisis WHERE NivelAnsiedad LIKE '%Leve%') AS totalLeve,
            (SELECT count(*) FROM Analisis WHERE NivelAnsiedad LIKE '%Moderado%') AS totalModerado,
            (SELECT count(*) FROM Analisis WHERE NivelAnsiedad LIKE '%Severo%') AS totalSevero,
            (SELECT count(*) FROM Analisis WHERE NivelAnsiedad NOT LIKE '%No se pudo analizar%') AS TotalCasos,
            (SELECT count(*) FROM Analisis WHERE NivelAnsiedad LIKE '%Normal%') AS totalNormal
        """
        cursor.execute(query_stats)
        stats = cursor.fetchone()  # Solo esperamos una fila de resultados

        # Asignar valores con manejo seguro de datos
        totalAlumnos = stats[0] if stats else 0
        totalLeve = stats[1] if stats else 0
        totalModerado = stats[2] if stats else 0
        totalSevero = stats[3] if stats else 0
        totalCasos = stats[4] if stats else 0
        totalNormal = stats[5] if stats else 0

    except Exception as e:
        print(f"Error al obtener los datos: {e}")
        return render_template('error.html')  # Página de error en caso de excepción
    finally:
        # Cerrar la conexión a la base de datos
        cursor.close()
        conn.close()

    return render_template(
        'Admin/index.html', 
        nombreAdmin=nombreAdmin, 
        totalAlumnos=totalAlumnos, 
        totalLeve=int(totalLeve) if totalLeve is not None else 0,
        totalModerado=int(totalModerado) if totalModerado is not None else 0,
        totalSevero=int(totalSevero) if totalSevero is not None else 0,
        totalCasos=int(totalCasos) if totalCasos is not None else 0,
        totalNormal=int(totalNormal) if totalNormal is not None else 0
    )

@app.route('/gestionUsuariosAdmin')
@login_required
def gestionUsuariosAdmin():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))  # Redirige al login si no está autenticado

    admin_id = session['usuario_id']  # Obtiene el AdminID de la sesión

    try:
        # Conexión a la base de datos
        conn = connect_to_database()
        cursor = conn.cursor()

        # Obtener el nombre del administrador
        query_admin = """
        SELECT CONCAT(Nombre, ' ', ApellidoPaterno, ' ', ApellidoMaterno) AS NombreAdmin 
        FROM Administrador
        WHERE AdminID = ?
        """
        cursor.execute(query_admin, (admin_id,))
        datosAdmin = cursor.fetchone()  # Usar fetchone ya que solo esperamos un resultado
        nombreAdmin = datosAdmin[0] if datosAdmin else "Admin desconocido"

        # Consultas para obtener los usuarios organizados por roles
        query_usuarios_admin = """
        SELECT Correo, Rol, CONCAT(Nombre, ' ', ApellidoPaterno, ' ', ApellidoMaterno) AS NombreCompleto
        FROM Usuarios
        JOIN Administrador ON Usuarios.UsuarioID = Administrador.AdminID
        """
        cursor.execute(query_usuarios_admin)
        usuarios_admin = cursor.fetchall()

        query_usuarios_alumno = """
        SELECT Correo, Rol, CONCAT(Nombre, ' ', ApellidoPaterno, ' ', ApellidoMaterno) AS NombreCompleto
        FROM Usuarios
        JOIN Alumno ON Usuarios.UsuarioID = Alumno.AlumnoID
        """
        cursor.execute(query_usuarios_alumno)
        usuarios_alumno = cursor.fetchall()

        query_usuarios_docente = """
        SELECT Correo, Rol, CONCAT(Nombre, ' ', ApellidoPaterno, ' ', ApellidoMaterno) AS NombreCompleto
        FROM Usuarios
        JOIN Docente ON Usuarios.UsuarioID = Docente.DocenteID
        """
        cursor.execute(query_usuarios_docente)
        usuarios_docente = cursor.fetchall()

        query_usuarios_psicologo = """
        SELECT Correo, Rol, CONCAT(Nombre, ' ', ApellidoPaterno, ' ', ApellidoMaterno) AS NombreCompleto
        FROM Usuarios
        JOIN Psicologo ON Usuarios.UsuarioID = Psicologo.PsicologoID
        """
        cursor.execute(query_usuarios_psicologo)
        usuarios_psicologo = cursor.fetchall()

        query_usuarios_tutor = """
        SELECT Correo, Rol, CONCAT(Nombre, ' ', ApellidoPaterno, ' ', ApellidoMaterno) AS NombreCompleto
        FROM Usuarios
        JOIN Tutor ON Usuarios.UsuarioID = Tutor.TutorID
        """
        cursor.execute(query_usuarios_tutor)
        usuarios_tutor = cursor.fetchall()

    except Exception as e:
        print(f"Error al obtener los datos: {e}")
        return render_template('error.html')  # Página de error en caso de excepción
    finally:
        # Cerrar la conexión a la base de datos
        cursor.close()
        conn.close()

    # Renderizar la plantilla con los datos de los usuarios
    return render_template(
        'Admin/gestion_usuarios.html',
        nombreAdmin=nombreAdmin,
        usuarios_admin=usuarios_admin,
        usuarios_alumno=usuarios_alumno,
        usuarios_docente=usuarios_docente,
        usuarios_psicologo=usuarios_psicologo,
        usuarios_tutor=usuarios_tutor
    )

@app.route('/reportesAdmin')
@login_required
def reportesAdmin():
    return render_template('Admin/reportes.html')




@app.route('/casosAtendidosAdmin')
@login_required
def casosAtendidosAdmin():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))  # Redirige al login si no está autenticado

    admin_id = session['usuario_id']  # Obtiene el AdminID de la sesión

    try:
        # Conexión única a la base de datos
        conn = connect_to_database()
        cursor = conn.cursor()

        # Obtener el nombre del administrador
        query_admin = """
        SELECT CONCAT(Nombre, ' ', ApellidoPaterno, ' ', ApellidoMaterno) AS NombreAdmin 
        FROM Administrador
        WHERE AdminID = ?
        """
        cursor.execute(query_admin, (admin_id,))
        datosAdmin = cursor.fetchone()  # Usar fetchone ya que solo esperamos un resultado
        nombreAdmin = datosAdmin[0] if datosAdmin else "Admin desconocido"

        # Obtener estadísticas en una sola transacción
        query_stats = """
        SELECT 
            (SELECT count(*) FROM Alumno) AS totalAlumnos,
            (SELECT count(*) FROM Analisis WHERE NivelAnsiedad LIKE '%Leve%') AS totalLeve,
            (SELECT count(*) FROM Analisis WHERE NivelAnsiedad LIKE '%Moderado%') AS totalModerado,
            (SELECT count(*) FROM Analisis WHERE NivelAnsiedad LIKE '%Severo%') AS totalSevero,
            (SELECT count(*) FROM Analisis) AS TotalCasos,
            (SELECT count(*) FROM Analisis WHERE NivelAnsiedad LIKE '%Normal%') AS totalNormal
        """
        cursor.execute(query_stats)
        stats = cursor.fetchone()  # Solo esperamos una fila de resultados

        # Asignar valores con manejo seguro de datos
        totalAlumnos = stats[0] if stats else 0
        totalLeve = stats[1] if stats else 0
        totalModerado = stats[2] if stats else 0
        totalSevero = stats[3] if stats else 0
        totalCasos = stats[4] if stats else 0
        totalNormal = stats[5] if stats else 0

    except Exception as e:
        print(f"Error al obtener los datos: {e}")
        return render_template('error.html')  # Página de error en caso de excepción
    finally:
        # Cerrar la conexión a la base de datos
        cursor.close()
        conn.close()

    return render_template(
        'Admin/casos_atendidos.html', 
        nombreAdmin=nombreAdmin, 
        totalAlumnos=totalAlumnos, 
        totalLeve=int(totalLeve) if totalLeve is not None else 0,
        totalModerado=int(totalModerado) if totalModerado is not None else 0,
        totalSevero=int(totalSevero) if totalSevero is not None else 0,
        totalCasos=int(totalCasos) if totalCasos is not None else 0,
        totalNormal=int(totalNormal) if totalNormal is not None else 0
    )







######################################################################################################################################
# Psicologo
######################################################################################################################################
@app.route('/indexPsicologo')
@login_required
def indexPsicologo():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))  # Redirige al login si no está autenticado

    psicologo_id = session['usuario_id']  # Obtiene el AdminID de la sesión

    try:
        # Conexión única a la base de datos
        conn = connect_to_database()
        cursor = conn.cursor()

        # Obtener el nombre del administrador
        query_psicologo = """
        SELECT CONCAT(Nombre, ' ', ApellidoPaterno, ' ', ApellidoMaterno) AS NombreAdmin 
        FROM Psicologo
        WHERE PsicologoID = ?
        """
        cursor.execute(query_psicologo, (psicologo_id,))
        datosPsicologo = cursor.fetchone()  # Usar fetchone ya que solo esperamos un resultado
        nombrePsicologo = datosPsicologo[0] if datosPsicologo else "Psicologo desconocido"

        query_alumnos = """
        SELECT CONCAT(Nombre, ' ', ApellidoPaterno, ' ', ApellidoMaterno) AS NombreCompleto
        FROM Alumno
        """
        cursor.execute(query_alumnos)
        usuarios_alumno = cursor.fetchall()

    except Exception as e:
        print(f"Error al obtener los datos: {e}")
        return render_template('error.html')  # Página de error en caso de excepción
    finally:
        # Cerrar la conexión a la base de datos
        cursor.close()
        conn.close()

    return render_template(
        'Psicologo/index.html', 
        nombrePsicologo=nombrePsicologo,
        usuarios_alumno = usuarios_alumno
    )


@app.route('/alumnosPsicologo')
@login_required
def alumnosPsicologo():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))  # Redirige al login si no está autenticado

    psicologo_id = session['usuario_id']  # Obtiene el AdminID de la sesión

    try:
        # Conexión única a la base de datos
        conn = connect_to_database()
        cursor = conn.cursor()

        # Obtener el nombre del administrador
        query_psicologo = """
        SELECT CONCAT(Nombre, ' ', ApellidoPaterno, ' ', ApellidoMaterno) AS NombreAdmin 
        FROM Psicologo
        WHERE PsicologoID = ?
        """
        cursor.execute(query_psicologo, (psicologo_id,))
        datosPsicologo = cursor.fetchone()  # Usar fetchone ya que solo esperamos un resultado
        nombrePsicologo = datosPsicologo[0] if datosPsicologo else "Psicologo desconocido"

        query_alumnos = """
        SELECT CONCAT(Alumno.Nombre, ' ', Alumno.ApellidoPaterno, ' ', Alumno.ApellidoMaterno) AS NombreCompleto, Telefono, Matricula, Correo 
        FROM Alumno JOIN Usuarios ON AlumnoID = UsuarioID
        """
        cursor.execute(query_alumnos)
        usuarios_alumno = cursor.fetchall()

    except Exception as e:
        print(f"Error al obtener los datos: {e}")
        return render_template('error.html')  # Página de error en caso de excepción
    finally:
        # Cerrar la conexión a la base de datos
        cursor.close()
        conn.close()

    return render_template(
        'Psicologo/alumnos.html', 
        nombrePsicologo=nombrePsicologo,
        usuarios_alumno = usuarios_alumno
    )


@app.route('/configuracionPsicologo')
@login_required
def configuracionPsicologo():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))  # Redirige al login si no está autenticado

    psicologo_id = session['usuario_id']  # Obtiene el AdminID de la sesión

    try:
        # Conexión única a la base de datos
        conn = connect_to_database()
        cursor = conn.cursor()

        # Obtener el nombre del administrador
        query_psicologo = """
        SELECT CONCAT(Nombre, ' ', ApellidoPaterno, ' ', ApellidoMaterno) AS NombreAdmin 
        FROM Psicologo
        WHERE PsicologoID = ?
        """
        cursor.execute(query_psicologo, (psicologo_id,))
        datosPsicologo = cursor.fetchone()  # Usar fetchone ya que solo esperamos un resultado
        nombrePsicologo = datosPsicologo[0] if datosPsicologo else "Psicologo desconocido"

        query_datos = """
        SELECT CONCAT(Nombre, ' ', ApellidoPaterno, ' ', ApellidoMaterno) AS NombreCompleto, Telefono, Correo 
        FROM Psicologo JOIN Usuarios ON PsicologoID = UsuarioID
        """
        cursor.execute(query_datos)
        datosPsicologo = cursor.fetchall()

    except Exception as e:
        print(f"Error al obtener los datos: {e}")
        return render_template('error.html')  # Página de error en caso de excepción
    finally:
        # Cerrar la conexión a la base de datos
        cursor.close()
        conn.close()

    return render_template(
        'Psicologo/configuracion.html', 
        nombrePsicologo=nombrePsicologo,
        datosPsicologo = datosPsicologo
    )





@app.route('/informacionPsicologo')
@login_required
def informacionPsicologo():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))  # Redirige al login si no está autenticado

    psicologo_id = session['usuario_id']  # Obtiene el AdminID de la sesión

    try:
        # Conexión única a la base de datos
        conn = connect_to_database()
        cursor = conn.cursor()

        # Obtener el nombre del administrador
        query_psicologo = """
        SELECT CONCAT(Nombre, ' ', ApellidoPaterno, ' ', ApellidoMaterno) AS NombreAdmin 
        FROM Psicologo
        WHERE PsicologoID = ?
        """
        cursor.execute(query_psicologo, (psicologo_id,))
        datosPsicologo = cursor.fetchone()  # Usar fetchone ya que solo esperamos un resultado
        nombrePsicologo = datosPsicologo[0] if datosPsicologo else "Psicologo desconocido"

        query_alumnos = """
        SELECT CONCAT(Nombre, ' ', ApellidoPaterno, ' ', ApellidoMaterno) AS NombreCompleto
        FROM Alumno
        """
        cursor.execute(query_alumnos)
        usuarios_alumno = cursor.fetchall()

        query_detecciones = """
        SELECT TOP(1) CONCAT(Alumno.Nombre, ' ', Alumno.ApellidoPaterno, ' ', Alumno.ApellidoMaterno) AS NombreCompleto, NivelAnsiedad
        FROM Alumno
        JOIN Analisis ON Alumno.AlumnoID = Analisis.AlumnoID
        WHERE (NivelAnsiedad LIKE '%Leve%' OR NivelAnsiedad LIKE '%Moderado%' OR NivelAnsiedad LIKE '%Severo%')
        GROUP BY Alumno.AlumnoID, Alumno.Nombre, Alumno.ApellidoPaterno, Alumno.ApellidoMaterno, Analisis.NivelAnsiedad
        """
        cursor.execute(query_detecciones)
        usuarios_detectados = cursor.fetchall()

    except Exception as e:
        print(f"Error al obtener los datos: {e}")
        return render_template('error.html')  # Página de error en caso de excepción
    finally:
        # Cerrar la conexión a la base de datos
        cursor.close()
        conn.close()

    return render_template(
        'Psicologo/informacion.html', 
        nombrePsicologo=nombrePsicologo,
        usuarios_alumno = usuarios_alumno,
        usuarios_detectados = usuarios_detectados
    )



@app.route('/mensajesPsicologo')
@login_required
def mensajesPsicologo():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))  # Redirige al login si no está autenticado

    psicologo_id = session['usuario_id']  # Obtiene el PsicologoID de la sesión

    try:
        # Conexión única a la base de datos
        conn = connect_to_database()
        cursor = conn.cursor()

        # Obtener el nombre del psicólogo
        query_psicologo = """
        SELECT CONCAT(Nombre, ' ', ApellidoPaterno, ' ', ApellidoMaterno) AS NombrePsicologo 
        FROM Psicologo
        WHERE PsicologoID = ?
        """
        cursor.execute(query_psicologo, (psicologo_id,))
        datosPsicologo = cursor.fetchone()
        nombrePsicologo = datosPsicologo[0] if datosPsicologo else "Psicólogo desconocido"

        # Obtener los alumnos
        query_alumnos = """
        SELECT CONCAT(Nombre, ' ', ApellidoPaterno, ' ', ApellidoMaterno) AS NombreCompleto, AlumnoID
        FROM Alumno
        """
        cursor.execute(query_alumnos)
        alumnos = cursor.fetchall()

        # Obtener los mensajes dirigidos al psicólogo
        query_mensaje = """
        SELECT IDMensaje, Fecha, Asunto, Mensaje, CONCAT(Nombre, ' ', ApellidoPaterno, ' ', ApellidoMaterno) AS NombreAlumno FROM Mensajes INNER JOIN Alumno ON Mensajes.UsuarioID = Alumno.AlumnoID
        WHERE Destinatario = ?
        ORDER BY Fecha DESC
        """
        cursor.execute(query_mensaje, (psicologo_id,))
        mensajes = cursor.fetchall()

    except Exception as e:
        print(f"Error al obtener los datos: {e}")
        mensajes = []  # En caso de error, devolver una lista vacía
        alumnos = []   # En caso de error, devolver una lista vacía
        nombrePsicologo = "Psicólogo desconocido"

    finally:
        # Cerrar la conexión a la base de datos
        cursor.close()
        conn.close()

    return render_template(
        'Psicologo/mensajes.html', 
        nombrePsicologo=nombrePsicologo,
        alumnos=alumnos,
        mensajes=mensajes
    )

######################################################################################################################################
# Psicologo
######################################################################################################################################











@app.route('/enviarMensaje', methods=['POST'])
@login_required
def enviar_mensaje():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Usuario no autenticado'}), 401
    
    psicologo_id = session['usuario_id']  # Obtiene el psicologo_id de la sesión
    destinatario_id = request.json.get('destinatario')  # Obtiene el destinatario (AlumnoID)
    mensaje = request.json.get('mensaje')  # Obtiene el mensaje
    asunto = request.json.get('asunto')

    if not destinatario_id or not mensaje:
        return jsonify({'success': False, 'message': 'Faltan datos'}), 400

    # Obtener la fecha y hora actuales
    fecha_actual = datetime.now().strftime('%Y-%m-%d')  # Formato YYYY-MM-DD
    hora_actual = datetime.now().strftime('%H:%M:%S')  # Formato HH:MM:SS

    try:
        # Conexión a la base de datos
        conn = connect_to_database()
        cursor = conn.cursor()

        # Insertar mensaje en la tabla Mensajes
        query_insert = """
        INSERT INTO Mensajes (UsuarioID, Destinatario, Fecha, Hora, Asunto, Mensaje, Leido)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query_insert, (psicologo_id, destinatario_id, fecha_actual, hora_actual, asunto, mensaje, 0))

        # Confirmar los cambios
        conn.commit()

        return jsonify({'success': True, 'message': 'Mensaje enviado con éxito'}), 200

    except Exception as e:
        # Imprimir el error para depuración
        print(f"Error al insertar mensaje: {e}")
        return jsonify({'success': False, 'message': f'Error al enviar el mensaje: {str(e)}'}), 500

    finally:
        # Cerrar la conexión a la base de datos
        cursor.close()
        conn.close()






@app.route('/upload_video', methods=['POST'])
@login_required
def upload_video():
    global video_counter
    video_filename = f'recorded_video{video_counter}.mp4'
    video_path = os.path.join(UPLOAD_FOLDER, video_filename)
    video = request.files['video']
    video.save(video_path)

    print(f"Video guardado en {video_path}")

    average_anxiety_score, anxiety_level = analyze_emotions_sequence(video_path)

    # Guardar resultado en la base de datos usando el usuario autenticado
    save_analysis_to_db(
        alumno_id=session['usuario_id'],  # Obtiene el ID del usuario autenticado
        puntaje_ansiedad=average_anxiety_score * 100,
        nivel_ansiedad=anxiety_level,
        observaciones="Sin observaciones"
    )

    video_counter += 1

    return jsonify({
        "message": "Video recibido y analizado",
        "anxiety_score": average_anxiety_score * 100,
        "anxiety_level": anxiety_level
    })

# Función para guardar análisis en la base de datos
def save_analysis_to_db(alumno_id, puntaje_ansiedad, nivel_ansiedad, observaciones):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        fecha_analisis = datetime.now()

        query = """
            INSERT INTO Analisis (AlumnoID, FechaAnalisis, PuntajeAnsiedad, NivelAnsiedad, Observaciones)
            VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(query, (alumno_id, fecha_analisis, puntaje_ansiedad, nivel_ansiedad, observaciones))
        conn.commit()
        print("Análisis guardado exitosamente en la base de datos.")
    except Exception as e:
        print(f"Error al guardar en la base de datos: {e}")
    finally:
        conn.close()

# Funciones del análisis
detector = FER(mtcnn=True)
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)
mp_holistic = mp.solutions.holistic
holistic = mp_holistic.Holistic(static_image_mode=False, model_complexity=1)

video_counter = 1

def detect_microexpressions(landmarks, brow_threshold, jaw_threshold):
    brow_dist = np.linalg.norm(
        np.array([landmarks[52].x, landmarks[52].y]) - 
        np.array([landmarks[282].x, landmarks[282].y])
    )
    jaw_tension = np.linalg.norm(
        np.array([landmarks[61].x, landmarks[61].y]) - 
        np.array([landmarks[291].x, landmarks[291].y])
    )
    return brow_dist < brow_threshold or jaw_tension < jaw_threshold

def detect_anxiety(emotions, microexpression_detected, gesture_detected):
    anxiety_emotions = {'fear': 0.8, 'sad': 0.8, 'angry': 0.8, 'surprise': 0.4}
    anxiety_score = sum(emotions.get(e, 0) * weight for e, weight in anxiety_emotions.items())
    if microexpression_detected or gesture_detected:
        anxiety_score += 0.2
    return anxiety_score > 0.5, anxiety_score

def determine_hamilton_anxiety_level(anxiety_score):
    if anxiety_score < 0.3:
        return "Normal"
    elif 0.3 <= anxiety_score < 0.6:
        return "Leve"
    elif 0.6 <= anxiety_score < 0.8:
        return "Moderado"
    else:
        return "Severo"

def analyze_emotions_sequence(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: No se pudo abrir el video {video_path}")
        return 0, "No se pudo analizar"

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps

    # frame_skip = max(1, int(fps * 0.5))

    print(f"FPS: {fps}, Duración: {duration:.2f}s, Frames totales: {total_frames}")

    frame_anxiety_scores = []

    while cap.isOpened():
        frame_pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        ret, frame = cap.read()
        if not ret:
            break

        # if frame_pos % frame_skip != 0:
        #     continue

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                microexpression_detected = detect_microexpressions(face_landmarks.landmark, 0.03, 0.05)
                emotions_in_frame = detector.detect_emotions(frame)

                if emotions_in_frame:
                    emotions = emotions_in_frame[0]["emotions"]
                    gesture_detected = detect_gestures(frame)
                    _, anxiety_score = detect_anxiety(emotions, microexpression_detected, gesture_detected)
                    frame_anxiety_scores.append(anxiety_score)

    cap.release()
    cv2.destroyAllWindows()

    if not frame_anxiety_scores:
        return 0, "No se pudo analizar"

    average_anxiety_score = np.mean(frame_anxiety_scores)
    anxiety_level = determine_hamilton_anxiety_level(average_anxiety_score)

    print(f"Puntaje promedio de ansiedad: {average_anxiety_score * 100:.2f}%")
    print(f"Nivel de ansiedad: {anxiety_level}")
    return average_anxiety_score, anxiety_level

def detect_gestures(frame):
    return False  # Implementar en el futuro

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
