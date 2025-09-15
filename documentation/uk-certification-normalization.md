# UK Certification Normalization Management Command

## Overview

The `normalize_uk_certifications` management command standardizes UK film certification data in your DVD collection by converting all certification values to lowercase. This ensures data consistency, improves filtering accuracy, and provides better database optimization.

## Command Usage

```bash
# Preview what will be updated (recommended first step)
python manage.py normalize_uk_certifications --dry-run

# Show detailed output during preview
python manage.py normalize_uk_certifications --dry-run --verbose

# Perform the actual normalization
python manage.py normalize_uk_certifications

# Perform normalization with detailed output
python manage.py normalize_uk_certifications --verbose
```

## Command Options

- `--dry-run`: Show what would be updated without making any actual changes
- `--verbose`: Display detailed output for each DVD processed

## Examples of Normalization

The command converts uppercase and mixed-case UK certifications to lowercase:

- `PG` → `pg`
- `12A` → `12a`
- `U` → `u`
- `15` → `15` (already lowercase/numeric)
- `18` → `18` (already lowercase/numeric)

## Features

### Statistics Display
- Shows total count of DVDs with certification data
- Identifies how many DVDs need normalization
- Displays current certification distribution after completion

### Safety Features
- **Dry run mode**: Always preview changes before applying them
- **Targeted updates**: Only processes DVDs that actually need normalization
- **Error handling**: Continues processing if individual DVDs fail
- **Detailed logging**: Shows exactly what changes will be/were made

### Model Integration
- The DVD model's `save()` method automatically normalizes certifications for new/updated records
- This command handles existing data that was created before the normalization feature

## Web Interface

The command is also available through the Admin Settings page in the web interface:

1. Navigate to Admin Settings
2. Find the "UK Certification Management" section  
3. Click "Normalize" button to run the operation
4. View real-time statistics about your certification data

## Example Output

```
Found 280 DVDs with UK certification data
Found 40 DVDs that need certification normalization

📋 DVDs to be updated:
[1/40] Movie A (2023)
  Certification: 'PG' → 'pg'
  ✅ Updated

✅ Successfully updated 40 DVDs!

📊 Current UK Certification Distribution:
  12: 20 DVDs
  12a: 24 DVDs
  15: 109 DVDs
  18: 93 DVDs
  pg: 31 DVDs
  u: 2 DVDs
  (no certification): 233 DVDs
```

## When to Use

- After importing bulk data that may have inconsistent certification formats
- When migrating from external sources with mixed-case certifications
- As part of regular data maintenance to ensure consistency
- Before implementing new filtering or search features that rely on certification data

## Technical Details

- **File Location**: `tracker/management/commands/normalize_uk_certifications.py`
- **Model Field**: `DVD.uk_certification` (CharField, max_length=10, blank=True)
- **Database Impact**: Updates only the `uk_certification` field for affected records
- **Performance**: Processes records efficiently with targeted queries and bulk operations