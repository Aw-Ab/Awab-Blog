from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL,Email,length , Email
from flask_ckeditor import CKEditorField

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class RegisterForm(FlaskForm):
    name = StringField('Name :' , validators=[DataRequired()])
    email = StringField('Email :' , validators=[DataRequired() , Email()])
    password = PasswordField('Password : ' , validators=[DataRequired() , length(min=8 , message='Your Password must contain at least 8 characters ')])
    submit = SubmitField('Register')

class SignInForm(FlaskForm):
    email = StringField('Email :', validators=[DataRequired(), Email()])
    password = PasswordField('Password : ', validators=[DataRequired(), length(min=8,
                                                                             message='Your Password must contain at least 8 characters ')])
    submit = SubmitField('Sign In')

class CommentForm(FlaskForm):
    body = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Sumit comment")