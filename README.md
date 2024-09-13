# Recipe Book Web Application

A web application for managing, sharing, and discovering recipes. Users can register, log in, add, edit, and delete their recipes, and view recipes shared by others. The application includes features like dark mode, image uploads, and a responsive design.

## Features

- **User Authentication**: Register, log in, and manage user profiles.
- **Recipe Management**: Add, edit, delete, and view recipes.
- **Image Uploads**: Customize recipes with images.
- **Dark Mode**: Toggle between light and dark modes for better accessibility.
- **Responsive Design**: Optimized for both desktop and mobile devices.
- **Search Functionality**: Search for recipes based on keywords.
- **Sidebar Navigation**: Quick access to different sections of the app.

## Technologies Used

- **Flask**: Backend framework to handle routing, authentication, and data processing.
- **SQLite**: Lightweight database for storing user and recipe data.
- **Jinja2**: Template engine for dynamic HTML rendering.
- **Flask-Login**: User authentication management.
- **Flask-Bcrypt**: Password hashing for secure storage.
- **HTML/CSS**: Frontend design with responsive and dark mode styles.
- **JavaScript**: Dynamic behavior for theme switching and interactive features.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/ConnorKohout/cookingdb
   cd cooking
2. **Create a virtual environment:**

    python -m venv venv
    source venv/bin/activate   # On Windows use `venv\Scripts\activate`
3. **Install the dependencies:**

    pip install -r requirements.txt
4. **Run the application:**
    python app.py
5. **Open your web browser and visit:**

    http://127.0.0.1:5000
    
### Project Structure
```

    recipe-book-app/
    ├── app.py                # Main application file
    ├── requirements.txt      # Python dependencies
    ├── static/
    │   ├── css/
    │   │   ├── style.css     # Custom styles
    │   │   └── bootstrap.min.css # Optional Bootstrap styles
    │   └── uploads/          # Uploaded recipe images
    ├── templates/
    │   ├── base.html         # Base template for all pages
    │   ├── index.html        # Home page template
    │   ├── register.html     # Registration page template
    │   ├── login.html        # Login page template
    │   ├── profile.html      # User profile page template
    │   ├── add_recipe.html   # Add recipe page template
    │   ├── recipe_detail.html # Recipe details page template
    │   └── manage_recipes.html # Manage user recipes page template
    └── README.md             # Project README file
```
Usage

    Register/Login: Create an account or log in with an existing account.
    Add a Recipe: Use the "Add Recipe" page to share your favorite recipes with images.
    Manage Recipes: Edit or delete your recipes from the "Manage Recipes" page.
    View Others' Recipes: Explore recipes shared by other users.
    Dark Mode: Click the "Toggle Dark Mode" button to switch between light and dark themes.

Contributing

Contributions are welcome! Please follow these steps:

    Fork the repository.
    Create a new branch: git checkout -b feature-name.
    Commit your changes: git commit -m 'Add new feature'.
    Push to the branch: git push origin feature-name.
    Open a pull request.

License

This project is licensed under the MIT License - see the LICENSE file for details.
Acknowledgements

    Thanks to the Flask community for their extensive documentation and resources.
    Icons and images from Font Awesome and Unsplash.