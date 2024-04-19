from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class EditarCredencialForm(FlaskForm):
    credencial_id = StringField('ID de la Credencial a Editar', validators=[DataRequired()])
    nuevo_correo = StringField('Nuevo Correo', validators=[DataRequired()])
    nueva_contrasena = StringField('Nueva Contraseña', validators=[DataRequired()])
    nuevo_producto_id = StringField('Nuevo Producto ID', validators=[DataRequired()])
    submit = SubmitField('Editar Credencial')