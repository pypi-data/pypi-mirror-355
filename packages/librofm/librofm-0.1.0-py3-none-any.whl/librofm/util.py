from functools import wraps

from librofm.models import Audiobook

def requires_auth(func):
    """Decorator that ensures authentication before method execution."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.access_token:
            self.authenticate()
        return func(self, *args, **kwargs)
    return wrapper
    
def get_isbn(audiobook: Audiobook | str) -> str:
    """Returns the ISBN of the audiobook, or the audiobook itself if it's a string."""
    return audiobook.isbn if isinstance(audiobook, Audiobook) else audiobook


def clean_filename(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in (' ', '-', '_', '(', ')', '.', ',')).rstrip()
