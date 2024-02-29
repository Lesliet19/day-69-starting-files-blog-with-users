from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey, Column
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
# Import your forms from the forms.py
from forms import CreatePostForm, RegisterForm, LoginForm, admin_required, CommentForm
#create environmental varaibles
import os


app = Flask(__name__)

# Access environment variable in Flask app config
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY', 'default_secret_key')

ckeditor = CKEditor(app)
Bootstrap5(app)

# TODO: Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

#User_loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# CREATE DATABASE
class Base(DeclarativeBase):
    pass
# environmental variable


app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQL_KEY')

db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLES
# TODO: Create a User table for all your registered users.
class User(db.Model, UserMixin, Base):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    name = db.Column(db.String)

    # This will act like a List of BlogPost objects attached to each User.
    # The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")

class BlogPost(db.Model,Base):
    __tablename__ = "blog_posts"
    id = db.Column(Integer, primary_key=True)

    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id = db.Column(Integer, db.ForeignKey("users.id"))
    # Create reference to the User object. The "posts" refers to the posts property in the User class.
    author = relationship("User", back_populates="posts")

    title = db.Column(String(250), unique=True, nullable=False)
    subtitle = db.Column(String(250), nullable=False)
    date = db.Column(String(250), nullable=False)
    body = db.Column(Text, nullable=False)
    #author: Mapped[str] = mapped_column(String(250), nullable=False), previous author
    img_url = db.Column(String(250), nullable=False)
    comments = relationship('Comment', back_populates='parent_post')

class Comment(db.Model, Base):
    __tablename__ = 'comments'

    id = db.Column(Integer, primary_key=True)
    text = db.Column(Text, nullable=False)
    author_id = Column(Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates='comments')

    # child relationship #
    post_id = Column(Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")


with app.app_context():
    db.create_all()


# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=["POST", "GET"])
def register():
    users = User.query.all()
    form = RegisterForm()
    login_form = LoginForm()
    if form.validate_on_submit():
        password = form.data['password']
        new_user = User(
            email=form.data["email"],
            password=generate_password_hash(password=password, method='pbkdf2:sha256', salt_length=10),
            name=form.data['name'],
        )
        user = User.query.filter_by(email=new_user.email).first()
        if user in users:
            flash('User already exists please log in.')
            return redirect(url_for('login'))
        else:
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form)


# TODO: Retrieve a user from the database based on their email. 
@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    users = User.query.all()
    if form.validate_on_submit():
        error = None
        email_entered = form.data['email']
        password_entered = form.data['password']
        # finding User with same name as user_entered
        user = User.query.filter_by(email=email_entered).first()

        # Check if user exists
        if user in users:
            # Check stored hash_pass with pass entered
            if check_password_hash(user.password, password_entered):
                login_user(user)
                flash('You were successfully logged in')
                return redirect(url_for('get_all_posts'))
            else:
                error = 'Wrong password, Please try again'
                return render_template('login.html', error=error, form=form)

        else:
            error = 'User does not exist please register'
            return render_template('login.html', error=error, form=form)

    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    flash('You have successfully logged out!')
    return redirect(url_for('login'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts, user=current_user)


# TODO: Allow logged-in users to comment on posts

@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    form = CommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))
        user_comment = Comment(text=form.comment_text.data,
                                   author_id=current_user.id,
                                   post_id=requested_post.id
                                   )
        db.session.add(user_comment)
        db.session.commit()

        return render_template("post.html", post=requested_post, form=form)
    return render_template("post.html", post=requested_post, form=form)



# TODO: Use a decorator so only an admin user can create a new post
@app.route("/new-post", methods=["GET", "POST"])
@admin_required
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


# TODO: Use a decorator so only an admin user can edit a post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_required
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)


# TODO: Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>")
@admin_required
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(port=5002)
