# Generated by Django 2.1.2 on 2019-02-18 08:52

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Chords',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=30, verbose_name='楽曲タイトル')),
                ('subtitle', models.CharField(max_length=255, verbose_name='サブ情報(作詞作曲等)')),
                ('link', models.CharField(max_length=500, verbose_name='リンク')),
                ('chords', models.CharField(max_length=10000, verbose_name='コード')),
            ],
        ),
    ]
