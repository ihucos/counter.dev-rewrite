from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("counter", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="timezone",
            field=models.IntegerField(default=0, help_text="UTC offset in minutes"),
        ),
        migrations.AddField(
            model_name="user",
            name="share_token",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]