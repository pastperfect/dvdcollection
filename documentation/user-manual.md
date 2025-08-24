# User Manual

Complete guide to using the DVD Collection Tracker application effectively.

## 🎬 Overview

The DVD Collection Tracker helps you catalog, organize, and manage your personal movie collection. Whether you collect physical DVDs, digital downloads, or ripped files, this application provides comprehensive tracking with rich metadata integration.

## 🏠 Homepage Dashboard

The homepage provides an at-a-glance view of your collection:

### Statistics Overview
- **Total DVDs**: Complete count of your collection
- **Kept vs Disposed**: Status distribution
- **Recent Additions**: Last 6 movies added
- **Special Collections**: Tartan DVDs, box sets, unwatched items

### Quick Actions
- **Add New DVD**: Start adding movies to your collection
- **Browse Collection**: View all DVDs with filtering
- **Statistics**: Detailed collection analytics
- **Admin Settings**: Configure the application

## 📽️ Managing Your DVD Collection

### Adding DVDs

#### Method 1: TMDB Search (Recommended)

1. **Navigate to Add DVD**:
   - Click "Add New DVD" from homepage or navigation
   - Use the search form to find movies

2. **Search for Movies**:
   ```
   Search Query: "The Matrix"
   ```
   - Enter movie title, partial titles work
   - Click "Search Movies"
   - Browse results with posters and descriptions

3. **Select and Customize**:
   - Click "Add This Movie" on your chosen result
   - Review auto-populated information
   - Customize the following fields:

#### DVD Details Form

| Field | Description | Options |
|-------|-------------|---------|
| **Name** | Movie title | Auto-filled from TMDB |
| **Status** | Current ownership | Kept, Disposed |
| **Media Type** | Format type | Physical, Download, Rip |
| **Storage Box** | Physical location | Free text (autocompletes) |
| **Tartan DVD** | Special release flag | Checkbox |
| **Box Set** | Part of collection | Checkbox |
| **Box Set Name** | Collection name | Text (if box set checked) |
| **Unopened** | Still sealed | Checkbox |
| **Unwatched** | Not yet viewed | Checkbox |

#### Method 2: Manual Entry

For movies not in TMDB or personal recordings:

1. Scroll to "Can't find your movie?"
2. Click "Add Manually"
3. Fill in all details manually
4. No automatic poster/metadata will be available

### Viewing DVDs

#### DVD List View

Access via "Browse DVDs" to see your complete collection:

- **Grid Layout**: Cards showing posters and key information
- **Pagination**: 12 DVDs per page
- **Sort Options**: By date added (newest first)

#### DVD Detail View

Click any DVD card to see comprehensive information:

- **Movie Poster**: High-resolution image from TMDB
- **Plot Overview**: Movie synopsis
- **Technical Details**: Runtime, rating, genres
- **Collection Info**: Status, media type, storage location
- **TMDB Data**: Release year, certification, user scores
- **Torrent Links**: YTS integration for available downloads

#### DVD Cards Information

Each DVD card displays:
- **Poster Image**: Movie artwork
- **Title & Year**: Movie identification
- **Status Badge**: 
  - 🟢 Kept (success)
  - 🔴 Disposed (danger)
- **Media Type Badge**:
  - 🔵 Physical (primary)
  - 🔵 Download (info)
  - 🟡 Rip (warning)
- **Special Badges**:
  - 🟣 Tartan (purple)
  - 🔵 Box Set (info)
  - 🟢 Unopened (success)
  - 🟡 Unwatched (warning)

### Editing DVDs

1. **Access Edit Mode**:
   - Click pencil icon on DVD card
   - Or click "Edit" in detail view

2. **Modify Fields**:
   - Update any editable field
   - Changes save to database immediately

3. **TMDB Data Refresh**:
   - Use "Fix TMDB Match" for incorrect movie data
   - Search for correct movie and update metadata

### Deleting DVDs

1. **Individual Deletion**:
   - Click trash icon on DVD card
   - Confirm deletion in popup dialog
   - Action is irreversible

2. **Bulk Deletion**:
   - Use bulk edit interface
   - Select multiple DVDs
   - Delete in batch operation

## 🔍 Search and Filtering

### Search Functionality

The search bar accepts:
- **Movie titles**: Full or partial names
- **Plot keywords**: Search in overviews
- **Genres**: Find by genre type
- **Box set names**: Locate collection members

### Filter Options

| Filter | Values | Description |
|--------|--------|-------------|
| **Status** | All, Kept, Disposed | Ownership status |
| **Media Type** | All, Physical, Download, Rip | Format type |
| **Tartan DVD** | All, Yes, No | Special releases |
| **Box Set** | All, Yes, No | Collection membership |
| **Unopened** | All, Yes, No | Sealed status |
| **Unwatched** | All, Yes, No | Viewing status |
| **Production Company** | Text search | Studio/distributor |

### Advanced Search

Combine multiple filters for precise results:
```
Search: "action"
Status: Kept
Media Type: Physical
Tartan DVD: Yes
```

## 📦 Special Collections

### Box Sets

Organize related movies into collections:

1. **Creating Box Sets**:
   - Check "Part of Box Set" when adding DVD
   - Enter descriptive name (e.g., "James Bond Collection")
   - Names autocomplete from existing sets

2. **Viewing Box Sets**:
   - Navigate to "Collections" → "Box Sets"
   - See collection cards with movie counts
   - Click to view all movies in set

3. **Box Set Management**:
   - Add movies to existing sets using autocomplete
   - Rename sets by editing individual movies
   - Remove movies by unchecking box set flag

### Tartan DVDs

Special tracking for Tartan Asia Extreme releases:

1. **Marking Tartan DVDs**:
   - Check "Tartan DVD" when adding
   - Purple badge appears on cards

2. **Viewing Collection**:
   - Navigate to "Collections" → "Tartan DVDs"
   - Filtered view of special releases
   - Count appears in statistics

### Storage Management

Track physical locations:

1. **Storage Boxes**:
   - Free text field with autocomplete
   - Use consistent naming (e.g., "Horror - Box 1")
   - Only relevant for "Kept" status DVDs

2. **Location Tracking**:
   - Search by storage box in filters
   - Bulk edit for moving collections
   - Leave empty for disposed items

## 📊 Statistics and Analytics

### Collection Overview

Access via "Statistics" menu:

| Metric | Description |
|--------|-------------|
| **Total DVDs** | Complete collection count |
| **Status Breakdown** | Kept vs Disposed distribution |
| **Media Types** | Physical vs Digital split |
| **Special Collections** | Tartan, Box Sets, Unopened counts |

### Rating Analysis

- **Average Rating**: TMDB user scores
- **Rating Distribution**: Score ranges
- **Top Rated**: Highest scoring movies
- **Unrated**: Missing rating information

### Runtime Statistics

- **Total Runtime**: Combined movie lengths
- **Average Runtime**: Mean movie duration
- **Longest/Shortest**: Extreme values
- **Runtime Distribution**: Length categories

### Genre Analysis

- **Top Genres**: Most common in collection
- **Genre Distribution**: Percentage breakdown
- **Genre Trends**: Popular vs niche categories

### Timeline Analysis

- **Decade Breakdown**: Movies by release decade
- **Year Range**: Earliest to latest releases
- **Recent Releases**: Modern vs classic ratio

### Production Companies

- **Top Studios**: Most collected distributors
- **Company Distribution**: Studio market share
- **Independent vs Major**: Studio type analysis

## 🔧 Bulk Operations

### Bulk Upload

Add multiple movies from a text list:

1. **Navigate to Bulk Upload**:
   - Click "Bulk Upload" in navigation
   - Prepare your movie list

2. **Format Movie List**:
   ```
   The Matrix
   Blade Runner
   Inception
   The Dark Knight
   ```
   - One movie per line
   - Use recognizable titles

3. **Set Default Options**:
   - **Status**: Kept/Disposed for all
   - **Media Type**: Physical/Download/Rip for all
   - **Box Set**: Apply to all if part of collection
   - **Storage Box**: Default location for kept items

4. **Upload Process**:
   - Click "Upload Movies"
   - System searches TMDB for each title
   - Results show added/skipped/failed counts

### Bulk Edit

Edit multiple DVDs in table format:

1. **Access Bulk Edit**:
   - Navigate to "Bulk Edit"
   - Filter DVDs to show desired subset

2. **Table Interface**:
   - Each row represents one DVD
   - Click cells to edit inline
   - Changes save automatically

3. **Editable Fields**:
   - Status (dropdown)
   - Media Type (dropdown) 
   - Box Set flag (checkbox)
   - Box Set Name (text)
   - Storage Box (text)
   - Tartan DVD flag (checkbox)

4. **Quick Actions**:
   - Delete individual DVDs
   - Apply filters to reduce scope
   - Navigate with pagination

### Export Data

Download your collection as CSV:

1. **Export Non-Kept DVDs**:
   - Navigate to "Export" in admin menu
   - Downloads movies not in "Kept" status
   - Includes torrent links if available

2. **CSV Format**:
   ```csv
   Movie Name,Release Year,Status,Media Type,720p Download Link,1080p Download Link
   ```

3. **Use Cases**:
   - Backup your collection data
   - Share lists with friends
   - Import into other systems
   - Track movies to acquire

## 🛠️ Admin Features

### Settings Management

Access via "Admin Settings":

1. **TMDB API Configuration**:
   - Update API key
   - Test connectivity
   - View usage statistics

2. **System Information**:
   - Application version
   - Database statistics
   - Recent activity logs

### Data Maintenance

#### TMDB Data Refresh

Update all movie metadata:

1. **Bulk Refresh**:
   - Click "Refresh All TMDB Data"
   - Background process updates all movies
   - Progress tracking with live updates

2. **Individual Refresh**:
   - Use "Fix TMDB Match" on specific DVDs
   - Search for correct movie data
   - Update metadata selectively

#### Database Cleanup

- **Remove Orphaned Files**: Clean unused poster images
- **Optimize Database**: Rebuild indexes and statistics
- **Backup Data**: Export for external storage

## 🚨 Troubleshooting

### Common Issues

#### Search Not Working
- **Check Internet**: TMDB requires connectivity
- **Verify API Key**: Ensure valid key in settings
- **Try Alternatives**: Use different movie titles

#### Missing Posters
- **Automatic Download**: May take time to process
- **Refresh Data**: Use TMDB refresh feature
- **Manual Update**: Change poster via detail view

#### Slow Performance
- **Large Collections**: Use filters to reduce load
- **Database Issues**: Contact administrator
- **Network Problems**: Check connectivity

#### Data Loss Prevention
- **Regular Exports**: Download CSV backups
- **Database Backups**: Administrative backups
- **Version Control**: Track configuration changes

### Error Messages

| Error | Cause | Solution |
|-------|-------|---------|
| "API Key Invalid" | Wrong TMDB key | Update in admin settings |
| "Movie Not Found" | Title not in TMDB | Try manual entry |
| "Connection Error" | Network issues | Check internet connection |
| "Storage Full" | Disk space low | Clean media files |

## 📱 Mobile Usage

### Responsive Design

The application works on all devices:

- **Phone**: Vertical card layout, simplified navigation
- **Tablet**: Grid layout with touch-friendly controls
- **Desktop**: Full feature access with keyboard shortcuts

### Touch Interface

- **Swipe Navigation**: Move between pages
- **Tap Actions**: Single tap for selection
- **Long Press**: Context menus on cards
- **Pinch Zoom**: Scale poster images

### Mobile-Specific Features

- **Quick Add**: Simplified form for mobile entry
- **Voice Search**: Browser voice input support
- **Photo Capture**: Take pictures of physical DVDs
- **Offline Mode**: Basic viewing without internet

---

*Complete user manual for DVD Collection Tracker. For technical details, see the [API Reference](api-reference.md) and [Development Guide](development.md).*