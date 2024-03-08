from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user, LoginManager
from flask import Flask, render_template, request, redirect, flash, session, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_bcrypt import Bcrypt
from datetime import datetime
from flask_gzip import Gzip
from functions import *
import requests
import random

# initiating flask app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = '63e9c7ec799576e61f8d7fe6280249bbda073a760438a758a20ca44272e23c13'

# Initialize loginManager, bcrypt, cache, gzip
login_manager = LoginManager(app)
bcrypt = Bcrypt(app)
cache = Cache(app, config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 3600})  # 3600 seconds (1hour) timeout
gzip = Gzip(app) # Gzip is a method of compressing files for faster network transfers.

# Initialize the app and migration with the extension
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# creating models for db
class Users(UserMixin, db.Model):
    __tablename__ = 'users' 
    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(100), unique=True, index=True)
    hash = db.Column(db.String)
    id_registerd = db.Column(db.String(20), nullable=False)
    
    # Establishing a one-to-many relationship between Users and game_data
    game_data = db.relationship('GameData', backref='user', lazy=True, cascade='all, delete-orphan')

    def __init__(self, name, hash, id_registerd):
        self.name = name
        self.hash = hash
        self.id_registerd = id_registerd


class GameData(db.Model):
    __tablename__ = 'game_data' 
    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    game_id = db.Column(db.Integer, index=True)
    game_name = db.Column(db.String, nullable=False, index=True)
    game_image = db.Column(db.String, nullable=True)

    def __init__(self, user_id, game_id, game_name, game_image):
        self.user_id = user_id
        self.game_id = game_id
        self.game_name = game_name
        self.game_image = game_image
        
        
        
        
class UserPreferences(db.Model):
    __tablename__ = 'user_preferences'
    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Preferences without string limitations
    selected_genres = db.Column(db.JSON)  # Assuming you're using PostgreSQL or similar supporting JSON
    selected_devs = db.Column(db.JSON)
    selected_pubs = db.Column(db.JSON)
    selected_plats = db.Column(db.JSON)
    selected_order = db.Column(db.JSON)

    # Define a relationship with Users model
    user = db.relationship('Users', backref='preferences', lazy=True)

    def __init__(self, user_id, selected_genres=None, selected_devs=None, selected_pubs=None, selected_plats=None, selected_order=None):
        self.user_id = user_id
        self.selected_genres = selected_genres
        self.selected_devs = selected_devs
        self.selected_pubs = selected_pubs
        self.selected_plats = selected_plats
        self.selected_order = selected_order





# handeling the erros
@app.errorhandler(404)
def internal_server_error(error):
    return redirect("/")

@app.errorhandler(502)
def internal_server_error(error):
    flash("API overload, Reload the page")
    return redirect("/")

@app.errorhandler(500)
def internal_server_error(error):
    flash("Oops Something went wrong")
    return redirect("/")


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

with app.app_context():
    db.create_all()

def check_password_login(user_pass, check_password):
    return bcrypt.check_password_hash(user_pass.hash, check_password)

# front page
@cache.cached(timeout=120)
@app.route('/')
def index():
    top_10_data = top_10_ranked_games()
    top_this_year_data = top_released_games_this_year()
    genres_data = get_genres()
    usr_game_db = get_added_game_datas()
    rand_quotes = get_random_quote()
    
    
    # Retrieve user preferences from the database
    if current_user.is_authenticated:
        user_preferences = UserPreferences.query.filter_by(user_id=current_user.id).first()
    
    
        if user_preferences:
            selected_genres = user_preferences.selected_genres
            selected_devs = user_preferences.selected_devs
            selected_pubs = user_preferences.selected_pubs
            selected_plats = user_preferences.selected_plats
            selected_order = user_preferences.selected_order

            if any([selected_genres, selected_devs, selected_pubs, selected_plats, selected_order]):
                recommended = get_recommandation(selected_genres, 
                                                selected_devs, 
                                                selected_pubs, 
                                                selected_order, 
                                                selected_plats)
                return render_template('front_page.html', rec_games=recommended, 
                                                        usr_games=usr_game_db, 
                                                        top10=top_10_data, 
                                                        top_this_year=top_this_year_data, 
                                                        genres=genres_data,
                                                        showGS=True, 
                                                        title="Gamefo")

    # If no preferences are found, render the front page without recommendations
    return render_template('front_page.html',rand_quotes=rand_quotes, usr_games=usr_game_db, top10=top_10_data, top_this_year=top_this_year_data, genres=genres_data, showGS=True, title="Gamefo")


@app.route('/search')
def search():
    return render_template('search_page.html',showGS = True, title="Search Game")



@app.route('/get_started')
def get_started():
    if current_user.is_authenticated:
        return redirect("/") 
    password_check = session.pop('password_check', None)
    return render_template("get_started.html", showGS=False, password_check=password_check)




# Global variabels for next prev page
next_url = ""
prev_url = ""


# Get the data of the specefic game
@cache.cached(timeout=3600)
@app.route('/get_games', methods=['GET', 'POST'])
@login_required
def get_games():
    if request.method == "POST":
        global next_url
        global prev_url
        
        game_name = request.form.get("search")
        if not game_name:
            flash("Input field empty")
            return redirect("/")

        game_data_get, data_page = game_data(game_name)
        if game_data_get:
            
            if data_page.get("next"):
                next_url = data_page.get("next")
            else:
                next_url = ""
            
            if data_page.get("previous"):
                prev_url = data_page.get("previous")
            else:
                prev_url = ""
                
 
            usr_game_db = get_added_game_datas()
            
            
            return render_template("search_page.html", games_data=game_data_get, p_u=prev_url, n_u=next_url, usr_games = usr_game_db, title=f"Gamefo : {game_name} ")
        
        else:
            flash("game not found")
            return redirect("/")
    else:
        flash("eh?")
        redirect("/")


# Next page button functions
@cache.cached(timeout=3600)
@app.route('/next', methods=['GET', 'POST'])
@login_required
def get__next_games():
    global next_url
    global prev_url

    params = {
        "page_size": 15,  # Adjust as needed
        "key": api_key_rawg  # Add the API key to the parameters
    }
    
    
    response = requests.get(next_url, params=params)
    
    if response.status_code == 200:
        next_page = response.json()
        if next_page.get("next"):
            next_url = next_page.get("next")
        else:
            next_url = ""
            
        if next_page.get("previous"):
            prev_url = next_page.get("previous")
        else:
            prev_url = ""
            
        
        game_data_get = next_page.get("results", [])
        if game_data_get:
            usr_game_db = get_added_game_datas()
            return render_template("search_page.html",usr_games = usr_game_db, games_data=game_data_get, p_u=prev_url, n_u=next_url, title=f"Gamefo")
        else:
            flash("game_data_get_error")
            usr_game_db = get_added_game_datas()
            return render_template("search_page.html",usr_games = usr_game_db)
    else:
        flash("No Line further")
        usr_game_db = get_added_game_datas()
        return render_template("search_page.html",usr_games = usr_game_db)


# Previous page functions
@cache.cached(timeout=3600)
@app.route('/previous', methods=['GET', 'POST'])
@login_required
def get__prev_games():
    global next_url
    global prev_url

    params = {
        "page_size": 15,  # Adjust as needed
        "key": api_key_rawg  # Add the API key to the parameters
    }
    
    
    response = requests.get(prev_url, params=params)
    
    if response.status_code == 200:
        prev_page = response.json()
        if prev_page.get("previous"):
            prev_url = prev_page.get("previous")
        else:
            prev_url = ""
            
        if prev_page.get("next"):
            next_url = prev_page.get("next")
        else:
            next_url = ""
        
        game_data_get = prev_page.get("results", [])
        if game_data_get:
            usr_game_db = get_added_game_datas()
            return render_template("search_page.html",usr_games = usr_game_db, games_data=game_data_get, p_u=prev_url, n_u=next_url, title=f"Gamefo")
        else:
            usr_game_db = get_added_game_datas()
            flash("game_data_get_error")
            return render_template("search_page.html",usr_games = usr_game_db)
    else:
        flash("No Line further")
        usr_game_db = get_added_game_datas()
        return render_template("search_page.html",usr_games = usr_game_db)
    
# Per Game page
@cache.cached(timeout=3600)
@app.route('/games/<game_id>', methods=['GET', 'POST'])
def game_info(game_id):
    game_details = per_game_detail(game_id)
    
    if game_details is not None:
        games, screenshots, dlcs = game_details
        user_game_db = get_added_game_datas()
        return render_template('game_page.html', game_data=games, game_shots=screenshots, game_dlc=dlcs, user_game_db=user_game_db, title=f"Gamefo: {games['name']}")
    else:
        flash("Game not found. Redirecting to a new random game.", "error")
        return redirect("/pick-and-play")



# get genre games
@cache.cached(timeout=3600)
@app.route('/genres/<genre_id>', methods=['GET', 'POST'])
def genre_game_info(genre_id):
    global next_url
    global prev_url
    
    game_data_get, data_page = genre_game_detail(genre_id)
    if game_data_get:
        if data_page.get("next"):
            next_url = data_page.get("next")
        else:
            next_url = ""
        
        if data_page.get("previous"):
            prev_url = data_page.get("previous")
        else:
            prev_url = ""
            
        usr_game_db = get_added_game_datas()
        return render_template("search_page.html",usr_games = usr_game_db, games_data=game_data_get, p_u=prev_url, n_u=next_url, title=f"Genres")
    
    else:
        flash("inavid genres not found")
        return redirect("/")



# add-game in library/database
@app.route('/add_game', methods=['GET', 'POST'])
def add_game():
    
    if not current_user.is_authenticated:
       return redirect(url_for('login'))
   
   
    game_id = request.form.get("game_id")   
    game_name = request.form.get("game_name")   
    game_image = request.form.get("image_url")   
    current_user_id = current_user.id
    
    data = GameData.query.filter_by(user_id=current_user_id, game_id=game_id).first()
    if data:
        flash("Game already in the account", "error")
        return redirect(url_for('game_info', game_id=str(game_id) ))
    
    add_game_data = GameData(
        user_id = current_user_id,
        game_id = game_id,
        game_name = game_name,
        game_image = game_image,
    )
    
    db.session.add(add_game_data)
    db.session.commit()
    

    flash("Game added to your profile", "success")    
    return redirect(url_for('game_info', game_id=str(game_id) ))

# remove-game for library/database
@app.route('/remove_game', methods=['GET', 'POST'])
def delete_game():
    if not current_user.is_authenticated:
       return redirect(url_for('login'))
   
   
    game_id = request.form.get("game_id")   
    current_user_id = current_user.id
    
    game_to_delete = GameData.query.filter_by(user_id = current_user_id, game_id = game_id).first()
    
    if not game_to_delete:
        flash("Game not found or you don't have permission to delete it", "error")
        return redirect("/")
    
    db.session.delete(game_to_delete)
    db.session.commit()
    
    flash("Game deleted successfully", "success")
    # return redirect(url_for('dashbord'))
    return redirect("/")
    

# fething tags, genres, platforms, publishers, developers 
@cache.cached(timeout=3600)
@app.route('/game-picker', methods=['GET', 'POST'])
@login_required
def game_picker():
    genres = get_genres()
    tags = get_tags()
    platforms = get_platforms()
    publishers = get_publishers()
    developers = get_developers()
    return render_template("game_picker.html", tags=tags, 
                                            genres=genres, 
                                            platforms=platforms, 
                                            publishers=publishers, 
                                            developers=developers, 
                                            title="Game Picker")
    

# Game Filterer 
@cache.cached(timeout=3600)
@app.route('/game-picker/random-game', methods=['GET', 'POST'])
@login_required
def random_game():
    if request.method == 'POST':
        selected_tags = request.form.getlist("selected_tags")
        selected_genres = request.form.getlist("selected_genres")
        selected_platforms = request.form.getlist("selected_platforms")
        selected_publishers = request.form.getlist("selected_publishers")
        selected_developers = request.form.getlist("selected_developers")
        selected_order = request.form.getlist("selected_ordering[]")


        print(f"Selected Tags: {selected_tags}")
        print(f"Selected Genres: {selected_genres}")
        print(f"Selected Order: {selected_order}")

        results, data = filter_game(selected_genres,
                                    selected_tags, 
                                    selected_platforms,
                                    selected_publishers,
                                    selected_developers,
                                    selected_order)
        
        usr_game_db = get_added_game_datas()

        global next_url
        global prev_url
        if results:
            if data and data.get("next"):
                next_url = data.get("next")
            else:
                next_url = ""

            if data and data.get("previous"):
                prev_url = data.get("previous")
            else:
                prev_url = ""

        return render_template("rng_game.html", game_found=results, p_u=prev_url, n_u=next_url, usr_games=usr_game_db, title="Filtered Games")

    return redirect(url_for('game_picker'))


# set preferances from my_acc
@cache.cached(timeout=3600)
@app.route('/preferance', methods=['GET', 'POST'])
@login_required
def rec_game_usr():
    if request.method == 'POST':
        current_user_id = current_user.id
        
    # Get the existing user preferences or create a new one
    
        user_preferences = UserPreferences.query.filter_by(user_id=current_user_id).first()
    
    # Check if the user already has preferences
        if user_preferences:
            # If preferences exist, delete the existing ones
            db.session.delete(user_preferences)
            db.session.commit()
                
        # Create new preferences with the updated values
        selected_genres = request.form.getlist("selected_genres")
        selected_devs = request.form.getlist("selected_devs")
        selected_pubs = request.form.getlist("selected_pubs")
        selected_plats = request.form.getlist("selected_plats")
        selected_order = request.form.getlist("selected_ordering[]")
        
        # Create a new UserPreferences object
        user_preferences = UserPreferences(user_id=current_user_id,
                                        selected_genres=selected_genres,
                                        selected_devs=selected_devs,
                                        selected_pubs=selected_pubs,
                                        selected_plats=selected_plats,
                                        selected_order=selected_order)
            
        # Save the new preferences to the database
        db.session.add(user_preferences)
        db.session.commit()
            
        flash("Your preferences have been updated successfully.", "success")
        return redirect(url_for('my_acc'))
    return redirect(url_for('my_acc'))


# random game generator
@cache.cached(timeout=3600) 
@app.route('/pick-and-play', methods=['GET', 'POST'])
@login_required
def random_game_selector():
    
    # Retrieve user preferences from the database
    user_preferences = UserPreferences.query.filter_by(user_id=current_user.id).first()

    
    if user_preferences:
        selected_genres = user_preferences.selected_genres
        selected_devs = user_preferences.selected_devs
        selected_pubs = user_preferences.selected_pubs
        selected_plats = user_preferences.selected_plats
        selected_order = user_preferences.selected_order

        # Check if any of the preferences exist
        if any([selected_genres, selected_devs, selected_pubs, selected_plats, selected_order]):
            game_id_no = advanced_game_randomizer(selected_genres, selected_devs, selected_pubs, selected_plats, selected_order)
            if game_id_no:  
                return redirect(f"/games/{game_id_no}")

    # If no preferences are found or no game is selected, generate a random game ID
    random_number = random.randint(1, get_total_games())
    return redirect(f"/games/{random_number}")

# games database setting for each user
def get_added_game_datas():
    if current_user.is_authenticated:
        current_user_id = current_user.id

        data = GameData.query.filter_by(user_id=current_user_id).all()

        existing_data = [
            {
                "user_id": entry.user_id,
                "game_id": entry.game_id,
                "game_name": entry.game_name,
                "image_url": entry.game_image,
            }
            for entry in data
        ]

        return existing_data

    return []







# REGISTER USER
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        
        
        if not name or not password:
            flash("Please provide both a username and password.", "error")
            return redirect("/get_started")
        
        if not confirm_password:
            flash("please confirm the password")
            return redirect("/get_started")
        
        if confirm_password != password:
            flash("Password mismatch")
            return redirect("/get_started")
            
        result = check_password(password)
        if "All requirements passed!" in result:
            # Continue with the registration process
            hash_pass = bcrypt.generate_password_hash(password).decode('utf-8')
        
            existing_user_name = Users.query.filter_by(name=name).first()
            if existing_user_name:
                flash("Username already exists. Please choose a different one.", "error")
                return redirect("/get_started")
            
            
        
            new_user = Users(name=name, 
                             hash=hash_pass,
                             id_registerd=datetime.now().strftime("%d %B %Y"))
            
            db.session.add(new_user)
            db.session.commit()
        
            # Log in the user using Flask-Login's login_user function
            login_user(new_user)

            flash("Registration success. You are now logged in.", "success")
            return redirect("/")
        else:
            # Display the error messages
            return render_template("get_started.html", password_check=result, title="Get started")

    return render_template("get_started.html")





# LOGIN USER
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name")
        password = request.form.get("password")
        
        if not name and not password:
            flash("Please Provide both username and password") 
            return redirect("/login")
        
        check_name = Users.query.filter_by(name=name).first()
        if check_name:
            if check_password_login(check_name, password):
                login_user(check_name)
                flash(f"You are logged in as {name}", "success")
                return redirect("/")
            else:
                flash("Password mismatch") 
                return redirect("/login")
                
        else:
            flash("User Not Found")         
            return redirect("/login")
    return render_template("get_started.html")


# Change Username
@app.route('/change_username', methods=["GET", "POST"])
@login_required
def change_username():
    if request.method == "POST":
        old_name = request.form.get("old_usrn")
        new_name = request.form.get("new_usrn")
        password = request.form.get("con_pass")
        
        if not old_name and not password and not new_name:
            flash("Please Provide All the necessary information", "error") 
            return redirect("/my-account")
        
        user = Users.query.filter_by(name=old_name).first()
        if user.name == "test_account":
            flash("you can't change the test account name")
            return redirect(url_for('my_acc'))
        
        
        if user:
 
            existing_user_name = Users.query.filter_by(name=new_name).first()
            if existing_user_name:
                flash("Username already exists. Please choose a different one.", "error")
                return redirect("/my-account")
            
            if check_password_login(user, password):
                
                user.name = new_name
                db.session.commit()
                
                flash(f"User info updates successfully", "success")
                return redirect("/my-accologoutunt")
            else:
                flash("Password mismatch") 
                return redirect("/my-account")
                
        else:
            flash("User Not Found")         
            return redirect("/my-account")
    return redirect("/my-account")


# Change Password
@app.route('/change_password', methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old_pass = request.form.get("old_pass")
        new_pass = request.form.get("new_pass")
        con_password = request.form.get("new_con_pass")
        
        if not old_pass and not new_pass and not con_password:
            flash("Please Provide All the necessary information", "error") 
            return redirect("/my-account")
        
         
        
        user = Users.query.filter_by(id=current_user.id).first()
        if user.name == "test_account":
            flash("you can't change the test account password")
            return redirect(url_for('my_acc'))
        
        if user:
            if check_password_login(user, old_pass):
                  
                if new_pass != con_password:
                    flash("New password mismatch") 
                    return redirect("/my-account") 
                
                if check_password_login(user, new_pass):
                    flash("You had used a similar password before. Please choose a new unique password.", "error")
                    return redirect("/my-account")
                
                result = check_password(new_pass)
                if "All requirements passed!" in result:
                    hash_pass = bcrypt.generate_password_hash(new_pass).decode('utf-8')              
                    user.hash = hash_pass
                    db.session.commit()
                    flash(f"Password updates successfully", "success")
                    return redirect("/my-account")
                else:
                    # Display the error messages
                    flash("week password", "error")
                    return redirect("/my-account")
                
                
            else:
                flash("Old password mismatch") 
                return redirect("/my-account")
    else:
        return redirect("/my-account")




# LOGOUT USER
@app.route('/logout', methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect("/")


@app.route('/delete_acc', methods=["GET", "POST"])
@login_required
def delete_acc():
    if not current_user.is_authenticated:
       return redirect(url_for('login'))
   
    current_user_id = current_user.id
    user_info = Users.query.filter_by(id=current_user_id).first()
    if user_info.name == "test_account":
        flash("you can't delete the test account")
        return redirect(url_for('my_acc'))
    
    # Delete user's game data
    user_game_data = GameData.query.filter_by(user_id=current_user_id).all()
    for game_data in user_game_data:
        db.session.delete(game_data)

    # Delete user's preferences
    user_preferences = UserPreferences.query.filter_by(user_id=current_user_id).first()
    if user_preferences:
        db.session.delete(user_preferences)

    # Delete the user
    user_info = Users.query.filter_by(id=current_user_id).first()
    
    db.session.delete(user_info)
    db.session.commit()
    
    logout_user()
    flash("Account successfully deleted", "success")
    return redirect("/")


# about page
@app.route('/about-page', methods=["GET", "POST"])
def about_page():
    return render_template("about_page.html")


# my_account
@app.route('/my-account', methods=["GET", "POST"])
@login_required
def my_acc():
    current_user_id = current_user.id
    devs = get_developers()
    pubs = get_publishers()
    plats = get_platforms()
    genres = get_genres()
    
    if not current_user.is_authenticated:
       return redirect(url_for('login'))
   
    user_data = {
    "user_name": current_user.name,
    "hashed_password": current_user.hash,
    "register_date": current_user.id_registerd,
    "games_count": GameData.query.filter_by(user_id=current_user_id).count(),
    "game_data": get_added_game_datas(),
    }   
   
    return render_template("user_page.html", usr_data = user_data,devs=devs, pubs=pubs, plats=plats,genres=genres, title="Account")






if __name__ == '__main__':
    app.run(debug=True)
