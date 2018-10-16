from wtforms import Form, StringField, TextAreaField, PasswordField, IntegerField, validators, RadioField

class PropertyForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=100)])
    body = TextAreaField('Body', [validators.Length(min=30, max=100)])
    location = StringField('Location', [validators.Length(min=1, max=50)])
    guests = IntegerField('Max guests', [validators.NumberRange(min=1, max=100)])
