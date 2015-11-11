import geojson

from datetime import datetime, date, timedelta
from os import environ

from sentinelsat.sentinel import (SentinelAPI, format_date, get_coordinates,
    convert_timestamp)


def test_format_date():
    assert format_date(datetime(2015, 1, 1)) == '2015-01-01T00:00:00Z'
    assert format_date(date(2015, 1, 1)) == '2015-01-01T00:00:00Z'
    assert format_date('2015-01-01T00:00:00Z') == '2015-01-01T00:00:00Z'
    assert format_date('20150101') == '2015-01-01T00:00:00Z'
    assert format_date('NOW') == 'NOW'


def test_convert_timestamp():
    assert convert_timestamp('/Date(1445588544652)/') == '2015-10-23T08:22:24Z'


def test_SentinelAPI():
    api = SentinelAPI(
        environ.get('SENTINEL_USER'),
        environ.get('SENTINEL_PASSWORD')
    )
    api.query('0 0,1 1,0 1,0 0', datetime(2015, 1, 1), datetime(2015, 1, 2))

    assert api.url == 'https://scihub.esa.int/dhus/search?format=json&rows=15000' + \
        '&q=(ingestionDate:[2015-01-01T00:00:00Z TO 2015-01-02T00:00:00Z]) ' + \
        'AND (footprint:"Intersects(POLYGON((0 0,1 1,0 1,0 0)))")'
    assert api.content.status_code == 200

    now = datetime.now()
    api.format_url('0 0,1 1,0 1,0 0', end_date=now)
    last_24h = format_date(now - timedelta(hours=24))
    assert api.url == 'https://scihub.esa.int/dhus/search?format=json&rows=15000' + \
        '&q=(ingestionDate:[%s TO %s]) ' % (last_24h, format_date(now)) + \
        'AND (footprint:"Intersects(POLYGON((0 0,1 1,0 1,0 0)))")'

    api.format_url('0 0,1 1,0 1,0 0', end_date=now, producttype='SLC')
    assert api.url == 'https://scihub.esa.int/dhus/search?format=json&rows=15000' + \
        '&q=(ingestionDate:[%s TO %s]) ' % (last_24h, format_date(now)) + \
        'AND (footprint:"Intersects(POLYGON((0 0,1 1,0 1,0 0)))") ' + \
        'AND (producttype:SLC)'


def test_get_coordinates():
    coords = '-66.2695312 -8.0592296,-66.2695312 0.7031074,' + \
        '-57.3046875 0.7031074,-57.3046875 -8.0592296,' +\
        '-66.2695312 -8.0592296'
    assert get_coordinates('tests/map.geojson') == coords


def test_get_product_info():
    api = SentinelAPI(
        environ.get('SENTINEL_USER'),
        environ.get('SENTINEL_PASSWORD')
    )

    expected = {'id': '079ed72f-b330-4918-afb8-b63854e375a5',
        'title': 'S1A_IW_GRDH_1SDV_20150527T081303_20150527T081328_006104_007EB2_E65B',
        'size': 1051461964,
        'date': '2015-05-27T08:13:03Z',
        'footprint': '-21.032057 -39.925808,-20.472944 -42.301277,-18.975924 -41.904408,-19.528255 -39.549416,-21.032057 -39.925808',
        'url': "https://scihub.esa.int/dhus/odata/v1/Products('079ed72f-b330-4918-afb8-b63854e375a5')/$value"
        }
    assert api.get_product_info('079ed72f-b330-4918-afb8-b63854e375a5') == expected


def test_footprints():
    api = SentinelAPI(
    environ.get('SENTINEL_USER'),
    environ.get('SENTINEL_PASSWORD')
    )
    api.query(get_coordinates('tests/map.geojson'), datetime(2014, 10, 10), datetime(2014, 12, 31), producttype="GRD")

    expected_footprints = geojson.loads(open('tests/expected_search_footprints.geojson', 'r').read())

    # to compare unordered lists (JSON objects) they need to be sorted or changed to sets
    assert set(api.get_footprints()) == set(expected_footprints)