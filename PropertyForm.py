from wtforms import Form, StringField, TextAreaField, PasswordField, validators, RadioField

class PropertyForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])
    locaton = StringField('Title', [validators.Length(min=1, max=200)])
