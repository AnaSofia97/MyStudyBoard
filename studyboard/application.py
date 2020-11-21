from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from functools import wraps
from cs50 import SQL

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

app = Flask( __name__ )
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
db = SQL("sqlite:///users.db")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":

        if not request.form.get("username"):
            lang = db.execute("SELECT * FROM language;")
            language = 'EN'
            if language == 'EN':
                return render_template("error.html", message="please, type your username", language=language)
            else:
                return render_template("error.html", message="por favor, escribí tu nombre de usuario", language=language)
        elif not request.form.get("password"):
            lang = db.execute("SELECT * FROM language;")
            language = lang[0]['language']
            if language == 'EN':
                return render_template("error.html", message="please, type your password", language=language)
            else:
                return render_template("error.html", message="por favor, escribí tu contraseña", language=language)
        rows = db.execute("SELECT * FROM user_info WHERE username = :username", username=request.form.get("username"))
        password = request.form.get("password")
        if len(rows) != 1 or rows[0]["password"]!=password:
            lang = db.execute("SELECT * FROM language;")
            language = lang[0]['language']
            if language == 'EN':
                return render_template("error.html", message="invalid username and/or password", language=language)
            else:
                return render_template("error.html", message="usuario o contraseña incorrectos", language=language)
        session["user_id"] = rows[0]["id"]
        return redirect("/")
    else:
        return render_template("login.html", language = 'EN')


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not request.form.get("username"):
            lang = db.execute("SELECT * FROM language;")
            language = lang[0]['language']
            if language == 'EN':
                return render_template("error.html", message="please, choose a username", language=language)
            else:
                return render_template("error.html", message="por favor, elegí un nombre de usuario", language=language)

        elif not request.form.get("password"):
            lang = db.execute("SELECT * FROM language;")
            language = lang[0]['language']
            if language == 'EN':
                return render_template("error.html", message="please, choose a password", language=language)
            else:
                return render_template("error.html", message="por favor, elegí una contraseña", language=language)

        elif not request.form.get("confirmation"):
            lang = db.execute("SELECT * FROM language;")
            language = lang[0]['language']
            if language == 'EN':
                return render_template("error.html", message="please, type your password again", language=language)
            else:
                return render_template("error.html", message="por favor, volvé a escribir tu contraseña", language=language)

        elif confirmation != password:
            lang = db.execute("SELECT * FROM language;")
            language = lang[0]['language']
            if language == 'EN':
                return render_template("error.html", message="please, make sure you type the same password twice", language=language)
            else:
                return render_template("error.html", message="por favor, asegurate de escribir la misma contraseña dos veces", language=language)
        else:
            existing_users=db.execute("SELECT username FROM user_info WHERE username = :username", username=username)
            if not existing_users:
                db.execute("INSERT INTO user_info(username, password) VALUES (:username, :password);", username=request.form.get("username"), password=request.form.get("password"))
                user_id=db.execute("SELECT id FROM user_info WHERE username = :username;", username=request.form.get("username"))
                db.execute("INSERT INTO personalization(user_id, background, font_size, font_type, profile_pic) VALUES (:user_id, 'darkseagreen', 'initial', 'Georgia, serif', '1.png');", user_id=user_id[0]['user_id'])
                return redirect("/")
            else:
                lang = db.execute("SELECT * FROM language;")
                language = lang[0]['language']
                if language == 'EN':
                    return render_template("error.html", message="username already exists", language=language)
                else:
                    return render_template("error.html", message="el nombre de usuario ya existe", language=language)
    else:
        lang = db.execute("SELECT * FROM language;")
        language = 'EN'
        return render_template("register.html", language=language)

@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        action = request.form.get("button")
        new_task = request.form.get("task")
        tasks = db.execute("SELECT task FROM tasks WHERE user_id = :user_id;", user_id = session['user_id'])
        if action == 'Delete all' or action == 'Borrar todo':
            db.execute("DELETE FROM tasks WHERE user_id = :user_id;", user_id = session['user_id'])
        elif action == 'Delete' or action == 'Borrar':
            for i in range(len(tasks)):
                if new_task == tasks[i]['task']:
                    db.execute("DELETE FROM tasks WHERE user_id = :user_id AND task = :task", user_id=session['user_id'], task = new_task)
            else:
                pass
        elif action == 'Add' or action =='Agregar':
            if not new_task:
                pass
            else:
                db.execute("INSERT INTO tasks (user_id, task) VALUES (:user_id, :task);", user_id=session["user_id"], task=new_task)
        return redirect ("/")
    else:
        lang = db.execute("SELECT * FROM language;")
        language = lang[0]['language']
        p_settings = db.execute("SELECT * FROM personalization WHERE user_id = :user_id;", user_id=session["user_id"])
        username = db.execute("SELECT username FROM user_info WHERE id = :user_id;", user_id=session["user_id"])
        tasks = db.execute("SELECT task FROM tasks WHERE user_id = :user_id;", user_id=session['user_id'])
        return render_template("index.html",language=language, username=username[0]['username'], background=p_settings[0]['background'], fontsize=p_settings[0]['font_size'], fontfamily=p_settings[0]['font_type'], profilepic=p_settings[0]['profile_pic'], tasks=tasks)

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == 'POST':
        is_pressed_change_username = request.form.get("change_username")
        is_pressed_change_password = request.form.get("change_password")
        is_pressed_delete_account = request.form.get("delete_account")
        is_pressed_language = request.form.get("language")
        new_username = request.form.get("new_username")
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        user_info = db.execute("SELECT * FROM user_info WHERE id = :user_id;", user_id=session["user_id"])

        if is_pressed_change_username == 'true':
            if not new_username:
                lang = db.execute("SELECT * FROM language;")
                language = lang[0]['language']
                p_settings=db.execute("SELECT * FROM personalization WHERE user_id = :user_id;", user_id=session["user_id"])
                username=db.execute("SELECT username FROM user_info WHERE id = :user_id", user_id=session["user_id"])
                if language == 'EN':
                    return render_template("error.html", language=language, message="please, choose a new username", username=username[0]['username'], background=p_settings[0]['background'], fontsize=p_settings[0]['font_size'], fontfamily=p_settings[0]['font_type'], profilepic=p_settings[0]['profile_pic'])
                else:
                    return render_template("error.html", language=language, message="por favor, elegí un nuevo nombre de usuario", username=username[0]['username'], background=p_settings[0]['background'], fontsize=p_settings[0]['font_size'], fontfamily=p_settings[0]['font_type'], profilepic=p_settings[0]['profile_pic'])
            else:
                db.execute("UPDATE user_info SET username = :username WHERE id = :user_id;", username=new_username, user_id=session["user_id"])
                return redirect("/")
        elif is_pressed_change_password == 'true':
            if not current_password:
                lang = db.execute("SELECT * FROM language;")
                language = lang[0]['language']
                p_settings=db.execute("SELECT * FROM personalization WHERE user_id = :user_id;", user_id=session["user_id"])
                username=db.execute("SELECT username FROM user_info WHERE id = :user_id", user_id=session["user_id"])
                if language == 'EN':
                    return render_template("error.html", language=language, message="please, type your current password", username=username[0]['username'], background=p_settings[0]['background'], fontsize=p_settings[0]['font_size'], fontfamily=p_settings[0]['font_type'], profilepic=p_settings[0]['profile_pic'])
                else:
                    return render_template("error.html", language=language, message="por favor, ingresá tu contraseña actual", username=username[0]['username'], background=p_settings[0]['background'], fontsize=p_settings[0]['font_size'], fontfamily=p_settings[0]['font_type'], profilepic=p_settings[0]['profile_pic'])
            elif not new_password:
                lang = db.execute("SELECT * FROM language;")
                language = lang[0]['language']
                p_settings=db.execute("SELECT * FROM personalization WHERE user_id = :user_id;", user_id=session["user_id"])
                username=db.execute("SELECT username FROM user_info WHERE id = :user_id", user_id=session["user_id"])
                if language == 'EN':
                    return render_template("error.html", language=language, message="please, choose a new password", username=username[0]['username'], background=p_settings[0]['background'], fontsize=p_settings[0]['font_size'], fontfamily=p_settings[0]['font_type'], profilepic=p_settings[0]['profile_pic'])
                else:
                    return render_template("error.html", language=language, message="por favor elegí una nueva contraseña", username=username[0]['username'], background=p_settings[0]['background'], fontsize=p_settings[0]['font_size'], fontfamily=p_settings[0]['font_type'], profilepic=p_settings[0]['profile_pic'])
            elif current_password != user_info[0]['password']:
                lang = db.execute("SELECT * FROM language;")
                language = lang[0]['language']
                p_settings=db.execute("SELECT * FROM personalization WHERE user_id = :user_id;", user_id=session["user_id"])
                username=db.execute("SELECT username FROM user_info WHERE id = :user_id", user_id=session["user_id"])
                if language == 'EN':
                    return render_template("error.html", language=language, message="please, make sure your current password is well typed", username=username[0]['username'], background=p_settings[0]['background'], fontsize=p_settings[0]['font_size'], fontfamily=p_settings[0]['font_type'], profilepic=p_settings[0]['profile_pic'])
                else:
                    return render_template("error.html", language=language, message="por favor, asegurte de que tu contraseña actual esté bien escrita", username=username[0]['username'], background=p_settings[0]['background'], fontsize=p_settings[0]['font_size'], fontfamily=p_settings[0]['font_type'], profilepic=p_settings[0]['profile_pic'])
            else:
                db.execute("UPDATE user_info SET password = :password WHERE id = :user_id;", password = new_password, user_id=session["user_id"])
                return redirect("/")
        elif is_pressed_delete_account == 'true':
            db.execute("DELETE FROM user_info WHERE id = :user_id;", user_id=session["user_id"])
            return redirect("/")
        elif is_pressed_language == 'SP':
            db.execute("UPDATE language SET language = 'SP';")
            return redirect ("/")
        elif is_pressed_language == 'EN':
            db.execute("UPDATE language SET language = 'EN';")
            return redirect ("/")
    else:
        lang = db.execute("SELECT * FROM language;")
        language = lang[0]['language']
        p_settings=db.execute("SELECT * FROM personalization WHERE user_id = :user_id;", user_id=session["user_id"])
        username=db.execute("SELECT username FROM user_info WHERE id = :user_id", user_id=session["user_id"])
        return render_template("settings.html", language=language, username=username[0]['username'], background=p_settings[0]['background'], fontsize=p_settings[0]['font_size'], fontfamily=p_settings[0]['font_type'], profilepic=p_settings[0]['profile_pic'])

@app.route("/personalization", methods=["GET", "POST"])
@login_required
def personalization():
    if request.method =="POST":
        button = request.form.get("button")
        if button == 'green':
            db.execute("UPDATE personalization SET background = 'darkseagreen' WHERE user_id = :user_id;", user_id=session["user_id"])
            return redirect ("/personalization")
        elif button == 'yellow':
            db.execute("UPDATE personalization SET background = 'moccasin' WHERE user_id = :user_id;", user_id=session["user_id"])
            return redirect ("/personalization")
        elif button == 'blue':
            db.execute("UPDATE personalization SET background = 'lightskyblue' WHERE user_id = :user_id;", user_id=session["user_id"])
            return redirect ("/personalization")
        elif button == 'pink':
            db.execute("UPDATE personalization SET background = 'pink' WHERE user_id = :user_id;", user_id=session["user_id"])
            return redirect ("/personalization")

        elif button == 'small':
            db.execute("UPDATE personalization SET font_size = 'small' WHERE user_id = :user_id;", user_id=session["user_id"])
            return redirect ("/personalization")
        elif button == 'medium':
            db.execute("UPDATE personalization SET font_size = 'initial' WHERE user_id = :user_id;", user_id=session["user_id"])
            return redirect ("/personalization")
        elif button == 'large':
            db.execute("UPDATE personalization SET font_size = 'large' WHERE user_id = :user_id;", user_id=session["user_id"])
            return redirect ("/personalization")

        elif button == 'arial':
            db.execute("UPDATE personalization SET font_type = 'Arial, Helvetica, sans-serif' WHERE user_id = :user_id;", user_id=session["user_id"])
            return redirect ("/personalization")
        elif button == 'georgia':
            db.execute("UPDATE personalization SET font_type = 'Georgia, serif' WHERE user_id = :user_id;", user_id=session["user_id"])
            return redirect ("/personalization")
        elif button == 'monospace':
            db.execute("UPDATE personalization SET font_type = 'Lucida Console, Monaco, monospace' WHERE user_id = :user_id;", user_id=session["user_id"])
            return redirect ("/personalization")

        elif button == '1':
            db.execute("UPDATE personalization SET profile_pic = '1.png' WHERE user_id = :user_id;", user_id=session["user_id"])
            return redirect ("/personalization")
        elif button == '2':
            db.execute("UPDATE personalization SET profile_pic = '2.png' WHERE user_id = :user_id;", user_id=session["user_id"])
            return redirect ("/personalization")
        elif button == '3':
            db.execute("UPDATE personalization SET profile_pic = '3.jpg' WHERE user_id = :user_id;", user_id=session["user_id"])
            return redirect ("/personalization")
        elif button == '4':
            db.execute("UPDATE personalization SET profile_pic = '4.png' WHERE user_id = :user_id;", user_id=session["user_id"])
            return redirect ("/personalization")
        elif button == '5':
            db.execute("UPDATE personalization SET profile_pic = '5.png' WHERE user_id = :user_id;", user_id=session["user_id"])
            return redirect ("/personalization")
        elif button == '6':
            db.execute("UPDATE personalization SET profile_pic = '6.jpg' WHERE user_id = :user_id;", user_id=session["user_id"])
            return redirect ("/personalization")
        elif button == '7':
            db.execute("UPDATE personalization SET profile_pic = '7.jpg' WHERE user_id = :user_id;", user_id=session["user_id"])
            return redirect ("/personalization")
        elif button == '8':
            db.execute("UPDATE personalization SET profile_pic = '8.jpg' WHERE user_id = :user_id;", user_id=session["user_id"])
            return redirect ("/personalization")
        elif button == '9':
            db.execute("UPDATE personalization SET profile_pic = '9.png' WHERE user_id = :user_id;", user_id=session["user_id"])
            return redirect ("/personalization")

    else:
        lang = db.execute("SELECT * FROM language;")
        language = lang[0]['language']
        p_settings=db.execute("SELECT * FROM personalization WHERE user_id = :user_id;", user_id=session["user_id"])
        username=db.execute("SELECT username FROM user_info WHERE id = :user_id", user_id=session["user_id"])
        return render_template("personalization.html", language=language, username=username[0]['username'], background=p_settings[0]['background'], fontsize=p_settings[0]['font_size'], fontfamily=p_settings[0]['font_type'], profilepic=p_settings[0]['profile_pic'])