
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("budgets", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="alert",
            name="kind",
            field=models.CharField(
                choices=[
                    ("Threshold", "Threshold"),
                    ("Limit", "Limit"),
                ],
                max_length=10,
                null=True,
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="budget",
            name="start_date",
            field=models.DateField(null=True, blank=True),
        ),
    ]
