import json
import hashlib
from functools import wraps
from django.core.cache import cache
from django.conf import settings

def generate_cache_key(prefix, *args, **kwargs):
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
    key_string = "_".join(key_parts)
    
    if len(key_string) > 200:
        hash_obj = hashlib.md5(key_string.encode('utf-8'))
        key_string = hash_obj.hexdigest()
        
    return f"{settings.CACHES['default']['KEY_PREFIX']}:{prefix}:{key_string}"

def cache_result(prefix, timeout=None):
    if timeout is None:
        timeout = getattr(settings, 'CACHE_TTL', 900)
        
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            skip_cache = kwargs.pop('skip_cache', False)
            
            if skip_cache:
                return func(*args, **kwargs)
                
            cache_key = generate_cache_key(prefix, func.__name__, *args, **kwargs)
            result = cache.get(cache_key)
            
            if result is not None:
                try:
                    return json.loads(result)
                except (TypeError, json.JSONDecodeError):
                    return result
                    
            result = func(*args, **kwargs)
            
            if result is not None:
                try:
                    cache.set(cache_key, json.dumps(result), timeout)
                except (TypeError, ValueError):
                    cache.set(cache_key, result, timeout)
                    
            return result
        return wrapper
    return decorator
    
def clear_user_cache(user_id):
    user_prefix = f"{settings.CACHES['default']['KEY_PREFIX']}:user_{user_id}"
    

    cache.delete_pattern(f"{user_prefix}*")
    
def clear_recommendation_cache(user_id):
    cache_key = f"{settings.CACHES['default']['KEY_PREFIX']}:recommendations:user_{user_id}"
    cache.delete(cache_key)
    
def get_cache_key(prefix, identifier):
    return f"{settings.CACHES['default']['KEY_PREFIX']}:{prefix}:{identifier}"
    
def cache_track(track_id, track_data, timeout=None):
    if timeout is None:
        timeout = getattr(settings, 'CACHE_TTL_LONG', 86400)
        
    cache_key = get_cache_key('track', track_id)
    try:
        cache.set(cache_key, json.dumps(track_data), timeout)
    except (TypeError, ValueError):
        cache.set(cache_key, track_data, timeout)
        
def get_cached_track(track_id):
    cache_key = get_cache_key('track', track_id)
    data = cache.get(cache_key)
    
    if data is not None:
        try:
            return json.loads(data)
        except (TypeError, json.JSONDecodeError):
            return data
            
    return None
    
def cache_user_recommendations(user_id, recommendations, timeout=None):
    if timeout is None:
        timeout = getattr(settings, 'CACHE_TTL', 900)
        
    cache_key = get_cache_key('recommendations', f"user_{user_id}")
    try:
        cache.set(cache_key, json.dumps(recommendations), timeout)
    except (TypeError, ValueError):
        cache.set(cache_key, recommendations, timeout)
        
def get_cached_user_recommendations(user_id):
    cache_key = get_cache_key('recommendations', f"user_{user_id}")
    data = cache.get(cache_key)
    
    if data is not None:
        try:
            return json.loads(data)
        except (TypeError, json.JSONDecodeError):
            return data
            
    return None

def cache_data(key, data, timeout=None):
    if timeout is None:
        timeout = getattr(settings, 'CACHE_TTL', 900)
    
    try:
        cache.set(key, json.dumps(data), timeout)
    except (TypeError, ValueError):
        cache.set(key, data, timeout)
        
def get_cached_data(key):
    data = cache.get(key)
    
    if data is not None:
        try:
            return json.loads(data)
        except (TypeError, json.JSONDecodeError):
            return data
            
    return None 