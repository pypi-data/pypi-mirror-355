from django import forms
from django.conf import settings
import time
from django.core.exceptions import ValidationError
from .backends import ModernCaptchaBackend

class ModernCaptchaForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Add honeypot field
        self.fields['hp_name'] = forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={
                'style': 'display:none;',
                'autocomplete': 'off',
                'tabindex': '-1'
            }),
            label=''
        )
        
        # Add timing field
        self.fields['captcha_start_time'] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=str(time.time())
        )
    
    def clean(self):
        cleaned_data = super().clean()
        
        captcha = ModernCaptchaBackend(self.request)
        try:
            captcha.validate(self.data)
        except ValidationError as e:
            self.add_error(None, e)
        
        return cleaned_data