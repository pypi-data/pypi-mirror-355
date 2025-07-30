from django.db import models
from django.conf import settings

class CaptchaChallenge(models.Model):
    TYPE_CHOICES = [
        ('MATH', 'Math Problem'),
        ('IMAGE', 'Image Recognition'),
        ('INVISIBLE', 'Invisible'),
        ('HONEYPOT', 'Honeypot'),
    ]
    
    challenge_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    secret = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # For image challenges
    image = models.ImageField(null=True, blank=True)
    image_areas = models.JSONField(null=True, blank=True)
    
    # For math challenges
    question = models.CharField(max_length=100, null=True, blank=True)
    answer = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['secret']),
            models.Index(fields=['expires_at']),
        ]

class CaptchaLog(models.Model):
    challenge = models.ForeignKey(CaptchaChallenge, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    was_successful = models.BooleanField()
    client_data = models.JSONField(default=dict)