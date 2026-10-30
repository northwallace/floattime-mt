"""Validate private location evidence without publishing or trusting client identity."""
import math
from datetime import date


def validate_location(value):
    if not isinstance(value, dict): raise ValueError('Location must be an object')
    for key, limit in [('lat',85),('lon',180)]:
        n=value.get(key)
        if type(n) not in (int,float) or not math.isfinite(n) or abs(n)>limit:
            raise ValueError('Enter valid latitude and longitude')
    if value.get('endpoint') not in ('putIn','takeOut','other'): raise ValueError('Choose the endpoint')
    if value.get('pinType') not in ('landing','parking','entrance'): raise ValueError('Choose a pin type')
    if value.get('method') not in ('manual','map','gps'): raise ValueError('Invalid location method')
    if type(value.get('firsthand',False)) is not bool: raise ValueError('Invalid firsthand flag')
    observed=value.get('observedOn','')
    if not isinstance(observed,str): raise ValueError('Invalid visit date')
    if observed:
        try: visit=date.fromisoformat(observed)
        except ValueError: raise ValueError('Invalid visit date')
        if visit>date.today(): raise ValueError('Visit date cannot be in the future')
    return {**{k:value[k] for k in ('lat','lon','endpoint','pinType','method')},'observedOn':observed,'firsthand':value.get('firsthand',False),'status':'community-reported'}
