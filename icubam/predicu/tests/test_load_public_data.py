import datetime

import predicu.data


def test_load_public_data():
    data = predicu.data.load_public_data()
    max_date = data.date.max()
    now = datetime.datetime.now()
    if now.hour < 20:
        expected_date = (now - datetime.timedelta(days=1)).date()
    else:
        expected_date = now.date()
    assert max_date == expected_date
