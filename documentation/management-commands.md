# Management Commands

Administrative commands for maintaining and managing the DVD Collection Tracker.

## Overview

The DVD Collection Tracker includes several Django management commands for administrative tasks. These commands can be run from the command line to perform bulk operations, data maintenance, and system administration tasks.

## Available Commands

### refresh_missing_details

Refresh TMDB data for DVDs missing detailed information like taglines, budget, revenue, production companies, director, and UK certification.

#### Usage

```bash
python manage.py refresh_missing_details [options]
```

#### Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Show what would be updated without making changes |
| `--verbose` | Show detailed output for each DVD processed |
| `--limit LIMIT` | Limit the number of DVDs to process (default: process all) |
| `--force` | Force refresh all DVDs with TMDB IDs, even if they have detailed data |

#### Examples

```bash
# Basic refresh - updates DVDs missing detailed information
python manage.py refresh_missing_details

# See what would be updated without making changes
python manage.py refresh_missing_details --dry-run

# Process only 50 DVDs with detailed output
python manage.py refresh_missing_details --limit 50 --verbose

# Force refresh all DVDs with TMDB IDs (even those with complete data)
python manage.py refresh_missing_details --force

# Dry run with verbose output to see exactly what would change
python manage.py refresh_missing_details --dry-run --verbose --limit 10
```

#### What Gets Updated

The command refreshes the following fields from TMDB:
- **Tagline**: Movie taglines and slogans
- **Budget**: Production budget information
- **Revenue**: Box office revenue data
- **Production Companies**: Studio and production company names
- **Director**: Director information from credits
- **UK Certification**: Age rating/certification for UK releases
- **Rating/User Score**: Updated TMDB ratings

#### Output

The command provides comprehensive feedback including:
- Number of DVDs processed, updated, skipped, and failed
- Current statistics for each detailed field
- Verbose mode shows field-by-field changes for each DVD

### normalize_uk_certifications

Normalize UK certification data to lowercase for existing DVDs in the collection.

#### Usage

```bash
python manage.py normalize_uk_certifications [options]
```

#### Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Show what would be updated without making changes |
| `--verbose` | Show detailed output for each DVD processed |

#### Examples

```bash
# Normalize all UK certifications to lowercase
python manage.py normalize_uk_certifications

# See what would be changed
python manage.py normalize_uk_certifications --dry-run --verbose
```

### refresh_torrent_data

Refresh YTS torrent availability data for DVDs with IMDB IDs.

#### Usage

```bash
python manage.py refresh_torrent_data [options]
```

### populate_imdb_ids

Populate missing IMDB IDs from TMDB data.

#### Usage

```bash
python manage.py populate_imdb_ids [options]
```

### cleanup_unused_posters

Clean up unused poster image files from the media directory.

#### Usage

```bash
python manage.py cleanup_unused_posters [options]
```

### load_sample_data

Load sample DVD data for testing and development.

#### Usage

```bash
python manage.py load_sample_data [options]
```

## Best Practices

### Running Commands Safely

1. **Always use --dry-run first**: Before making bulk changes, use `--dry-run` to see what would be affected
2. **Start with small limits**: Use `--limit` to test on a small subset before processing your entire collection
3. **Use verbose output**: Enable `--verbose` to understand exactly what changes are being made
4. **Backup your data**: Always backup your database before running bulk operations

### Performance Considerations

- **API Rate Limits**: TMDB commands are subject to API rate limits. Large collections may take time to process
- **Network Dependency**: Commands that fetch data from TMDB require a stable internet connection
- **Database Locking**: Some operations may temporarily lock database tables during updates

### Monitoring Progress

For commands that process many DVDs:
- Use `--verbose` to see real-time progress
- Monitor log files for errors or warnings
- Check the final statistics to verify successful completion

## Common Workflows

### Initial Collection Setup

After importing a large collection:

```bash
# 1. Populate missing IMDB IDs
python manage.py populate_imdb_ids --dry-run --verbose
python manage.py populate_imdb_ids

# 2. Refresh detailed information
python manage.py refresh_missing_details --dry-run --limit 10
python manage.py refresh_missing_details

# 3. Normalize certifications
python manage.py normalize_uk_certifications --dry-run
python manage.py normalize_uk_certifications

# 4. Update torrent availability
python manage.py refresh_torrent_data
```

### Regular Maintenance

Monthly maintenance routine:

```bash
# Check for DVDs needing data refresh
python manage.py refresh_missing_details --dry-run

# Clean up unused files
python manage.py cleanup_unused_posters

# Update torrent availability for newly added DVDs
python manage.py refresh_torrent_data --recent-only
```

### Troubleshooting Issues

If you encounter problems:

```bash
# Check what needs updating with dry run
python manage.py refresh_missing_details --dry-run --verbose --limit 5

# Process a small batch to isolate issues
python manage.py refresh_missing_details --limit 10 --verbose

# Force refresh specific problematic DVDs
python manage.py refresh_missing_details --force --limit 1 --verbose
```

## Error Handling

All management commands include comprehensive error handling:

- **Network Errors**: Commands will skip failed API calls and report them
- **Database Errors**: Individual record failures won't stop the entire operation
- **Validation Errors**: Invalid data is logged and skipped
- **Permission Errors**: File system issues are reported with clear messages

## Getting Help

For detailed help on any command:

```bash
python manage.py <command_name> --help
```

This will show all available options and usage examples for the specific command.