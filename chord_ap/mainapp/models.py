from django.db import models

# Create your models here.
class Chords(models.Model):

    title = models.CharField('楽曲タイトル', max_length=30)
    subtitle = models.CharField('サブ情報(作詞作曲等)', max_length=255)
    link = models.CharField('リンク', max_length=500)
    chords = models.CharField('コード', max_length=10000)

    def __str__(self):
        return self.name
