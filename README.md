# DVD Collection Tracker

A modern Django web application for tracking your personal DVD collection with automatic metadata fetching from The Movie Database (TMDB).

## Features

- **TMDB Integration**: Automatically fetch movie posters, overviews, and metadata
- **Search & Filter**: Find movies in your collection by title, status, or media type
- **Responsive Design**: Modern Bootstrap-based interface that works on all devices
- **Data Management**: Add, edit, and delete DVDs with comprehensive movie information
- **Status Tracking**: Track whether DVDs are "Kept" or "Disposed"
- **Media Types**: Categorize as "Physical", "Download", or "Rip"
- **Rich Metadata**: Store release year, genres, runtime, and ratings
- **Single-User**: No authentication required - perfect for personal use

## Setup Instructions

1. **Clone and navigate to the project:**
   
   ```bash
   cd Movie_Tracker
   ```

2. **Create and activate a virtual environment:**
   
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # source venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies:**
   
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - Copy `.env.example` to `.env`
   - Add your TMDB API key to the `.env` file:
     
     ```env
     TMDB_API_KEY=your_api_key_here
     SECRET_KEY=your_django_secret_key_here
     DEBUG=True
     ```
   - Get your TMDB API key from: <https://www.themoviedb.org/settings/api>

5. **Run migrations:**
   
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Load sample data (optional):**
   
   ```bash
   python manage.py load_sample_data
   ```

7. **Start the development server:**
   
   ```bash
   python manage.py runserver
   ```

8. **Access the application:**
   Open your browser to `http://127.0.0.1:8000`

## Project Structure

```
Movie_Tracker/
├── dvd_tracker/          # Main Django project
├── tracker/              # DVD tracking app
├── static/               # Static files (CSS, JS)
├── media/                # Uploaded files (movie posters)
├── templates/            # HTML templates
├── requirements.txt      # Python dependencies
├── manage.py            # Django management script
└── README.md            # This file
```

## Usage

1. **Add a DVD:** Click "Add New DVD" and search for a movie title
2. **Edit a DVD:** Click the edit button on any DVD card
3. **Delete a DVD:** Click the delete button and confirm
4. **Filter:** Use the search bar and filter dropdowns to find specific DVDs

## TMDB API

This application uses The Movie Database (TMDB) API to fetch movie information. You'll need to:

1. Create an account at https://www.themoviedb.org/
2. Request an API key from https://www.themoviedb.org/settings/api
3. Add the API key to your `.env` file

## Deployment

This application is ready for deployment to cloud platforms like Azure App Service. Make sure to:

1. Set environment variables in your hosting platform
2. Configure static file serving
3. Set `DEBUG=False` in production
4. Use a production database (PostgreSQL recommended)
