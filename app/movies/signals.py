from django.dispatch import receiver
from django.db.models.signals import post_save


@receiver(post_save, sender='movies.Person')
def congratulatory(sender, instance, created, **kwargs):
    if created and 'John' in instance.full_name:
        print(
            f"""Cегодня к нам присоединился еще один Джон -
            {instance.full_name}! 🥳""")
