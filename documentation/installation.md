# Installation Guide

This guide will walk you through setting up the DVD Collection Tracker on your local machine or server.

## 📋 Prerequisites

Before installing, ensure you have the following:

### System Requirements
- **Python 3.8+** (Python 3.12 recommended)
- **Git** for cloning the repository
- **PowerShell** (for Windows users)
- **Internet connection** for API calls and dependencies

### External Service Requirements
- **TMDB API Key** - Free registration at [The Movie Database](https://www.themoviedb.org/)
- **Optional**: YTS API access for torrent information

## 🛠️ Installation Steps

### 1. Clone the Repository

```powershell
# Navigate to your projects directory
cd C:\Projects

# Clone the repository
git clone <repository-url> dvdcollection
cd dvdcollection
```

### 2. Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# For Command Prompt users:
# venv\Scripts\activate.bat

# For Linux/macOS users:
# source venv/bin/activate
```

### 3. Install Dependencies

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install required packages
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```powershell
# Copy the example file
copy .env.example .env

# Edit the .env file with your settings
notepad .env
```

Required environment variables:
```env
# Django Settings
SECRET_KEY=your_super_secret_key_here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# TMDB API Configuration
TMDB_API_KEY=your_tmdb_api_key_here

# Database (SQLite is default for development)
DATABASE_URL=sqlite:///db.sqlite3

# Optional: YTS API Settings
YTS_API_BASE_URL=https://yts.mx/api/v2
```

### 5. Database Setup

```powershell
# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Optional: Create a superuser for admin access
python manage.py createsuperuser

# Optional: Load sample data
python manage.py load_sample_data
```

### 6. Static Files Collection

```powershell
# Collect static files
python manage.py collectstatic --noinput
```

### 7. Start Development Server

```powershell
# Run the development server
python manage.py runserver

# Access the application at:
# http://127.0.0.1:8000
```

## 🔑 TMDB API Key Setup

### Getting Your API Key

1. **Create Account**: Visit [TMDB](https://www.themoviedb.org/) and create a free account
2. **Request API Key**: Go to Settings → API → Request an API key
3. **Choose Type**: Select "Developer" for personal use
4. **Application Details**: Fill in your application information
5. **Copy Key**: Once approved, copy your API key

### Adding to Environment

Add your TMDB API key to the `.env` file:
```env
TMDB_API_KEY=your_actual_api_key_here
```

## 📁 Project Structure

After installation, your project structure should look like:

```
dvdcollection/
├── documentation/          # Documentation files
├── dvd_tracker/           # Main Django project
│   ├── settings.py        # Django settings
│   ├── urls.py           # URL configuration
│   └── wsgi.py           # WSGI configuration
├── tracker/              # Main application
│   ├── models.py         # Database models
│   ├── views.py          # View functions
│   ├── forms.py          # Django forms
│   └── services.py       # External API services
├── static/               # Static files (CSS, JS)
├── media/                # User uploads (posters)
├── templates/            # HTML templates
├── requirements.txt      # Python dependencies
├── manage.py            # Django management script
├── .env                 # Environment variables (create this)
└── db.sqlite3           # SQLite database (created after migration)
```

## 🧪 Verify Installation

Test your installation with these verification steps:

### 1. Check Server Start
```powershell
python manage.py runserver
```
Visit `http://127.0.0.1:8000` - you should see the homepage.

### 2. Test TMDB Integration
1. Navigate to "Add DVD"
2. Search for a movie (e.g., "The Matrix")
3. Verify that search results appear with posters

### 3. Test Database Operations
1. Add a DVD to your collection
2. View the DVD list
3. Edit or delete a DVD

## 🚨 Troubleshooting

### Common Issues

#### ModuleNotFoundError
```powershell
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

#### TMDB API Errors
- Verify your API key is correct in `.env`
- Check that you have internet connectivity
- Ensure you haven't exceeded rate limits

#### Database Errors
```powershell
# Reset database if needed
rm db.sqlite3
python manage.py migrate
```

#### Static Files Not Loading
```powershell
# Collect static files
python manage.py collectstatic --noinput
```

### Permission Issues (Windows)

If you encounter PowerShell execution policy issues:
```powershell
# Check current policy
Get-ExecutionPolicy

# Set policy for current user (if needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 🔧 Development vs Production

This guide covers **development installation**. For production deployment:

- Use PostgreSQL instead of SQLite
- Set `DEBUG=False`
- Configure proper static file serving
- Set up SSL/TLS certificates
- Use a production WSGI server (gunicorn/uWSGI)

See the [Deployment Guide](deployment.md) for production setup instructions.

## ✅ Next Steps

After successful installation:

1. Read the [Quick Start Guide](quick-start.md)
2. Explore the [User Manual](user-manual.md)
3. Check out the [Features Overview](features.md)

---

*Installation complete! You're ready to start tracking your DVD collection.*