from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo
from datetime import timedelta
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
csrf = CSRFProtect(app)
# Set session to be permanent and define its lifetime (30 days)
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

login_manager = LoginManager()
login_manager.init_app(app)

# Function to connect to the database
def connect_db():
    return sqlite3.connect('database.db')

# Define the User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email

class EditarClienteForm(FlaskForm):
    telefono = StringField('Teléfono', validators=[DataRequired()])
    direccion = StringField('Dirección', validators=[DataRequired()])
    submit = SubmitField('Guardar Cambios')

# Load a user from the database given its ID
@login_manager.user_loader
def load_user(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email FROM users WHERE id = ?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return User(user_data[0], user_data[1])
    else:
        return None

# Function to check if the user is authenticated
def esta_autenticado():
    return current_user.is_authenticated

# Route for the login form
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email=?', (email,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user[4], password):  
            user_obj = User(user[0], user[2])
            login_user(user_obj)  # Log in the user
            return redirect(url_for('home'))
        else:
            if user:
                error = 'Contraseña incorrecta'
            else:
                error = 'Usuario no encontrado'
            flash(error, 'error')  # Flash error message
    
    return render_template('login.html', error=error)

# Route for logging out
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('', 'success')
    return redirect(url_for('login'))  # Redirect to the login page

# Function to check authentication before each request
@app.before_request
def verificar_autenticacion():
    if not esta_autenticado() and request.endpoint not in ['login', 'signup']:
        return redirect(url_for('login'))

# Route for the home page (requires authentication)
@app.route('/')
@login_required
def home():
    user_id = current_user.id
    
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT nombre, apellido FROM users WHERE id=?', (user_id,))
    user_data = cursor.fetchone()
    
    if user_data:
        nombre, apellido = user_data
        return render_template('home.html', nombre=nombre, apellido=apellido)
    else:
        flash('Usuario no encontrado en la base de datos', 'error')
        return redirect(url_for('login'))

# Function to send HTTP cache headers
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# Define the SignUpForm using Flask-WTF
class SignUpForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    apellido = StringField('Apellido', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')

# Route for the signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        nombre = form.nombre.data
        apellido = form.apellido.data
        email = form.email.data
        password = form.password.data
        
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email=?', (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            flash('El usuario ya existe. Por favor, elige otro correo electrónico.', 'error')
            return redirect(url_for('signup'))

        password_hash = generate_password_hash(password)  

        cursor.execute('INSERT INTO users (nombre, apellido, email, password) VALUES (?, ?, ?, ?)', (nombre, apellido, email, password_hash))
        conn.commit()
        conn.close()
        
        flash('Registro exitoso. Por favor, inicia sesión.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html', form=form) 


@app.route('/editar_cliente.html')
def editarcliente():
    return redirect(url_for('/clientes/editar_cliente.html'))

@app.route('/cliente.html')
def cliente():
    return render_template('/clientes/cliente.html')

@app.route('/servicios')
def servicios():
    return render_template('servicios.html')

# Area de clientes

@app.route('/clientes')
def mostrar_clientes():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Clientes')
    clientes = cursor.fetchall()

    conn.close()

    return render_template('/clientes/buscarcliente.html', clientes=clientes)

# Route for the add client page
@app.route('/agregar_cliente', methods=['GET', 'POST'])
@login_required
def agregar_cliente():
    form = ClientForm()
    if form.validate_on_submit():
        nombre = form.nombre.data
        telefono = form.telefono.data
        direccion = form.direccion.data
        
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute('INSERT INTO Clientes (Nombre, Telefono, Direccion) VALUES (?, ?, ?)', (nombre, telefono, direccion))
        conn.commit()
        conn.close()
        
        flash('Cliente agregado correctamente.', 'success')
        return redirect(url_for('mostrar_clientes'))
    
    return render_template('/clientes/agregar_cliente', form=form)

# Define the ClientForm using Flask-WTF
class ClientForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    telefono = StringField('Teléfono', validators=[DataRequired()])
    direccion = StringField('Dirección')
    submit = SubmitField('Agregar Cliente')


# Ruta para mostrar el formulario de agregar cliente
@app.route('/agregar_cliente_form')
def agregar_cliente_form():
    form = ClientForm()  # Aquí se crea una instancia del formulario
    return render_template('/clientes/agregar_cliente.html', form=form)  # Se pasa el formulario al renderizar el template


@app.route('/editar_cliente_form', methods=['GET'])
def editar_cliente_form():
    cliente_id = request.args.get('cliente_id')
    
    # Verificar si se proporcionó un ID de cliente
    if cliente_id:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Buscar el cliente por ID o nombre
        cursor.execute('SELECT * FROM Clientes WHERE ID_Cliente = ? OR Nombre LIKE ?', (cliente_id, f'%{cliente_id}%'))
        cliente = cursor.fetchone()
        conn.close()
        
        # Verificar si se encontró un cliente
        if cliente:
            # Aquí se crea una instancia del formulario
            form = EditarClienteForm()
            return render_template('/clientes/editar_cliente.html', cliente_id=cliente[0], nombre=cliente[1], telefono=cliente[2], direccion=cliente[3], form=form)
        else:
            return "Cliente no encontrado"
    else:
        return "ID de cliente no proporcionado"

from flask import request

@app.route('/editar_cliente', methods=['POST'])
def editar_cliente():
    cliente_id = request.form.get('cliente_id')
    telefono = request.form.get('telefono')
    direccion = request.form.get('direccion')

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE Clientes SET Telefono=?, Direccion=? WHERE ID_Cliente=?', (telefono, direccion, cliente_id))
    conn.commit()
    conn.close()

    # Después de actualizar el cliente, redirige a una página apropiada, como la lista de clientes
    return redirect(url_for('cliente'))

@app.route('/buscarclienteeditar')
def buscarclienteeditar():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Clientes')
    clientes = cursor.fetchall()

    conn.close()

    return render_template('/clientes/buscarclienteeditar.html', clientes=clientes)

@app.route('/eliminar_cliente_form', methods=['GET', 'POST'])
def eliminar_cliente_form():
    form = ClientForm()  # Crea una instancia del formulario
    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM Clientes WHERE ID_Cliente = ?', (cliente_id,))
        conn.commit()
        conn.close()

        return redirect(url_for('mostrar_clientes'))  # Redirige a la página de clientes después de eliminar el cliente
    
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM Clientes')
    clientes = cursor.fetchall()

    conn.close()

    return render_template('/clientes/eliminar_cliente_form.html', form=form, clientes=clientes)


class VentasForm(FlaskForm):
    cliente = StringField('Cliente', validators=[DataRequired()])
    producto = StringField('Producto', validators=[DataRequired()])
    correo = StringField('Correo', validators=[DataRequired()])
    contrasena = StringField('Contraseña', validators=[DataRequired()])
    perfil = StringField('Perfil', validators=[DataRequired()])
    pin_perfil = StringField('PIN del Perfil', validators=[DataRequired()])
    fecha_venta = StringField('Fecha de Venta', validators=[DataRequired()])
    fecha_vencimiento = StringField('Fecha de Vencimiento', validators=[DataRequired()])
    submit = SubmitField('Guardar')


@app.route('/venta')
def ventas_form():
    # Conectar a la base de datos
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Obtener clientes y productos de la base de datos
        cursor.execute("SELECT ID_Cliente, Nombre FROM Clientes")
        clientes = cursor.fetchall()

        cursor.execute("SELECT ID_Producto, Nombre FROM Productos")
        productos = cursor.fetchall()

        # Crear una instancia del formulario
        form = VentasForm()

        # Pasar el formulario como contexto al renderizar la plantilla
        return render_template('/ventas/ventas_form.html', form=form, clientes=clientes, productos=productos)
    except sqlite3.Error as e:
        print("Error:", e)
    finally:
        conn.close()

# Ruta para manejar la solicitud de obtener las opciones del correo y la contraseña
@app.route('/fetch_credentials')
def fetch_credentials():
    producto_id = request.args.get('producto_id')

    # Conectar a la base de datos y ejecutar la consulta para obtener las opciones del correo y la contraseña
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('SELECT ID_Credencial, Correo, Contraseña FROM Credenciales WHERE Producto_ID = ?', (producto_id,))
    credentials = cursor.fetchall()

    conn.close()

    # Devolver las opciones del correo y la contraseña en formato JSON
    return jsonify({
        'credentials': credentials
    })

@app.route('/registro_venta', methods=['POST'])
def registro_venta():
    if request.method == 'POST':
        cliente = request.form.get('cliente')
        producto = request.form.get('producto')
        correo = request.form.get('correo')
        contrasena = request.form.get('contrasena')
        perfil = request.form.get('perfil')
        pin_perfil = request.form.get('pin_perfil')
        fecha_venta = request.form.get('fecha_venta')
        fecha_vencimiento = request.form.get('fecha_vencimiento')

        # Verifica si algún campo está vacío
        if not all([cliente, producto, correo, contrasena, perfil, pin_perfil, fecha_venta, fecha_vencimiento]):
            flash('Todos los campos son requeridos.', 'error')
            return redirect(url_for('ventas_form'))  # Redirige a la página de ventas

        # Conectar a la base de datos y realizar las inserciones
        conn = connect_db()
        cursor = conn.cursor()

        try:
            # Insertar la venta en la tabla Ventas
            cursor.execute('''INSERT INTO Ventas (ID_Cliente, ID_Producto, ID_Perfil, Fecha_Venta, Fecha_Vencimiento)
                              VALUES (?, ?, ?, ?, ?)''',
                              (cliente, producto, perfil, fecha_venta, fecha_vencimiento))
            
            # Insertar el perfil y pin en la tabla Perfiles
            cursor.execute('''INSERT INTO Perfiles (ID_Producto, Perfil, Pin, Vendido)
                              VALUES (?, ?, ?, ?)''',
                              (producto, perfil, pin_perfil, 1))  # 1 indica que está vendido

            # Confirmar los cambios en la base de datos
            conn.commit()

            flash('Venta registrada correctamente.', 'success')
        except Exception as e:
            flash(f'Error al registrar la venta: {e}', 'error')
            conn.rollback()
        finally:
            conn.close()

        return redirect(url_for('ventas_form'))  # Redirige a la página de ventas

    return redirect(url_for('ventas_form'))  # Redirige a la página de ventas si no es un método POST

################################################

@app.route('/mostrar_credenciales')
def mostrar_credenciales():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Credenciales")
    credenciales = cursor.fetchall()

    conn.close()

    form = TuFormulario()  # Aquí inicializas el formulario si es necesario
    
    return render_template('credenciales.html', form=form, credenciales=credenciales)

@app.route('/agregar_credencial', methods=['POST'])
def agregar_credencial():
    if request.method == 'POST':
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        producto_id = request.form['producto_id']

        # Verifica si algún campo está vacío
        if not correo or not contrasena or not producto_id:
            flash('Todos los campos son requeridos.', 'error')
        else:
            conn = connect_db()
            cursor = conn.cursor()

            # Inserta la nueva credencial en la base de datos
            cursor.execute("INSERT INTO Credenciales (Correo, Contraseña, Producto_ID) VALUES (?, ?, ?)",
                           (correo, contrasena, producto_id))
            conn.commit()
            conn.close()

    # Obtén las credenciales de la base de datos
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Credenciales")
    credenciales = cursor.fetchall()
    conn.close()

    form = TuFormulario()  # Inicializa el formulario
    return render_template('credenciales.html', form=form, credenciales=credenciales)


class TuFormulario(FlaskForm):
    correo = StringField('Correo', validators=[DataRequired()])
    contrasena = StringField('Contraseña', validators=[DataRequired()])
    producto_id = StringField('Producto ID', validators=[DataRequired()])
    submit = SubmitField('Agregar Credencial')

    # Agrega los campos para la edición
    credencial_id = StringField('ID de la Credencial a Editar', validators=[DataRequired()])
    nuevo_correo = StringField('Nuevo Correo', validators=[DataRequired()])
    nueva_contrasena = StringField('Nueva Contraseña', validators=[DataRequired()])
    nuevo_producto_id = StringField('Nuevo Producto ID', validators=[DataRequired()])



@app.route('/editar_credencial', methods=['POST'])
def editar_credencial():
    if request.method == 'POST':
        credencial_id = request.form['credencial_id']
        nuevo_correo = request.form['nuevo_correo']
        nueva_contrasena = request.form['nueva_contrasena']
        nuevo_producto_id = request.form['nuevo_producto_id']

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("UPDATE Credenciales SET Correo=?, Contraseña=?, Producto_ID=? WHERE ID_Credencial=?",
                       (nuevo_correo, nueva_contrasena, nuevo_producto_id, credencial_id))
        conn.commit()
        conn.close()

    return redirect(url_for('mostrar_credenciales'))

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")