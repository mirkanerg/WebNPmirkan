#app.py
#Login-Manager Quelle: https://www.youtube.com/watch?v=71EU8gnZqZQ

#import bcrypt
from flask import Flask, render_template, redirect, url_for, request, abort, flash
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
import forms
#from flask_bcrypt import Bcrypt
from flask import jsonify

app = Flask(__name__) #Flask Instanz

app.config.from_mapping(
    SECRET_KEY = 'secret_key_just_for_dev_environment',
    BOOTSTRAP_BOOTSWATCH_THEME = 'pulse'
)



from db import db, Todo, List, insert_sample, User # (1.)
from forms import RegisterForm, LoginForm

bootstrap = Bootstrap5(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/index') #routen werden an todos weiter geleitet
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/todos/', methods=['GET', 'POST'])
@login_required
def todos(): # Ausführung der Funktion todos() bei Route '/todos/'
    form = forms.CreateTodoForm()
    if request.method == 'GET':
        todos = db.session.execute(db.select(Todo).order_by(Todo.id)).scalars() # alle todos in db nach id geordnet in Variable gespeichert
        return render_template('todos.html', todos=todos, form=form) 
    else:  # request.method == 'POST'
        if form.validate():
            todo = Todo(description=form.description.data)  #!!description = StringField(validators=[InputRequired(), Length(min=5)]) !!
            db.session.add(todo)  # !! Hinzufügen zu db
            db.session.commit()  # !! Speichern in db
            flash('Todo has been created.', 'success')
        else:
            flash('No todo creation: validation error.', 'warning')
        return redirect(url_for('todos'))

@app.route('/todos/<int:id>', methods=['GET', 'POST'])
@login_required
def todo(id):
    todo = db.session.get(Todo, id)  # !!
    form = forms.TodoForm(obj=todo)  # (2.)  # !!
    if request.method == 'GET':
        if todo:
            if todo.lists: form.list_id.data = todo.lists[0].id  # (3.)  # !!
            choices = db.session.execute(db.select(List).order_by(List.name)).scalars()  # !!
            form.list_id.choices = [(0, 'List?')] + [(c.id, c.name) for c in choices]  # !!
            return render_template('todo.html', form=form)
        else:
            abort(404)
    else:  # request.method == 'POST'
        if form.method.data == 'PATCH':
            if form.validate():
                form.populate_obj(todo)  # (4.)
                todo.populate_lists([form.list_id.data])  # (5.)  # !!
                db.session.add(todo)  # !!
                db.session.commit()  # !!
                flash('Todo has been updated.', 'success')
            else:
                flash('No todo update: validation error.', 'warning')
            return redirect(url_for('todo', id=id))
        elif form.method.data == 'DELETE':
            db.session.delete(todo)  # !!
            db.session.commit()  # !!
            flash('Todo has been deleted.', 'success')
            return redirect(url_for('todos'), 303)
        else:
            flash('Nothing happened.', 'info')
            return redirect(url_for('todo', id=id))

@app.route('/lists/')
@login_required
def lists():
    lists = db.session.execute(db.select(List).order_by(List.name)).scalars()  # (6.)  # !!
    return render_template('lists.html', lists=lists)

@app.route('/lists/<int:id>')
@login_required
def list(id):
    list = db.session.get(List, id)  # !!
    if list is not None:
        return render_template('list.html', list=list)
    else:
        return redirect(url_for('lists'))

@app.route('/insert/sample')
def run_insert_sample():
    insert_sample()
    return 'Database flushed and populated with some sample data.'

@app.errorhandler(404)
def http_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def http_internal_server_error(e):
    return render_template('500.html'), 500

@app.get('/faq/<css>')
@app.get('/faq/', defaults={'css': 'default'})
def faq(css):
    return render_template('faq.html', css=css)

@app.get('/ex/<int:id>')
@app.get('/ex/', defaults={'id':1})
def ex(id):
    if id == 1:
        return render_template('ex1.html')
    elif id == 2:
        return render_template('ex2.html')
    else:
        abort(404)



@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:  # Vergleich des Passworts
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)


@app.route('/api/logindata', methods=['GET']) # Anzeigen der Logindaten in DB für DEVS (Später Löschen)
def logindata():
    users = User.query.all()  
    user_list = [f"User ID: {user.id}, Username: {user.username}, Password: {user.password}" for user in users]

    return jsonify(user_list)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    return render_template('profile.html')

@app.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():

        # Löschen Sie das Benutzerkonto und führen Sie eine Abmeldung durch
            db.session.delete(current_user)
            db.session.commit()
            logout_user()
            flash('Ihr Konto wurde erfolgreich gelöscht.', 'success')
            return redirect(url_for('login'))
       


@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        #hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=form.password.data)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


if __name__ == "__main__":
    app.run(debug=True)
        