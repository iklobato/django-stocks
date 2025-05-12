from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userrequesthistory',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userrequesthistory',
            name='data',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='userrequesthistory',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.RenameField(
            model_name='userrequesthistory',
            old_name='stock_symbol',
            new_name='symbol',
        ),
        migrations.AlterModelOptions(
            name='userrequesthistory',
            options={'ordering': ['-created_at'], 'verbose_name_plural': 'User request histories'},
        ),
    ]