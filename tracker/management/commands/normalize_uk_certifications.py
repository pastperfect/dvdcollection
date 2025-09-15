from django.core.management.base import BaseCommand
from django.db import models
from tracker.models import DVD


class Command(BaseCommand):
    help = 'Normalize UK certification data to lowercase for existing DVDs in the collection'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each DVD processed'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        # Find DVDs with UK certification data that needs normalization
        dvds_with_certifications = DVD.objects.filter(
            models.Q(uk_certification__isnull=False) & 
            ~models.Q(uk_certification='')
        )
        
        # Find those that need updating (have uppercase characters)
        dvds_to_update = []
        for dvd in dvds_with_certifications:
            original = dvd.uk_certification
            normalized = original.lower() if original else ''
            if original != normalized:
                dvds_to_update.append((dvd, original, normalized))
        
        total_count = len(dvds_to_update)
        total_with_certs = dvds_with_certifications.count()
        
        # Display summary
        self.stdout.write(
            f"Found {total_with_certs} DVDs with UK certification data"
        )
        self.stdout.write(
            f"Found {total_count} DVDs that need certification normalization"
        )
        
        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS("✅ All UK certifications are already normalized!")
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN MODE - No changes will be made")
            )
        
        self.stdout.write(f"\n📋 DVDs to be updated:")
        
        updated_count = 0
        error_count = 0
        
        for i, (dvd, original, normalized) in enumerate(dvds_to_update, 1):
            try:
                if verbose or dry_run:
                    self.stdout.write(
                        f"[{i}/{total_count}] {dvd.name} ({dvd.release_year or 'N/A'})"
                    )
                    self.stdout.write(f"  Certification: '{original}' → '{normalized}'")
                
                if not dry_run:
                    # Update the certification
                    dvd.uk_certification = normalized
                    dvd.save(update_fields=['uk_certification'])
                    updated_count += 1
                    
                    if verbose:
                        self.stdout.write(f"  ✅ Updated")
                else:
                    if verbose:
                        self.stdout.write(f"  📝 Would update")
                        
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Error updating {dvd.name}: {str(e)}")
                )
        
        # Final summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n🔍 DRY RUN COMPLETE: Would update {total_count} DVDs"
                )
            )
            self.stdout.write(
                "Run without --dry-run to apply these changes."
            )
        else:
            if error_count == 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n✅ Successfully updated {updated_count} DVDs!"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠️  Updated {updated_count} DVDs with {error_count} errors"
                    )
                )
        
        # Show certification distribution
        self.show_certification_stats()
    
    def show_certification_stats(self):
        """Display current certification distribution."""
        self.stdout.write(f"\n📊 Current UK Certification Distribution:")
        
        # Get certification counts
        cert_counts = DVD.objects.filter(
            models.Q(uk_certification__isnull=False) & 
            ~models.Q(uk_certification='')
        ).values('uk_certification').annotate(
            count=models.Count('uk_certification')
        ).order_by('uk_certification')
        
        if cert_counts:
            for cert in cert_counts:
                self.stdout.write(f"  {cert['uk_certification']}: {cert['count']} DVDs")
        else:
            self.stdout.write("  No certification data found")
        
        # Show total without certifications
        no_cert_count = DVD.objects.filter(
            models.Q(uk_certification__isnull=True) | 
            models.Q(uk_certification='')
        ).count()
        
        if no_cert_count > 0:
            self.stdout.write(f"  (no certification): {no_cert_count} DVDs")