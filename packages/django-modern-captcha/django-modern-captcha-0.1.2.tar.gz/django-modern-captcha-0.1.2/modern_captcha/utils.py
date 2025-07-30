import time
import json
import hashlib
import numpy as np
from django.conf import settings
from django.core.cache import cache
from sklearn.ensemble import IsolationForest

# Constants
DEFAULT_RISK_THRESHOLD = 0.65
BEHAVIOR_CACHE_TIMEOUT = 3600  # 1 hour

def generate_captcha_id(ip_address: str) -> str:
    """Generate unique CAPTCHA ID based on IP and timestamp"""
    timestamp = str(time.time()).encode('utf-8')
    unique_string = f"{ip_address}{timestamp}".encode('utf-8')
    return hashlib.sha256(unique_string).hexdigest()[:16]

def analyze_behavior(behavior_data: dict) -> float:
    """
    Analyze user behavior patterns using machine learning
    Returns risk score between 0 (human) and 1 (bot)
    """
    # Convert behavior data to feature vector
    features = [
        len(behavior_data.get('mouse_events', [])),
        len(behavior_data.get('key_events', [])),
        behavior_data.get('timing_data', {}).get('form_fill_time', 0),
        behavior_data.get('timing_data', {}).get('mouse_idle_time', 0),
    ]
    
    # Load or create behavior model
    model = cache.get('behavior_model')
    if not model:
        model = IsolationForest(contamination=0.1)
        # Initialize with some dummy normal behavior data
        dummy_data = np.random.normal(5, 1, (100, 4))
        model.fit(dummy_data)
        cache.set('behavior_model', model, BEHAVIOR_CACHE_TIMEOUT)
    
    # Calculate anomaly score
    risk_score = model.decision_function([features])[0]
    return max(0, min(1, (risk_score + 0.5) * 0.5))  # Normalize to 0-1

def validate_timestamp(timestamp: float, max_age: int = 300) -> bool:
    """Validate if timestamp is recent"""
    current_time = time.time()
    return current_time - timestamp <= max_age

def generate_math_challenge() -> dict:
    """Generate simple math challenge"""
    operations = [
        ('+', lambda a, b: a + b),
        ('-', lambda a, b: a - b),
        ('*', lambda a, b: a * b),
    ]
    op_symbol, op_func = operations[np.random.randint(0, len(operations))]
    a = np.random.randint(1, 10)
    b = np.random.randint(1, 10)
    question = f"{a} {op_symbol} {b}"
    answer = str(op_func(a, b))
    return {'question': question, 'answer': answer}

def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_config():
    """Get merged configuration from settings and defaults"""
    return {
        'risk_threshold': getattr(settings, 'MODERN_CAPTCHA_RISK_THRESHOLD', DEFAULT_RISK_THRESHOLD),
        'enabled_methods': getattr(settings, 'MODERN_CAPTCHA_METHODS', ['honeypot', 'behavior', 'math']),
        'cache_timeout': getattr(settings, 'MODERN_CAPTCHA_CACHE_TIMEOUT', 300),
    }

class BehaviorLogger:
    """Utility class for logging and analyzing behavior patterns"""
    
    def __init__(self, request=None):
        self.request = request
        self.data = {
            'mouse_events': [],
            'key_events': [],
            'timing_data': {
                'start_time': time.time(),
                'last_activity': time.time(),
            }
        }
    
    def add_mouse_event(self, x, y):
        """Record mouse movement"""
        self.data['mouse_events'].append({
            'x': x,
            'y': y,
            'timestamp': time.time()
        })
        self._update_activity()
    
    def add_key_event(self, key):
        """Record keyboard activity"""
        self.data['key_events'].append({
            'key': key,
            'timestamp': time.time()
        })
        self._update_activity()
    
    def _update_activity(self):
        """Update last activity timestamp"""
        self.data['timing_data']['last_activity'] = time.time()
    
    def get_risk_score(self):
        """Calculate and return behavior risk score"""
        self.data['timing_data']['total_time'] = (
            time.time() - self.data['timing_data']['start_time']
        )
        return analyze_behavior(self.data)