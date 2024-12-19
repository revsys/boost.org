# Generated by Django 4.2.16 on 2024-12-19 15:20

from django.db import migrations


def drop_existing_reviews(apps, schema_editor):
    Review = apps.get_model("versions", "Review")
    output = Review.objects.all().delete()
    print(f"\nDeleted {output}...")


class Migration(migrations.Migration):
    dependencies = [
        ("versions", "0015_drop_review_generated_stub_users"),
    ]
    operations = [
        migrations.RunPython(drop_existing_reviews, migrations.RunPython.noop),
    ]
