from flask import Flask, render_template, flash, request, redirect, url_for, send_file

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime
from datetime import date

from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user


from webforms import LoginForm, PostForm, UserForm, PasswordForm, NamerForm, SearchForm
from flask_ckeditor import CKEditor
from werkzeug.utils import secure_filename
import uuid as uuid
import os
from sqlalchemy.sql import exists


# Create a Flask Instance
app = Flask (__name__)
# Add CKEditor
ckeditor = CKEditor(app)

# Secret Key!
app.config['SECRET_KEY'] = "moonlight"

# Add Database

# OLD SQLite db
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# NEW MySQL DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/our_users'

# Initialize the Database

UPLOAD_FOLDER = 'static/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ATTACHMENT_FOLDER = 'static/attachments/'
app.config['ATTACHMENT_FOLDER'] = ATTACHMENT_FOLDER

db =  SQLAlchemy(app)
migrate = Migrate(app, db)

# Flask_Login Stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Pass Stuff to Navbar
@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)

# Create Admin Page
@app.route('/admin')
@login_required
def admin():
    id = current_user.id
    our_users = Users.query.order_by(Users.date_added)
    if id == 19:
        return render_template("admin.html", our_users=our_users)
    else:
        flash("You must be the Admin to access this page!")
        return redirect(url_for('dashboard'))


# Create Search Function
@app.route('/search', methods=['POST'])
def search():
    form = SearchForm()
    posts = Posts.query
    if form.validate_on_submit():
        # Get data from submitted form
        post.searched = form.searched.data
        # Query the database
        posts = posts.filter(Posts.content.like('%' + post.searched + '%'))
        posts = posts.order_by(Posts.title).all()
        
        
        return render_template("search.html", form=form, searched=post.searched, posts=posts)
    
    else:
    
        post.searched = " "
        return render_template("search.html", form=form, searched=post.searched, posts=posts)
    

# Create Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            # Check the Hash
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Logged in Successfully!")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid Password. Please Try Again. ")
        else:
            flash("Account Doesn't Exist! Please Try again.")
    return render_template('login.html', form=form)

# Create Logout Function
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# Create Dashboard Page
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    posts = Posts.query.order_by(Posts.date_posted)
    return render_template('dashboard.html', posts=posts)

# Create Profile Page
@app.route('/profile/<int:id>', methods=['GET', 'POST'])
@login_required
def profile(id):
    id = Users.query.get_or_404(id)
    posts = Posts.query.order_by(Posts.date_posted)
    
    return render_template('profile.html', posts=posts, id=id)


@app.route('/posts/delete/<int:id>')
@login_required
def delete_post(id):
    post_to_delete = Posts.query.get_or_404(id)
    id = current_user.id
    
    if id ==post_to_delete.poster.id or id == 19:
        try:
            db.session.delete(post_to_delete)
            db.session.commit()
            
            # Return a Message
            flash("Material was Deleted!")
            
            # Grab all posts from the database
            posts = Posts.query.order_by(Posts.date_posted)
            return render_template("posts.html", posts=posts)
            
        except:
            flash("Whoops! There was a problem deleting post. Try Again!")
    else:
        # Return a Message
        flash("You are Not Authorized to Delete That Post!")
            
        # Grab all posts from the database
        posts = Posts.query.order_by(Posts.date_posted)
        return render_template("posts.html", posts=posts)
    

@app.route('/posts')
def posts():
    # Grab all posts from the database
    posts = Posts.query.order_by(Posts.date_posted)
    return render_template("posts.html", posts=posts)

@app.route('/posts/<int:id>')
@login_required
def post(id):
    exist = db.session.query(exists().where(Posts.poster_id == current_user.id)).scalar()
    post = Posts.query.get_or_404(id)
    return render_template('post.html', post=post, exist=exist)

@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Posts.query.get_or_404(id)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.author = form.author.data
        post.doc_type = form.doc_type.data
        post.content = form.content.data
        post.file_attachment = form.file_attachment.data
        upload = request.files['file_attachment']
        if upload:  
            # Grab Attachment Name
            af_filename = secure_filename(upload.filename)
            # Set UUID
            attachment_name = str(uuid.uuid1()) + "_" + af_filename
            # Save that Attachment
            post.file_attachment.save(os.path.join(app.config['ATTACHMENT_FOLDER'], attachment_name))
            # Change it to a String to save to db
            post.file_attachment=attachment_name
    
        try:
            # Update Database
            db.session.add(post)
            db.session.commit()
    
            flash("Post Has Been Updated")
            return redirect(url_for('post', id=post.id))
        except:
            flash("Something went wrong")
            return redirect(url_for('post', id=post.id))
    
    if current_user.id == post.poster_id or current_user.id == 19:
        form.title.data = post.title
        form.author.data = post.author
        form.doc_type.data = post.doc_type
        form.content.data = post.content
        return render_template('edit_post.html', form=form)
    
    else:
        flash("You are Not Authorized to Edit This Post")
        posts = Posts.query.order_by(Posts.date_posted)
        return render_template("posts.html", posts=posts)

# Add Post Page
@app.route('/add-post', methods=['GET', 'POST'])
def add_post():
    form = PostForm()
    
    if form.validate_on_submit():
        poster = current_user.id
        upload = request.files['file_attachment']
        attachment_name=None
        if upload:
            # Grab Attachment Name
            af_filename = secure_filename(upload.filename)
            # Set UUID
            attachment_name = str(uuid.uuid1()) + "_" + af_filename
            # Save that Attachment
            form.file_attachment.data.save(os.path.join(app.config['ATTACHMENT_FOLDER'], attachment_name))
        
        # Change it to a String to save to db
        post = Posts(title=form.title.data, content=form.content.data, author=form.author.data, poster_id=poster, doc_type=form.doc_type.data, file_attachment=attachment_name)
        
        
        
        # Clear the Form
        form.title.data = ''
        form.content.data = ''
        form.author.data = ''
        form.doc_type.data = ''
        form.file_attachment.data = ''
        
        # Add Post Data to Database
        db.session.add(post)
        db.session.commit()
        # Return a Message
        flash("Post Submitted Successfully!")
        
    # Redirect to the webpage
    return render_template("post.html", form=form)
    

# Json Thing
@app.route('/date')
def get_current_date():
    favorite_pizza = {"John": "Pepperoni", "Mary": "Cheese", "Tim": "Mushroom"}
    #return favorite_pizza
    return {"Date": datetime.today()}

@app.route('/download/<file>')
def download(file):
    attachment = Posts.query.filter_by(file_attachment=file).first()
    path = "./static/attachments/"
    finalpath = path + str(attachment.file_attachment)
    return send_file(finalpath, as_attachment=True)


# Delete User Reccord
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    if id == current_user.id or current_user.id == 19:
        user_to_delete = Users.query.get_or_404(id)
        name = None
        form = UserForm()

        try:
            db.session.delete(user_to_delete)
            db.session.commit()
            if id == current_user.id:
                flash("Account Deleted Successfully!")
                return render_template("add_user.html", form=form, name=name)
            if current_user.id == 19:
                our_users = Users.query.order_by(Users.date_added)
                return render_template("admin.html", form=form, name=name, our_users=our_users)
        except:
            flash("Whoops! There was a problem deleting this account, try again...")
            return render_template("add_user.html", form=form, name=name, our_users=our_users)
        
    else: 
        flash("You are not authorized to delete that account!")
        return redirect(url_for('dashboard'))
    
    


# Update Database Record
@app.route('/update/<int:id>', methods = ['GET', 'POST'])
@login_required
def update(id):
    form = UserForm()
    name_to_update = Users.query.get_or_404(id)
    posts = Posts.query.order_by(Posts.date_posted)
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.program = request.form['program']
        name_to_update.bio = request.form['bio']
        name_to_update.username = request.form['username']
        
        
        # Check for profile pic
        if request.files['profile_pic']:
            name_to_update.profile_pic = request.files['profile_pic']
        
            # Grab Image Name
            pic_filename = secure_filename(name_to_update.profile_pic.filename)
            # UUID
            pic_name = str(uuid.uuid1()) + "_" + pic_filename
            # Save the image
            saver = request.files['profile_pic']
            
            
            # Change it to a string to save to db
            name_to_update.profile_pic = pic_name
            
            try:
                db.session.commit()
                saver.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
                flash("Profile Updated Successfully!")
                return render_template("dashboard.html", form=form, name_to_update=name_to_update, id=id, posts=posts)
            except:
                flash("Error! Looks like there was a problem... Try Again.")
                return render_template("update.html", form=form, name_to_update=name_to_update, id=id)
            
        else:
            db.session.commit()
            flash("Profile Updated Successfully!")
            return render_template("dashboard.html", form=form, name_to_update=name_to_update, id=id, posts=posts)
    else:
        return render_template("update.html", form=form, name_to_update=name_to_update, id=id)


#def index():
#    return "<h1>Hello World!</h1>"

# FILTERS!!
#safe
#capitalize
#upper
#lower
#title
#trim
#striptags

# Create a Route Decorator
@app.route('/')
def index():
    first_name = "John"
    return render_template("index.html",first_name=first_name)

# localhost:5000/user/john
@app.route('/user/<name>')
def user(name):
    return render_template("user.html", user_name=name)



# Create Custom Error Pages

# Invalid URL
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# Internal Server Error
@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500

# Create Name Page
@app.route('/name', methods = ['GET', 'POST'])
def name():
    name = None
    form = NamerForm()
    # Validate Form
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
        flash("Form Submitted Successfully!")
    return render_template("name.html", name = name, form = form)

# Create Password Test Page
@app.route('/test_pw', methods = ['GET', 'POST'])
def test_pw():
    email = None
    password = None
    pw_to_check = None
    passed = None
    form = PasswordForm()
    # Validate Form
    if form.validate_on_submit():
        email = form.email.data
        password = form.password_hash.data
        form.email.data = ''
        form.password_hash.data = ''
        
        # Lookup User by email address
        pw_to_check = Users.query.filter_by(email=email).first()
        
        # Check Hashed Password
        passed = check_password_hash(pw_to_check.password_hash, password)
        
    return render_template("test_pw.html", email = email, password = password, pw_to_check= pw_to_check, passed=passed, form = form)

@app.route('/user/add', methods = ['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    if form.validate_on_submit():
        uemail = Users.query.filter_by(email=form.email.data).first()
        uname = Users.query.filter_by(username=form.username.data).first()
        if uemail is None and uname is None:
            # Hash the Password!
            hashed_pw = generate_password_hash(form.password_hash.data, "sha256")
            user =  Users(name=form.name.data, username=form.username.data, email=form.email.data, program=form.program.data, password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()
        
            name = form.name.data
            form.name.data = ''
            form.username.data = ''
            form.email.data = ''
            form.program.data = ''
            form.password_hash.data = ''
            flash("Registration Complete!")
            return redirect(url_for('login'))
        else:
            flash("Email or Username already exist! Please Try Again.")
            form.email.data = ''
    our_users = Users.query.order_by(Users.date_added)
    return render_template("add_user.html", form=form, name=name, our_users=our_users)


# Create a Archive Post Model
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column((db.Text))
    author = db.Column((db.String(255)))
    date_posted = db.Column(db.DateTime, default= datetime.now)
    doc_type = db.Column(db.String(255))
    file_attachment = db.Column(db.String(500), nullable=True)
    # Foreign Key to Link Users (refer to primary key of the user)
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    


#Create Model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    program = db.Column(db.String(120))
    bio = db.Column(db.Text(500), nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.now)
    profile_pic = db.Column(db.String(500), nullable=True)
    # Do some password stuff!
    password_hash = db.Column(db.String((128)))
    # User can have many posts
    posts = db.relationship('Posts', backref='poster')
    
    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute!')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Create a String
    def __repr__(self):
        return '<Name %r>' % self.name