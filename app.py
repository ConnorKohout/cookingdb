from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import sqlite3
import os
from werkzeug.utils import secure_filename
import configparser

# Load configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Configuration
UPLOAD_FOLDER = config['DEFAULT']['UPLOAD_FOLDER']
ALLOWED_EXTENSIONS = set(config['DEFAULT']['ALLOWED_EXTENSIONS'].split(','))
SECRET_KEY = config['DEFAULT']['SECRET_KEY']

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = SECRET_KEY  # Use the secret key from the config file

bcrypt = Bcrypt(app)

# The rest of your Flask app code...

# Flask-Login setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email, is_admin=False):
        self.id = id
        self.username = username
        self.email = email
        self.is_admin = is_admin

    @staticmethod
    def get(user_id):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        if not user:
            return None
        return User(user[0], user[1], user[2], bool(user[4]))  # Convert is_admin to a boolean


# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


# Database setup
def connect_db():
    return sqlite3.connect('recipes.db')

def create_database():
    """Create database tables if they do not exist."""
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0  -- 0 means regular user, 1 means admin
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            instructions TEXT,
            cuisine TEXT,
            prep_time INTEGER,
            cook_time INTEGER,
            diet_type TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            ingredient TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes (id)
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            filename TEXT NOT NULL,
            FOREIGN KEY (recipe_id) REFERENCES recipes (id)
        )
        ''')



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def index():
    recipes = get_recipes_by_user(current_user.id) if current_user.is_authenticated else get_all_recipes()
    return render_template('view_recipes.html', recipes=recipes)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        with connect_db() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', 
                               (username, email, hashed_password))
                conn.commit()
                flash('Registration successful. Please log in.')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Username or email already exists.')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            if user and bcrypt.check_password_hash(user[3], password):
                user_obj = User(user[0], user[1], user[2])
                login_user(user_obj)
                flash('Logged in successfully.')
                return redirect(url_for('index'))
            else:
                flash('Invalid credentials. Please try again.')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.')
    return redirect(url_for('login'))

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_recipe():
    if request.method == 'POST':
        try:
            # Log the form data for debugging
            print(request.form)

            # Ensure the form fields are correctly accessed
            name = request.form['name']
            instructions = request.form['instructions']
            cuisine = request.form.get('cuisine', '')
            prep_time = request.form.get('prep_time', 0)
            cook_time = request.form.get('cook_time', 0)
            diet_type = request.form.get('diet_type', '')

            with connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO recipes (user_id, name, instructions, cuisine, prep_time, cook_time, diet_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (current_user.id, name, instructions, cuisine, prep_time, cook_time, diet_type))
                recipe_id = cursor.lastrowid  # Get the ID of the newly inserted recipe

                # Handle multiple image uploads
                if 'photos' in request.files:
                    files = request.files.getlist('photos')
                    for file in files:
                        if file and allowed_file(file.filename):
                            filename = secure_filename(file.filename)
                            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                            cursor.execute('INSERT INTO recipe_images (recipe_id, filename) VALUES (?, ?)', 
                                           (recipe_id, filename))
                
                conn.commit()

            flash('Recipe added successfully!')
            return redirect(url_for('index'))
        except KeyError as e:
            flash(f"Missing data for field: {e.args[0]}")
        except Exception as e:
            flash(f"An error occurred: {e}")

    return render_template('add_recipe.html')




@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    # Fetch the recipe details for the given recipe_id
    recipe = get_recipe_by_user(recipe_id)

    if not recipe:
        flash('Recipe not found.')
        return redirect(url_for('index'))

    # Fetch the ingredients for the given recipe
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM ingredients WHERE recipe_id = ?', (recipe_id,))
        ingredients = cursor.fetchall()

        # Fetch the images for the given recipe
        cursor.execute('SELECT * FROM recipe_images WHERE recipe_id = ?', (recipe_id,))
        images = cursor.fetchall()

    return render_template('recipe_detail.html', recipe=recipe, ingredients=ingredients, images=images)



@app.route('/edit/<int:recipe_id>', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    recipe = get_recipe_by_user(recipe_id)
    if not recipe or recipe[1] != current_user.id:  # Check if the recipe belongs to the current user
        flash('Recipe not found or you do not have permission to edit it.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Get updated recipe data
        name = request.form['name']
        instructions = request.form['instructions']
        cuisine = request.form['cuisine']
        prep_time = request.form['prep_time']
        cook_time = request.form['cook_time']
        diet_type = request.form['diet_type']

        with connect_db() as conn:
            cursor = conn.cursor()

            # Update recipe details
            cursor.execute('''
            UPDATE recipes
            SET name = ?, instructions = ?, cuisine = ?, prep_time = ?, cook_time = ?, diet_type = ?
            WHERE id = ?
            ''', (name, instructions, cuisine, prep_time, cook_time, diet_type, recipe_id))

            # Handle deletion of selected images
            delete_image_ids = request.form.getlist('delete_images')
            if delete_image_ids:
                for image_id in delete_image_ids:
                    cursor.execute('SELECT filename FROM recipe_images WHERE id = ?', (image_id,))
                    image = cursor.fetchone()
                    if image:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image[0]))  # Delete file from filesystem
                        cursor.execute('DELETE FROM recipe_images WHERE id = ?', (image_id,))

            # Handle new image uploads
            if 'new_photos' in request.files:
                files = request.files.getlist('new_photos')
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        cursor.execute('INSERT INTO recipe_images (recipe_id, filename) VALUES (?, ?)', 
                                       (recipe_id, filename))

            conn.commit()

        flash('Recipe updated successfully!')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))

    # Fetch existing images for the recipe
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM recipe_images WHERE recipe_id = ?', (recipe_id,))
        images = cursor.fetchall()

    return render_template('edit_recipe.html', recipe=recipe, images=images)


@app.route('/delete/<int:recipe_id>', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    recipe = get_recipe_by_user(recipe_id)
    if not recipe or recipe[1] != current_user.id:  # Check if the recipe belongs to the current user
        flash('Recipe not found or you do not have permission to delete it.')
        return redirect(url_for('index'))

    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM recipes WHERE id = ?', (recipe_id,))
        conn.commit()

    flash('Recipe deleted successfully!')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    # Fetch the user's recipes
    user_recipes = get_recipes_by_user(current_user.id)
    return render_template('profile.html', user_recipes=user_recipes)

@app.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']

        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE users
            SET username = ?, email = ?
            WHERE id = ?
            ''', (username, email, current_user.id))
            conn.commit()

        flash('Profile updated successfully!')
        return redirect(url_for('profile'))

    return render_template('update_profile.html')


@app.route('/view_others')
def view_others_recipes():
    recipes = get_all_recipes()
    return render_template('view_others_recipes.html', recipes=recipes)

@app.route('/manage')
@login_required
def manage_recipes():
    recipes = get_recipes_by_user(current_user.id)
    return render_template('manage_recipes.html', recipes=recipes)

def get_recipe_by_user(recipe_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT recipes.*, users.username
        FROM recipes
        JOIN users ON recipes.user_id = users.id
        WHERE recipes.id = ?
        ''', (recipe_id,))
        return cursor.fetchone()

def get_recipes_by_user(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT recipes.*, users.username
        FROM recipes
        JOIN users ON recipes.user_id = users.id
        WHERE recipes.user_id = ?
        ''', (user_id,))
        return cursor.fetchall()

def get_all_recipes():
    with connect_db() as conn:
        cursor = conn.cursor()
        # Selecting the necessary columns from recipes and the author's username from users
        cursor.execute('''
        SELECT recipes.id, recipes.name, recipes.instructions, recipes.cuisine, 
               recipes.prep_time, recipes.cook_time, recipes.diet_type, users.username 
        FROM recipes
        JOIN users ON recipes.user_id = users.id
        ''')
        return cursor.fetchall()


@app.route('/search', methods=['GET'])
@login_required
def search_recipes():
    query = request.args.get('query', '').strip()

    if query:
        with connect_db() as conn:
            cursor = conn.cursor()
            # Search for recipes by name, cuisine, or any other field you want
            cursor.execute('''
            SELECT recipes.*, users.username
            FROM recipes
            JOIN users ON recipes.user_id = users.id
            WHERE recipes.name LIKE ? OR recipes.cuisine LIKE ? OR users.username LIKE ?
            ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
            recipes = cursor.fetchall()
    else:
        recipes = []

    return render_template('search_results.html', recipes=recipes, query=query)


@app.route('/create-recipe', methods=['GET', 'POST'])
def create_recipe():
    # Logic to handle recipe creation
    return render_template('create_recipe.html')


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']

        with connect_db() as conn:
            cursor = conn.cursor()
            # Verify the current password
            cursor.execute('SELECT password FROM users WHERE id = ?', (current_user.id,))
            user = cursor.fetchone()

            if user and bcrypt.check_password_hash(user[0], current_password):
                # Update with the new password
                hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
                cursor.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, current_user.id))
                conn.commit()
                flash('Password changed successfully!')
                return redirect(url_for('profile'))
            else:
                flash('Current password is incorrect.')

    return render_template('change_password.html')

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    with connect_db() as conn:
        cursor = conn.cursor()
        # Delete the user's account and associated data
        cursor.execute('DELETE FROM users WHERE id = ?', (current_user.id,))
        cursor.execute('DELETE FROM recipes WHERE user_id = ?', (current_user.id,))
        cursor.execute('DELETE FROM recipe_images WHERE recipe_id IN (SELECT id FROM recipes WHERE user_id = ?)', (current_user.id,))
        conn.commit()

    logout_user()
    flash('Your account has been deleted.')
    return redirect(url_for('index'))


if __name__ == '__main__':
    create_database()
    app.run(debug=True)
