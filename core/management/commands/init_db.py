from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime

User = get_user_model()

INITIAL_USERS = [
    {
        'username': 'john_doe',
        'email': 'john@example.com',
        'password': 'securepass123',
        'first_name': 'John',
        'last_name': 'Doe',
        'bio': 'Software developer by day, gamer by night',
        'birth_date': datetime(1990, 1, 15),
        'location': 'San Francisco, CA',
        'website': 'https://johndoe.dev',
        'is_staff': True,
        'is_superuser': True,
    },
    {
        'username': 'jane_smith',
        'email': 'jane@example.com',
        'password': 'securepass123',
        'first_name': 'Jane',
        'last_name': 'Smith',
        'bio': 'Digital artist and photography enthusiast',
        'birth_date': datetime(1992, 5, 20),
        'location': 'New York, NY',
        'website': 'https://janesmith.art',
    },
    {
        'username': 'mike_wilson',
        'email': 'mike@example.com',
        'password': 'securepass123',
        'first_name': 'Mike',
        'last_name': 'Wilson',
        'bio': 'Travel blogger exploring the world',
        'birth_date': datetime(1988, 9, 3),
        'location': 'London, UK',
        'website': 'https://mikestravels.com',
    }
]


class Command(BaseCommand):
    help = 'Initialize database with sample users'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating initial users...')

        for user_data in INITIAL_USERS:
            password = user_data.pop('password')
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )

            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully created user: {user.username}'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'User {user.username} already exists'
                ))

        self.stdout.write(self.style.SUCCESS(
            'Database initialization completed!'))
