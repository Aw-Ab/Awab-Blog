from flask import Flask, render_template, redirect, url_for, flash, request , abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, SignInForm , RegisterForm , CommentForm
from functools import wraps
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['CKEDITOR_PKG_TYPE'] = 'full'
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app=app)

@login_manager.user_loader
def load_user(user_id):
    logged_in = True
    return User.query.get(user_id)

def admin_only(func):
    @wraps(func)
    def decorated_function(*args , **kwargs) :
        if current_user.id != 1 :
            abort(403)
        return func(*args , **kwargs)
    return decorated_function

class User(UserMixin ,db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer , primary_key=True)
    name = db.Column(db.String(250) , nullable=False)
    email = db.Column(db.String(250) , nullable=False , unique =True)
    password = db.Column(db.String(250) , nullable=False)
    posts = relationship('BlogPost' , back_populates='author')
    comments = relationship('Comment' , back_populates='commenter')
    def __repr__(self):
        return f'{self.name}'

##CONFIGURE TABLES
with app.app_context():
    db.create_all()

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer , db.ForeignKey('users.id'))
    author = relationship('User' , back_populates='posts')

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments = relationship('Comment' , back_populates='post')

with app.app_context():
    db.create_all()

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer , primary_key=True)
    post_id = db.Column(db.Integer , db.ForeignKey('blog_posts.id'))
    post = relationship('BlogPost' , back_populates='comments')
    body = db.Column(db.String(500) , nullable=True)
    commenter = relationship('User' ,back_populates='comments')
    commenter_id = db.Column(db.Integer , db.ForeignKey('users.id'))

with app.app_context():
    db.create_all()





@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts , logged_in=current_user.is_authenticated)

@app.route('/register' , methods=['GET' , 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST' :
        user = db.session.query(User).filter_by(email=form.email.data).first()
        if user is None :
            new_user = User(name=form.name.data ,
                        email=form.email.data ,
                        password=generate_password_hash(form.password.data , 'pbkdf2:sha256',8))
            with app.app_context():
                db.session.add(new_user)
                db.session.commit()
            login_user(User.query.filter_by(email=request.form['email']).first())
            return redirect(url_for('get_all_posts'))
        flash("This email is already registered , you can log in .")
        return redirect(url_for('login'))
    return render_template("register.html" , form=form)


@app.route('/login' , methods=['GET' , 'POST'])
def login():
    form = SignInForm()
    if request.method == 'POST' :
        user = User.query.filter_by(email=request.form['email']).first()
        if user is not None :
            if check_password_hash(user.password , form.password.data) :
                login_user(user)
                return redirect(url_for('get_all_posts'))
            flash('Wrong password , Try again .')
            return redirect(url_for('login'))
        flash('This email is not registered , Try a valid one please .')
        return redirect(url_for('login'))
    return render_template("login.html" , form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>" , methods=['GET' , 'POST' ])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    comments = Comment.query.filter_by(post=requested_post).all()
    form = CommentForm()
    if request.method == 'POST' :
        data = form.data
        new_comment = Comment(commenter=current_user , post=requested_post , body=data.get('body'))
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('show_post' , post_id=post_id))

    return render_template("post.html", comments =comments ,post=requested_post , form=form , logged_in=current_user.is_authenticated)


@app.route("/about")
def about():
    return render_template("about.html" , logged_in=current_user.is_authenticated)


@app.route("/contact")
def contact():
    return render_template("contact.html" , logged_in=current_user.is_authenticated)


@app.route("/new-post" , methods=['GET' , 'POST'])
@admin_only
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


@app.route("/edit-post/<int:post_id>")
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
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
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000 , debug=True)
