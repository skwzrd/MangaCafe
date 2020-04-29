from flask import Flask, render_template, redirect, flash, session, request, url_for
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
import os
import functools

app = Flask(__name__)

app.secret_key = os.urandom(16)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '' # your mysql password
app.config['MYSQL_DB'] = 'manga_cafe'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/article')
def article():
    cur = mysql.connection.cursor()
    rows = cur.execute('select * from articles')
    articles =  cur.fetchall()
    cur.close()
    if rows > 0:
        return render_template('article.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('article.html', msg=msg)


@app.route('/article/<string:id>')
def article_display(id):
    cur = mysql.connection.cursor()
    rows = cur.execute('select * from articles where id=%s', [id])
    article =  cur.fetchone()
    cur.close()
    if rows > 0:
        return render_template('article_display.html', article=article)
    else:
        msg = 'No Articles Found'
        return render_template('article_display.html', msg=msg)


class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=32)])
    email = StringField('Email', [validators.Length(min=6, max=128)])
    username = StringField('Username', [validators.Length(min=4, max=32)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('password_confirmation', message='Passwords do not match.'),
        validators.Length(min=4, max=32)
    ])
    password_confirmation = PasswordField('Confirm Password')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = str(sha256_crypt.encrypt(form.password.data))

        cur = mysql.connection.cursor()
        string = 'insert into users(name, email, username, password) values(%s, %s, %s, %s)'
        cur.execute(string, [name, email, username, password])
        mysql.connection.commit()
        cur.close()

        flash('You\'re now registered! Please log in.', 'success')
        return redirect(url_for('login'))
    else:
        return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        cur = mysql.connection.cursor()
        result = cur.execute("select * from users where username=%s", [username])

        if result > 0:
            data = cur.fetchone()
            cur.close()
            password = data['password']
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
        cur.close()
    return render_template('login.html')


def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('home'))


class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=3, max=32)])
    body = TextAreaField('Body', [validators.Length(min=8, max=256)])


@app.route('/add_article', methods=['GET', 'POST'])
@login_required
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        print('1:'+str(form.body.data))
        title = form.title.data
        body = form.body.data

        cur = mysql.connection.cursor()
        cur.execute('insert into articles(title, body, author) values(%s, %s, %s)',\
                                                    [title, body, session['username']])
        mysql.connection.commit()
        cur.close()

        flash("Article Published.", 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@login_required
def edit_article(id):
    cur = mysql.connection.cursor()
    cur.execute("select * from articles where id=%s", [id])
    article = cur.fetchone()
    cur.close()

    form = ArticleForm(request.form)

    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        cur = mysql.connection.cursor()
        cur.execute("update articles set title=%s, body=%s where id=%s",(title, body, id))
        mysql.connection.commit()
        cur.close()

        flash('Article Updated', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)


@app.route('/delete_article/<string:id>', methods=['POST'])
@login_required
def delete_article(id, *args):
    cur = mysql.connection.cursor()
    cur.execute('delete from articles where id=%s', [id])
    mysql.connection.commit()
    cur.close()

    flash('Article Deleted', 'success')
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
@login_required
def dashboard():
    cur = mysql.connection.cursor()
    rows = cur.execute('select * from articles where author=%s', [session['username']])
    articles =  cur.fetchall()
    cur.close()
    if rows > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)


if __name__ == '__main__':
    app.run()

