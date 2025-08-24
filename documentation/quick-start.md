# Quick Start Guide

Get your DVD Collection Tracker up and running in just a few minutes! This guide assumes you've already completed the [Installation](installation.md).

## 🚀 First Steps

### 1. Start the Application

```powershell
# Navigate to project directory
cd C:\Projects\dvdcollection

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start the development server
python manage.py runserver
```

### 2. Access the Web Interface

Open your browser and navigate to:
```
http://127.0.0.1:8000
```

You should see the DVD Collection Tracker homepage with:
- Collection statistics dashboard
- Quick navigation menu
- Recent additions section

## 📚 Adding Your First DVD

### Method 1: Search and Add from TMDB

1. **Click "Add New DVD"** from the homepage or navigation menu

2. **Search for a Movie**:
   - Enter a movie title (e.g., "The Matrix")
   - Click "Search Movies"
   - Browse the search results with posters and descriptions

3. **Select Your Movie**:
   - Click "Add This Movie" on your desired result
   - Review the auto-filled information

4. **Customize Details**:
   - **Status**: Choose "Kept" or "Disposed"
   - **Media Type**: Select "Physical", "Download", or "Rip"
   - **Storage Box**: Enter where you store this DVD (for kept items)
   - **Special Properties**:
     - ✅ Tartan DVD (if it's a Tartan release)
     - ✅ Box Set (if part of a collection)
     - ✅ Unopened (if still sealed)
     - ✅ Unwatched (if you haven't seen it yet)

5. **Save**: Click "Add DVD" to save to your collection

### Method 2: Manual Entry

1. Click "Add New DVD"
2. Scroll down to "Can't find your movie?"
3. Click "Add Manually"
4. Fill in the movie details yourself
5. Save your entry

## 🔍 Exploring Your Collection

### Viewing Your DVDs

- **Homepage Dashboard**: See recent additions and quick stats
- **Browse Collection**: Click "Browse DVDs" to see all movies
- **Filter & Search**: Use the search bar and filters to find specific movies

### Understanding the Interface

Each DVD card shows:
- **Movie Poster**: Auto-downloaded from TMDB
- **Title & Year**: Movie name and release year
- **Status Badge**: Kept (green) or Disposed (red)
- **Media Type Badge**: Physical, Download, or Rip
- **Special Badges**: Tartan, Box Set, Unopened, Unwatched
- **Action Buttons**: View details, Edit, Delete

## 📊 Collection Statistics

Click "Statistics" to see:
- **Collection Overview**: Total DVDs, kept vs disposed
- **Media Breakdown**: Physical vs digital distribution
- **Special Collections**: Tartan DVDs, box sets, unopened items
- **Genre Analysis**: Most common genres in your collection
- **Timeline**: Movies by decade
- **Top Production Companies**: Studios you collect most

## 🎬 Special Features

### Box Sets

Organize related movies together:
1. When adding a DVD, check "Part of Box Set"
2. Enter the box set name (autocomplete will suggest existing sets)
3. View all box sets at "Collections" → "Box Sets"

### Tartan DVDs

Mark special Tartan DVD releases:
1. Check "Tartan DVD" when adding/editing
2. View all Tartan DVDs at "Collections" → "Tartan DVDs"

### Bulk Operations

For large collections:
- **Bulk Upload**: Add multiple movies from a text list
- **Bulk Edit**: Edit multiple DVDs in a table format
- **Export**: Download your collection as CSV

## 🛠️ Quick Configuration

### Admin Settings

Access admin settings to:
- Update your TMDB API key
- Configure application preferences
- View system information

### TMDB Integration

The app automatically:
- Fetches movie posters
- Downloads plot summaries
- Gets release years, genres, ratings
- Retrieves runtime and certification info

## 📱 Mobile-Friendly Design

The interface is fully responsive:
- **Phone**: Stack cards vertically, simplified navigation
- **Tablet**: Grid layout with touch-friendly buttons
- **Desktop**: Full feature access with keyboard shortcuts

## 🔄 Workflow Examples

### Example 1: Adding a Physical DVD

1. Search for "Blade Runner"
2. Select the 1982 version
3. Set Status: "Kept"
4. Set Media Type: "Physical"
5. Enter Storage Box: "Action Movies - Box 1"
6. Save

### Example 2: Recording a Digital Download

1. Search for "Inception"
2. Select the movie
3. Set Status: "Kept"
4. Set Media Type: "Download"
5. Check "Unwatched" if you haven't seen it
6. Save

### Example 3: Tracking Disposed DVDs

1. Find an existing DVD in your collection
2. Click "Edit"
3. Change Status to "Disposed"
4. Clear the Storage Box field
5. Save

## 🎯 Pro Tips

### Efficient Adding
- Use the search autocomplete for faster movie entry
- Storage box names autocomplete from previous entries
- Box set names also autocomplete

### Organization
- Use consistent naming for storage boxes (e.g., "Action - Box 1")
- Group similar genres together
- Mark unwatched movies to track your viewing queue

### Maintenance
- Regularly update disposed DVDs
- Use bulk edit for changing multiple storage locations
- Export your data periodically for backup

## 🆘 Quick Troubleshooting

### No Search Results
- Check your internet connection
- Verify TMDB API key in admin settings
- Try alternative movie titles or years

### Missing Posters
- Posters download automatically but may take time
- Check your media folder permissions
- Refresh TMDB data if posters are missing

### Slow Performance
- Large collections may load slowly
- Use filters to reduce displayed items
- Consider pagination on large result sets

## 📚 What's Next?

Now that you're up and running:

1. **Add More DVDs**: Build your collection database
2. **Explore Features**: Try bulk operations, statistics, exports
3. **Customize Setup**: Adjust settings for your workflow
4. **Read Documentation**: Check the [User Manual](user-manual.md) for advanced features

---

*You're all set! Start building your digital DVD collection inventory.*