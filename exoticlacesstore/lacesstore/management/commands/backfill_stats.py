# lacesstore/management/commands/backfill_stats.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import connection
from lacesstore.models import DailyVisitorStats, Visitor
from datetime import timedelta

class Command(BaseCommand):
    help = 'Backfill daily visitor statistics for all dates'

    def handle(self, *args, **options):
        self.stdout.write('Starting backfill...')
        
        # Get the oldest visitor date
        oldest_visitor = Visitor.objects.order_by('first_visit').first()
        
        if not oldest_visitor:
            self.stdout.write(self.style.WARNING('No visitors found in database'))
            return
        
        start_date = oldest_visitor.first_visit.date()
        end_date = timezone.now().date()
        
        self.stdout.write(f'Backfilling from {start_date} to {end_date}')
        
        current_date = start_date
        created_count = 0
        
        while current_date <= end_date:
            # Get visitors for this date
            visitors = Visitor.objects.filter(first_visit__date=current_date)
            unique_count = visitors.count()
            
            if unique_count > 0:
                registered_count = visitors.exclude(user__isnull=True).count()
                guest_count = visitors.filter(user__isnull=True).count()
                
                # Create or update stats
                stats, created = DailyVisitorStats.objects.get_or_create(
                    date=current_date,
                    defaults={
                        'unique_visitors': unique_count,
                        'total_page_views': unique_count * 3,  # Estimate: 3 pages per visit
                        'registered_users': registered_count,
                        'guest_users': guest_count,
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'✓ Created stats for {current_date}: {unique_count} visitors')
                else:
                    # Update existing stats
                    stats.unique_visitors = unique_count
                    stats.registered_users = registered_count
                    stats.guest_users = guest_count
                    stats.save()
                    self.stdout.write(f'✓ Updated stats for {current_date}: {unique_count} visitors')
            
            current_date += timedelta(days=1)
        
        self.stdout.write(self.style.SUCCESS(f'Backfill completed! {created_count} new records created.'))