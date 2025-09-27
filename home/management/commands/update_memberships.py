from django.core.management.base import BaseCommand
from django.utils import timezone
from home.models import User

class Command(BaseCommand):
    help = "Deactivate expired memberships"

    def handle(self, *args, **kwargs):
        now = timezone.now()
        users = User.objects.filter(is_member=True)
        for user in users:
            active_membership = user.memberships.order_by('-expiry_date').first()
            if not active_membership or active_membership.expiry_date < now:
                user.is_member = False
                user.save(update_fields=['is_member'])
                self.stdout.write(f"Membership expired for {user.username}")
