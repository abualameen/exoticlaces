# lacesstore/management/commands/update_daily_stats.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from lacesstore.models import DailyVisitorStats, Visitor

class Command(BaseCommand):
    help = 'Update daily visitor statistics for today'

    def handle(self, *args, **options):
        # Get today's date
        today = timezone.now().date()
        
        # Get visitors for today
        visitors = Visitor.objects.filter(first_visit__date=today)
        unique_count = visitors.count()
        registered_count = visitors.exclude(user__isnull=True).count()
        guest_count = visitors.filter(user__isnull=True).count()
        
        # Create or update stats
        stats, created = DailyVisitorStats.objects.get_or_create(
            date=today,
            defaults={
                'unique_visitors': unique_count,
                'total_page_views': unique_count * 3,
                'registered_users': registered_count,
                'guest_users': guest_count,
            }
        )
        
        if not created:
            stats.unique_visitors = unique_count
            stats.registered_users = registered_count
            stats.guest_users = guest_count
            stats.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Updated stats for {today}: {stats.unique_visitors} unique visitors')
        )