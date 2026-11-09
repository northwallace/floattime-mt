"""Keep temporary download credentials out of the published source catalog."""
from urllib.parse import parse_qs, urlsplit


def validate_public_source_urls(value, path='catalog'):
    if isinstance(value, dict):
        for key, child in value.items():
            validate_public_source_urls(child, f'{path}.{key}')
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_public_source_urls(child, f'{path}[{index}]')
    elif isinstance(value, str) and value.startswith(('https://', 'http://')):
        keys = {key.lower() for key in parse_qs(urlsplit(value).query, keep_blank_values=True)}
        temporary = (
            'sig.expires' in keys
            or any(key.startswith(('x-amz-', 'x-goog-')) for key in keys)
            or {'signature', 'key-pair-id'} <= keys
            or {'sig', 'se', 'sv'} <= keys
        )
        if temporary:
            # Do not echo a signed URL (or its credentials) in validation output.
            raise ValueError(f'{path}: temporary signed source URL; use the stable agency page or document link')
