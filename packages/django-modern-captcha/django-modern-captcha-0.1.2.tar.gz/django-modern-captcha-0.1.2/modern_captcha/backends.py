import time
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import CaptchaChallenge
from .utils import analyze_behavior


class ModernCaptchaBackend:
    def __init__(self, request=None):
        self.request = request
    
    def validate(self, form_data):
        # Check multiple verification methods
        methods = [
            self._validate_honeypot,
            self._validate_timing,
            self._validate_challenge,
            self._validate_behavior
        ]
        
        for method in methods:
            try:
                method(form_data)
            except ValidationError as e:
                raise e
        
        return True
    
    def _validate_honeypot(self, form_data):
        if 'hp_name' in form_data and form_data['hp_name']:
            raise ValidationError("Honeypot field was filled")
    
    def _validate_timing(self, form_data):
        if 'captcha_start_time' in form_data:
            submit_time = time.time()
            load_time = float(form_data['captcha_start_time'])
            if submit_time - load_time < 2:  # Less than 2 seconds to submit
                raise ValidationError("Form submitted too quickly")
    
    def _validate_challenge(self, form_data):
        if 'captcha_id' in form_data and 'captcha_response' in form_data:
            try:
                challenge = CaptchaChallenge.objects.get(
                    pk=form_data['captcha_id'],
                    is_active=True,
                    expires_at__gt=timezone.now()
                )
                
                if challenge.challenge_type == 'MATH':
                    if form_data['captcha_response'] != challenge.answer:
                        raise ValidationError("Incorrect answer")
                
                # Add other challenge type validations
                
                challenge.is_active = False
                challenge.save()
                
            except CaptchaChallenge.DoesNotExist:
                raise ValidationError("Invalid CAPTCHA challenge")
    
    def _validate_behavior(self, form_data):
        if self.request:
            behavior_data = {
                'ip': self.request.META.get('REMOTE_ADDR'),
                'user_agent': self.request.META.get('HTTP_USER_AGENT'),
                'headers': {k: v for k, v in self.request.META.items() 
                            if k.startswith('HTTP_')},
                'mouse_events': form_data.get('mouse_events', []),
                'key_events': form_data.get('key_events', []),
                'timing_data': form_data.get('timing_data', {})
            }
            
            risk_score = analyze_behavior(behavior_data)
            if risk_score > settings.MODERN_CAPTCHA_RISK_THRESHOLD:
                raise ValidationError("Suspicious behavior detected")