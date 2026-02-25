from django.db import models

class Ticket(models.Model):

    CATEGORY_CHOICES = [
        ('billing','billing'),
        ('technical','technical'),
        ('account','account'),
        ('general','general'),
    ]

    PRIORITY_CHOICES = [
        ('low','low'),
        ('medium','medium'),
        ('high','high'),
        ('critical','critical'),
    ]

    STATUS_CHOICES = [
        ('open','open'),
        ('in_progress','in_progress'),
        ('resolved','resolved'),
        ('closed','closed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
