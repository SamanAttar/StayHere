from wtforms import Form, StringField, TextAreaField, PasswordField, validators, RadioField

class RegisterForm(Form):
    user_type = RadioField('Label', choices=[('GuestButton','Guest'),('HostButton','Host')])
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message = 'Password Does Not Match')
    ])
    confirm = PasswordField('Confrim Password')
