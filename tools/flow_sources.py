"""Reviewed flow-source identifiers and agency discharge adapters.

Catalog evidence chooses a station; a successful request never chooses one.
Only instantaneous discharge is supported here, not stage or daily averages.
"""
from datetime import date, datetime, timedelta, timezone
import math
import re
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

USBR_DAYFILE = 'https://www.usbr.gov/gp-bin/webdaycsv.pl'
CDWR_API = 'https://dwr.state.co.us/Rest/GET/api/v2/telemetrystations/'


def gauge_relationship(river):
    return river.get('gaugeRelationship', 'representative' if river.get('gauge') or river.get('flowSource') else 'none')


def supports_live_timing(river):
    return bool(flow_key(river) and gauge_relationship(river) == 'representative'
                and river.get('timing', {}).get('mode') != 'unavailable')


def flow_key(river):
    if gauge_relationship(river) in ('none', 'other-river-reference'):
        return None
    source = river.get('flowSource')
    if not source:
        return river.get('gauge')
    prefix = {'usbr-gp': 'USBR', 'colorado-dwr': 'CDWR'}[source['provider']]
    return f"{prefix}:{source['station']}:{source['parameter']}"


def flow_provider(river):
    return {'usbr-gp': 'Reclamation', 'colorado-dwr': 'Colorado DWR'}.get(
        river.get('flowSource', {}).get('provider'), 'USGS')


def flow_label(river):
    if not river.get('gauge') and not river.get('flowSource'):
        return 'No suitable flow gauge'
    source = river.get('flowSource')
    return f"{flow_provider(river)} {source['station']}" if source else f"USGS {river['gauge']}"


def flow_name(river):
    return river.get('flowSource', {}).get('name', river.get('gaugeName') or 'No suitable flow gauge')


def flow_url(river):
    if not river.get('gauge') and not river.get('flowSource'):
        return None
    return river.get('flowSource', {}).get('sourceUrl',
        f"https://waterdata.usgs.gov/monitoring-location/USGS-{river.get('gauge')}/")


def flow_description(river):
    relation = gauge_relationship(river)
    if relation == 'none':
        return 'No suitable flow gauge is assigned. Reviewed access information and published guide times remain available.'
    station = f'{flow_label(river)} ({flow_name(river)})'
    if relation == 'other-river-reference':
        return f'{station} measures another river. It is linked for reference only; its readings are not used for this river’s flow, water temperature or trip estimates.'
    if relation == 'same-river-reference':
        return f'{station} provides reference conditions elsewhere on this river. Its readings do not measure every listed section and are not used for live trip estimates.'
    return f'Float ETA uses {station} for discharge when a recent reading is available.'


def validate_gauge(river):
    gauge = river.get('gauge')
    if gauge is not None and (not isinstance(gauge, str) or not re.fullmatch(r'\d{8,15}', gauge)):
        raise ValueError('Gauge must be null or an 8–15 digit string')
    if gauge is not None and (not isinstance(river.get('gaugeName'), str) or not river['gaugeName'].strip()):
        raise ValueError('gaugeName required for an assigned station')
    relation = gauge_relationship(river)
    if relation not in ('representative', 'same-river-reference', 'other-river-reference', 'none'):
        raise ValueError('Invalid gauge relationship')
    has_source = bool(gauge or river.get('flowSource'))
    if (relation == 'none') == has_source:
        raise ValueError('Gauge relationship must match whether a source is assigned')
    if relation != 'representative':
        if river.get('timing', {}).get('mode') != 'unavailable':
            raise ValueError('Missing or reference-only gauges require unavailable timing')
        if not river.get('gaugeContext'):
            raise ValueError('Missing or reference-only gauges require sourced gaugeContext')


def validate_source(river):
    source = river.get('flowSource')
    if source is None:
        return
    if not isinstance(source, dict) or source.get('provider') not in ('usbr-gp', 'colorado-dwr'):
        raise ValueError('Unsupported flow source provider')
    parameters = ('Q', 'Q_I') if source['provider'] == 'usbr-gp' else ('DISCHRG',)
    if not re.fullmatch(r'[A-Z0-9]{3,12}', str(source.get('station', ''))) or source.get('parameter') not in parameters:
        raise ValueError('Flow source needs a station and supported instantaneous discharge parameter')
    expected_kind = 'dam-release' if source['parameter'] == 'Q_I' else 'streamflow'
    if source.get('timeZone') != 'America/Denver' or source.get('kind') != expected_kind:
        raise ValueError('Flow kind must distinguish river discharge from imported dam release')
    for key in ('name', 'note', 'sourceUrl', 'checkedOn'):
        if not isinstance(source.get(key), str) or not source[key].strip():
            raise ValueError('Flow source ' + key + ' required')
    prefix = ('https://www.usbr.gov/gp-bin/hydromet_dayfiles.pl?' if source['provider'] == 'usbr-gp'
              else 'https://dwr.state.co.us/Tools/Stations/')
    if source['sourceUrl'] != prefix + source['station']:
        raise ValueError('Use the official station page')
    date.fromisoformat(source['checkedOn'])
    # These replacements provide conditions, not a newly calibrated ETA model.
    if river.get('timing', {}).get('mode') != 'unavailable':
        raise ValueError('Alternative flow sources currently require unavailable timing')
    if river.get('gaugeContext', {}).get('status') != 'context-only':
        raise ValueError('Alternative flow sources require reach-specific context')


def cdwr_urls(source, now):
    end = now.astimezone(ZoneInfo(source['timeZone'])).date()
    common = {'abbrev': source['station'], 'parameter': 'DISCHRG'}
    return (CDWR_API + 'telemetrystation?' + urlencode({'abbrev': source['station']}),
            CDWR_API + 'telemetrytimeseriesraw?' + urlencode({**common,
                'startDate': (end - timedelta(days=7)).isoformat(),
                'endDate': (end + timedelta(days=1)).isoformat(), 'pageSize': 2000}))


def _cdwr_rows(payload):
    if not isinstance(payload, dict) or payload.get('PageCount') != 1 or payload.get('PageNumber') != 1:
        raise ValueError('Missing or incomplete Colorado DWR response')
    rows = payload.get('ResultList')
    if not isinstance(rows, list) or payload.get('ResultCount') != len(rows):
        raise ValueError('Colorado DWR row count mismatch')
    return rows


def _cdwr_value(row):
    # DWR's stationflags dictionary: A approved, O original, P provisional.
    # Ice/backwater/estimated/maintenance/seasonal flags cannot become live flow.
    if row.get('flagA') not in ('A', 'O', 'P') or row.get('flagB') not in (None, ''):
        return None
    value = row.get('measValue')
    return value if type(value) in (int, float) and math.isfinite(value) and 0 <= value < 998877 else None


def parse_cdwr(station_payload, history_payload, source, now):
    rows = _cdwr_rows(station_payload)
    if len(rows) != 1:
        raise ValueError('Colorado DWR station missing or ambiguous')
    row = rows[0]
    if (row.get('abbrev') != source['station'] or row.get('parameter') != 'DISCHRG'
            or row.get('units', '').lower() != 'cfs' or row.get('dataSourceAbbrev') != 'DWR'
            or row.get('stationStatus') != 'Active' or row.get('thirdParty') is not False):
        raise ValueError('Colorado DWR source, parameter, units or status mismatch')
    stamp = datetime.fromisoformat(str(row.get('measDateTime', '')))
    if stamp.utcoffset() is None:
        raise ValueError('Colorado DWR latest reading needs an explicit UTC offset')
    if stamp > now + timedelta(minutes=5) or stamp < now - timedelta(days=8):
        raise ValueError('Colorado DWR latest timestamp outside supported window')
    flow = _cdwr_value(row)
    series = []
    zone = ZoneInfo(source['timeZone'])
    if stamp.astimezone(zone).replace(tzinfo=None) != stamp.replace(tzinfo=None):
        raise ValueError('Colorado DWR history clock convention changed')
    for point in _cdwr_rows(history_payload):
        if (point.get('abbrev') != source['station'] or point.get('parameter') != 'DISCHRG'
                or point.get('measUnit', '').lower() != 'cfs'):
            raise ValueError('Colorado DWR history station, parameter or units mismatch')
        value = _cdwr_value(point)
        if value is None:
            continue
        try:
            time = datetime.fromisoformat(point['measDateTime'])
            if time.utcoffset() is None:
                if time.replace(tzinfo=zone, fold=0).utcoffset() != time.replace(tzinfo=zone, fold=1).utcoffset():
                    continue
                time = time.replace(tzinfo=zone)
        except (ValueError, KeyError, TypeError):
            continue
        if now - timedelta(days=8) <= time <= now + timedelta(minutes=5):
            series.append({'t': time.timestamp() * 1000, 'q': value})
    series.sort(key=lambda point: point['t'])
    return {'flow': flow, 'at': stamp.timestamp() * 1000 if flow is not None else None,
            'temp': None, 'tempAt': None, 'series': series,
            'source': 'Colorado Division of Water Resources', 'sourceUrl': source['sourceUrl'],
            'station': source['station'], 'provisional': row.get('flagA') != 'A'}


def dayfile_url(source, now):
    end = now.astimezone(ZoneInfo(source['timeZone'])).date()
    start = end - timedelta(days=7)
    return USBR_DAYFILE + '?' + urlencode({
        'parameter': source['station'] + ' ' + source['parameter'],
        'syer': start.year, 'smnth': start.month, 'sdy': start.day,
        'eyer': end.year, 'emnth': end.month, 'edy': end.day, 'format': 2,
    })


def _local_timestamp(value, zone):
    naive = datetime.strptime(value, '%m/%d/%Y %H:%M')
    first, second = naive.replace(tzinfo=zone, fold=0), naive.replace(tzinfo=zone, fold=1)
    # The feed has no UTC offset: do not guess during a DST fold or gap.
    if first.utcoffset() != second.utcoffset():
        return None
    return first.timestamp() * 1000


def parse_dayfile(text, source, now):
    """Format 2 retains quality flags; accept only unflagged numeric cells.

    Format 8 hides near-zero readings and JSON omits quality flags. Neither is
    suitable for this adapter. Missing/flagged values must not become zero flow.
    """
    body = re.search(r'BEGIN DATA\s*\n(.*?)END DATA', text, re.S)
    if not body:
        raise ValueError('Missing Reclamation data table')
    lines = body[1].strip().splitlines()
    header = r'DATE\s+TIME\s*,\s*' + re.escape(source['station']) + r'\s+' + re.escape(source['parameter']) + r'\s*'
    if not lines or not re.fullmatch(header, lines[0].strip()):
        raise ValueError('Reclamation station or parameter mismatch')
    zone = ZoneInfo(source['timeZone'])
    # GP's generated-at header was cross-checked against UTC. If its clock
    # convention changes, fail closed instead of silently shifting reading age.
    generated = re.search(r'retrieved:\s*([A-Za-z]{3} [A-Za-z]{3}\s+\d{1,2} \d{2}:\d{2}:\d{2} \d{4})', text)
    if not generated:
        raise ValueError('Missing Reclamation retrieval clock')
    clock = datetime.strptime(generated[1], '%a %b %d %H:%M:%S %Y').replace(tzinfo=zone)
    if abs((now - clock).total_seconds()) > 900:
        raise ValueError('Reclamation retrieval clock differs from expected timezone')
    values = {}
    for line in lines[1:]:
        cell = re.fullmatch(r'\s*(\d{2}/\d{2}/\d{4} \d{2}:\d{2}),\s*([+-]?\d+(?:\.\d+)?)\s*', line)
        if not cell:
            continue
        try:
            stamp = _local_timestamp(cell[1], zone)
            value = float(cell[2])
        except ValueError:
            continue
        if stamp is None or not math.isfinite(value) or value < 0 or value >= 998877:
            continue
        if stamp > now.timestamp() * 1000 + 300000 or stamp < (now - timedelta(days=8)).timestamp() * 1000:
            continue
        values[stamp] = value
    series = [{'t': t, 'q': q} for t, q in sorted(values.items())]
    latest = series[-1] if series else {}
    return {'flow': latest.get('q'), 'at': latest.get('t'), 'temp': None, 'tempAt': None,
            'series': series, 'source': 'Bureau of Reclamation GP Hydromet',
            'sourceUrl': source['sourceUrl'], 'station': source['station'], 'provisional': True}
