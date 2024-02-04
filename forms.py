from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField
from functools import wraps
from flask import redirect, url_for, abort
from flask_login import current_user

# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField(label="Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


# TODO: Create a RegisterForm to register new users
class RegisterForm(FlaskForm):
    email = StringField(label="Username", validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    name = StringField(label='Name', validators=[DataRequired()])
    submit = SubmitField(label='Sign me up')


# TODO: Create a LoginForm to login existing users
class LoginForm(FlaskForm):
    email = StringField(label='Email', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    submit = SubmitField(label='Login')


# TODO: Create a CommentForm so users can leave comments below posts
class CommentForm(FlaskForm):
    comment_text = CKEditorField(label='Comment')
    submit = SubmitField("Submit comment")


# Create protect route authoriser
def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        # Check if the user is authenticated
        if not current_user.is_authenticated:
            # Redirect to the login page or another appropriate page
            return redirect(url_for('login'))

        # Check if the user's ID is 1
        if current_user.get_id() != '1':
            # Redirect to a page indicating unauthorized access or another appropriate page
            return abort(401)

        # Call the original view function if the user is authenticated and has the correct ID
        return view_func(*args, **kwargs)

    return wrapper
