from django.db import models
from django.core.exceptions import ValidationError

class Source(models.Model):
    TYPE_CHOICES = [
        ('movie', 'Фильм'),
        ('book', 'Книга'),
        ('other', 'Другое'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Название")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Тип")
    year = models.IntegerField(null=True, blank=True, verbose_name="Год")
    
    class Meta:
        unique_together = ['title', 'type']
    
    def __str__(self):
        return f"{self.get_type_display()}: {self.title}"

from django.db import models
from django.core.exceptions import ValidationError

from django.db import models
from django.core.exceptions import ValidationError

class Quote(models.Model):
    text = models.TextField(verbose_name="Текст цитаты")
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='quotes')
    weight = models.IntegerField(default=1, verbose_name="Вес")
    views_count = models.IntegerField(default=0, verbose_name="Количество просмотров")
    likes = models.IntegerField(default=0, verbose_name="Лайки")
    dislikes = models.IntegerField(default=0, verbose_name="Дизлайки")
    voted_ips = models.JSONField(default=list, blank=True, verbose_name="Проголосовавшие IP")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['text', 'source']
    
    def clean(self):
        # Проверяем, что у источника не больше 3 цитат
        if self.pk is None:  # только для новых объектов
            # Проверяем существование такой же цитаты
            if Quote.objects.filter(text=self.text, source=self.source).exists():
                raise ValidationError("Цитата с таким текстом и источником уже существует")
            
            # Проверяем ограничение на количество цитат у источника
            if Quote.objects.filter(source=self.source).count() >= 3:
                raise ValidationError("У одного источника не может быть больше 3 цитат")    
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def has_user_voted(self, ip_address):
        return ip_address in self.voted_ips
    
    def add_vote(self, ip_address, vote_type):
        if not self.has_user_voted(ip_address):
            if vote_type == 'like':
                self.likes += 1
            elif vote_type == 'dislike':
                self.dislikes += 1
            
            self.voted_ips.append(ip_address)
            self.save()
            return True
        return False
    
    def __str__(self):
        return f'"{self.text[:50]}..." - {self.source}'
    

