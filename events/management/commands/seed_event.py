from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from events.utils import get_event_settings


class Command(BaseCommand):
    help = "Create the default PIEMR event settings and admin account."

    def handle(self, *args, **options):
        event = get_event_settings()
        event.organizer = "Prestige Institute of Engineering Management and Research, Indore"
        event.organized_by = "Dept. of Computer Science Engineering & AIDS, PIEMR"
        event.event_scope = "National Event"
        event.expert_name = "Mr. Dhawal Shrivastava"
        event.expert_linkedin = "https://www.linkedin.com/in/dhawalshrivastava/"
        event.expert_image_url = "https://media.licdn.com/dms/image/v2/D4D03AQEHp61h7Scm_Q/profile-displayphoto-scale_400_400/B4DZ1mJcS7KUAg-/0/1775535249227?e=1778716800&v=beta&t=Tw6w9QjbI7f_BpVxEfIH-vUi52lW60lmLgn2AI5FrFw"
        event.venue = "Civil Auditorium, PIEMR, Prestige Vihar, Scheme Number 72, Vijay Nagar, Indore"
        event.faculty_coordinator_name = "Prof Dr. Dinesh C Jain"
        event.faculty_coordinator_detail = "Dept. of CSE"
        event.faculty_coordinator_email = "djain@piemr.edu.in"
        event.student_coordinator_name = "Mr. Agastya Sharma"
        event.student_coordinator_detail = "4 Sem CSE, PIEMR"
        event.student_coordinator_email = "51110105688@piemr.edu.in"
        event.seat_limit = max(event.seat_limit, 100)
        event.registration_open = True
        event.save()

        admin, created = User.objects.get_or_create(
            username="piemr#123",
            defaults={
                "email": "work.agastya20@gmail.com",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.email = "work.agastya20@gmail.com"
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password("piemr#123")
        admin.save()

        action = "created" if created else "updated"
        self.stdout.write(self.style.SUCCESS(f"Seed complete: event ready, admin {action}."))
