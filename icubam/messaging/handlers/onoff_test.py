from icubam.messaging.handlers import onoff

def test_silence_request():
  userid = 123
  icuids = [773, 32]
  on = False
  delay = None

  request = onoff.OnOffRequest(
    user_id=userid, icu_ids=icuids, on=on, delay=delay
  )
  encoded = request.to_json()
  assert isinstance(encoded, str)

  decoded = onoff.OnOffRequest()
  assert decoded.user_id == None

  decoded.from_json(encoded)
  assert decoded.user_id == userid
  assert len(decoded.icu_ids) == len(icuids)
  assert decoded.icu_ids[0] == icuids[0]
  assert decoded.on == on
  assert decoded.on == on
  assert decoded.delay == delay
