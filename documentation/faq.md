# Frequently Asked Questions (FAQ)

Common questions and troubleshooting for the DVD Collection Tracker.

## 🚀 Getting Started

### Q: What do I need to get started?
**A:** You need:
- Python 3.8+ installed
- A TMDB API key (free from themoviedb.org)
- Internet connection for movie data
- Basic command line knowledge for setup

### Q: How do I get a TMDB API key?
**A:** 
1. Create a free account at [TMDB](https://www.themoviedb.org/)
2. Go to Settings → API
3. Click "Request an API key"
4. Choose "Developer" option
5. Fill in application details
6. Copy your API key to the `.env` file

### Q: Can I use this without an internet connection?
**A:** Partially. You can:
- View existing DVDs and their stored data
- Edit DVD information manually
- Use basic search and filtering

You cannot:
- Add new DVDs via TMDB search
- Download new posters
- Refresh movie metadata
- Access torrent links

## 📚 Using the Application

### Q: How do I add a movie that's not in TMDB?
**A:** 
1. Go to "Add New DVD"
2. Scroll down to "Can't find your movie?"
3. Click "Add Manually"
4. Fill in all details yourself
5. Note: No automatic poster or metadata will be available

### Q: What's the difference between status types?
**A:**
- **Kept**: DVDs you currently own and have access to
- **Disposed**: DVDs you once owned but sold, gave away, or lost

### Q: What media types should I use?
**A:**
- **Physical**: Actual DVD discs you own
- **Download**: Digital files you've downloaded
- **Rip**: Digital files you created from your own DVDs

### Q: How do box sets work?
**A:**
1. Check "Part of Box Set" when adding a DVD
2. Enter the collection name (e.g., "James Bond Collection")
3. Use the same name for all movies in the set
4. View all box sets at Collections → Box Sets

### Q: What are Tartan DVDs?
**A:** Tartan Asia Extreme was a UK DVD label specializing in Asian cinema. If you collect these special releases, mark them as Tartan DVDs for separate tracking.

## 🔧 Technical Issues

### Q: The movie search isn't returning results
**A:** Check:
1. **Internet connection**: TMDB requires online access
2. **API key**: Verify it's correctly entered in admin settings
3. **Movie title**: Try alternative titles or add the year
4. **TMDB availability**: The movie might not be in TMDB database

### Q: Posters aren't downloading
**A:** This can happen due to:
1. **Network issues**: Check internet connection
2. **Permission issues**: Ensure write access to media folder
3. **API limits**: Wait a moment and try again
4. **File conflicts**: Rename or delete existing poster files

### Q: The application is running slowly
**A:** Try:
1. **Use filters**: Reduce the number of displayed DVDs
2. **Clear browser cache**: Refresh cached static files
3. **Check database size**: Large collections may need optimization
4. **Restart server**: Sometimes helps with memory issues

### Q: I get "Permission Denied" errors
**A:** On Windows with PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Q: How do I backup my data?
**A:**
1. **Regular exports**: Use the CSV export feature
2. **Database backup**: Copy the `db.sqlite3` file
3. **Media backup**: Copy the `media/posters/` folder
4. **Settings backup**: Save your `.env` file

## 📊 Data Management

### Q: Can I import my existing collection?
**A:** Yes, use the bulk upload feature:
1. Navigate to "Bulk Upload"
2. Enter movie titles (one per line)
3. Set default options for status, media type, etc.
4. The system will automatically search TMDB for each title

### Q: How do I fix incorrect movie data?
**A:**
1. Go to the DVD detail page
2. Click "Fix TMDB Match"
3. Search for the correct movie
4. Select the right match to update metadata

### Q: Can I change multiple DVDs at once?
**A:** Yes, use the bulk edit feature:
1. Navigate to "Bulk Edit"
2. Filter to show the DVDs you want to change
3. Click on cells to edit them inline
4. Changes save automatically

### Q: What happens if I delete a DVD by mistake?
**A:** Unfortunately, deletions are permanent. The best protection is:
1. **Regular exports**: Download CSV backups frequently
2. **Database backups**: Copy the SQLite file regularly
3. **Caution**: Double-check before confirming deletions

## 🎬 Movie Data

### Q: Why is some movie information missing?
**A:** This depends on TMDB data quality:
- **Popular movies**: Usually have complete information
- **Obscure films**: May have limited data
- **Recent releases**: Information may be incomplete initially
- **Non-English films**: May have less detailed data

### Q: Can I edit the movie information manually?
**A:** Yes, you can edit most fields:
1. Click "Edit" on any DVD
2. Modify the information
3. Save your changes
4. Note: Refreshing TMDB data will overwrite manual changes

### Q: How often is TMDB data updated?
**A:** 
- **Manual**: Use "Fix TMDB Match" for individual movies
- **Bulk**: Use "Refresh All TMDB Data" in admin settings
- **Automatic**: No automatic updates (you control when to refresh)

### Q: What if a movie has multiple versions?
**A:** Add each version separately:
- Director's Cut
- Extended Edition
- Different releases/regions
- Use the notes or storage box field to distinguish them

## 🔍 Search and Organization

### Q: How does the search work?
**A:** The search looks through:
- Movie titles (partial matches work)
- Plot overviews/summaries
- Genres
- Box set names
- Production companies

### Q: Can I search by actor or director?
**A:** Not directly, but you can:
- Search plot summaries (actors/directors might be mentioned)
- Use external tools to find movies, then search by title
- Add actor/director info to the overview field manually

### Q: How do I organize my storage efficiently?
**A:** Suggestions:
- **Consistent naming**: "Action - Box 1", "Horror - Shelf 2"
- **Genre grouping**: Keep similar movies together
- **Size considerations**: Separate large box sets
- **Access frequency**: Keep frequently watched movies accessible

### Q: What's the best way to handle box sets?
**A:**
1. **Use descriptive names**: "Marvel Phase 1", "Criterion Collection"
2. **Be consistent**: Use exactly the same name for all movies
3. **Number if needed**: "James Bond - Part 1", "James Bond - Part 2"
4. **Track completion**: Use the box set statistics to see what's missing

## 📱 Usage and Access

### Q: Can I access this from my phone?
**A:** Yes! The interface is fully responsive and works on:
- Smartphones (iOS, Android)
- Tablets
- Desktop computers
- Any device with a web browser

### Q: Can multiple people use the same collection?
**A:** The application is designed for single-user use, but:
- Multiple people can access the same installation
- No user authentication by default
- All users share the same collection data
- For multi-user needs, consider Django's built-in user system

### Q: Can I access this from outside my home network?
**A:** For security reasons, the default setup only allows local access. For external access:
- Configure your router for port forwarding
- Set up proper security measures
- Consider using a VPN instead
- See the [Deployment Guide](deployment.md) for production setup

## 🛠️ Customization

### Q: Can I change the look and feel?
**A:** Yes, you can customize:
- **CSS**: Modify `static/css/style.css`
- **Templates**: Edit HTML files in `templates/`
- **Bootstrap theme**: Replace the Bootstrap CSS
- **Logo/branding**: Update images and text

### Q: Can I add custom fields?
**A:** This requires Django knowledge:
1. Modify the `DVD` model in `models.py`
2. Create and run migrations
3. Update forms and templates
4. See the [Development Guide](development.md) for details

### Q: Can I integrate with other services?
**A:** The application is designed to be extensible:
- Add new API services to `services.py`
- Create new views and URLs
- Extend the existing models
- Follow Django best practices for extensions

## 🚨 Troubleshooting

### Q: The server won't start
**A:** Check:
1. **Virtual environment**: Is it activated?
2. **Dependencies**: Run `pip install -r requirements.txt`
3. **Database**: Run `python manage.py migrate`
4. **Port conflicts**: Try a different port with `python manage.py runserver 8001`

### Q: I see a "500 Internal Server Error"
**A:**
1. Check the console output for error details
2. Ensure `DEBUG=True` in your `.env` file (development only)
3. Verify database permissions
4. Check that all migrations are applied

### Q: Movies aren't saving properly
**A:**
1. **Database permissions**: Ensure write access to `db.sqlite3`
2. **Form validation**: Check for required field errors
3. **API connectivity**: Verify TMDB API access
4. **Disk space**: Ensure sufficient space for database growth

### Q: Bulk operations are failing
**A:**
1. **API rate limits**: Wait between operations
2. **Large datasets**: Process smaller batches
3. **Network timeouts**: Check internet connectivity
4. **Memory issues**: Restart the server between large operations

## 💡 Best Practices

### Q: What's the best way to organize a large collection?
**A:**
1. **Use consistent naming**: Establish patterns for storage boxes
2. **Leverage filters**: Use search and filtering instead of browsing
3. **Regular maintenance**: Update disposed items promptly
4. **Backup frequently**: Export data regularly
5. **Use box sets**: Group related movies for easier management

### Q: How should I handle different editions?
**A:**
- **Same movie, different formats**: Use media type field
- **Director's cuts, etc.**: Add as separate entries
- **Region variants**: Note in storage box or manually in overview
- **Chronological releases**: Use release year to distinguish

### Q: What's the workflow for disposed items?
**A:**
1. **Before disposal**: Change status to "Disposed"
2. **Clear storage box**: Remove physical location
3. **Keep records**: Maintain for collection history
4. **Export lists**: Generate "wanted" lists for re-acquisition

---

*Still have questions? Check the [User Manual](user-manual.md) for detailed instructions or the [Development Guide](development.md) for technical information.*