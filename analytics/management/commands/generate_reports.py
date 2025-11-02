from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from analytics.models import Report

class Command(BaseCommand):
    help = 'Automatically generate/update reports for the last 7 days'

    def handle(self, *args, **options):
        end = timezone.now().date()
        start = end - timedelta(days=7)
        report_types = Report.REPORT_TYPES
        for rtype, _ in report_types:
            report, created = Report.objects.get_or_create(
                title=f'Auto {rtype.title()} Report',
                report_type=rtype,
                start_date=start,
                end_date=end,
                defaults={'is_auto_generated': True}
            )
            if not created:
                report.start_date = start
                report.end_date = end
            report.update_data()
            self.stdout.write(self.style.SUCCESS(f'Updated {rtype} report'))