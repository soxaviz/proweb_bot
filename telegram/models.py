from django.db import models


class Course(models.Model):
    title = models.CharField(
        max_length=300
    )
    language = models.CharField(
        max_length=150
    )

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'


class Group(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=300
    )
    telegram_group_id = models.CharField(
        max_length=250
    )

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'


class UserAdmin(models.Model):
    telegram_id = models.IntegerField(
        unique=True,
    )
    username = models.CharField(
        max_length=250,
        blank=True,
        null=True
    )
    first_name = models.CharField(
        max_length=250,
        blank=True,
        null=True
    )
    last_name = models.CharField(
        max_length=250,
        blank=True,
        null=True
    )
    is_admin = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f"{self.first_name}"

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

