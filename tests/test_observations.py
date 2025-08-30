import datetime as dt

ISO = "%Y-%m-%dT%H:%M:%SZ"


def iso(dtobj):
    return dtobj.strftime(ISO)


def test_observations_flow(client, authz):
    # Ensure there is at least one buoy to reference (id=1 likely after create_all; but create explicitly)
    rv = client.post(
        "/buoys",
        json={"name": "BW-OBS", "lat": 1.0, "lon": 1.0, "status": "active"},
        headers=authz,
    )
    assert rv.status_code in (200, 201), rv.get_json()
    buoy = rv.get_json()
    buoy_id = buoy["id"]

    # Create two observations in current quarter
    now = dt.datetime.now(dt.timezone.utc)
    o1 = {
        "buoy_id": buoy_id,
        "observed_at": iso(now.replace(microsecond=0)),
        "timezone": "UTC",
        "lat": 1.1,
        "lon": 1.2,
        "temp_c": 24.5,
        "humidity": 55,
        "wind_m_s": 3.2,
        "precipitation_mm": 0.0,
        "haze": False,
        "notes": "ok",
    }
    o2 = {
        "buoy_id": buoy_id,
        "observed_at": iso((now + dt.timedelta(hours=1)).replace(microsecond=0)),
        "timezone": "UTC",
        "lat": 1.15,
        "lon": 1.25,
        "temp_c": 24.7,
        "humidity": 54,
        "wind_m_s": 3.1,
        "precipitation_mm": 0.0,
        "haze": False,
        "notes": "ok2",
    }

    rv = client.post("/observations", json=[o1, o2], headers=authz)
    assert rv.status_code == 201, rv.get_json()
    body = rv.get_json()
    assert "created" in body and len(body["created"]) == 2
    created_ids = body["created"]

    # GET (filter by buoy_id, from date)
    frm = iso(now.replace(hour=0, minute=0, second=0, microsecond=0))
    rv = client.get(f"/observations?buoy_id={buoy_id}&from={frm}", headers=authz)
    assert rv.status_code == 200
    data = rv.get_json()
    assert "items" in data and data["count"] >= 2

    # GET one
    obs_id = created_ids[0]
    rv = client.get(f"/observations/{obs_id}", headers=authz)
    assert rv.status_code == 200
    one = rv.get_json()
    assert one["id"] == obs_id

    # PUT (replace) current quarter → allowed
    rv = client.put(
        f"/observations/{obs_id}",
        json={
            "buoy_id": buoy_id,
            "observed_at": iso(now.replace(microsecond=0)),
            "timezone": "UTC",
            "lat": 2.0,
            "lon": 2.0,
            "temp_c": 26.0,
            "humidity": 58,
            "wind_m_s": 2.8,
            "precipitation_mm": 0.0,
            "haze": False,
            "notes": "replaced",
        },
        headers=authz,
    )
    assert rv.status_code == 200
    assert rv.get_json()["notes"] == "replaced"

    # PATCH (partial) current quarter → allowed
    rv = client.patch(
        f"/observations/{obs_id}",
        json={"notes": "patched"},
        headers=authz,
    )
    assert rv.status_code == 200
    assert rv.get_json()["notes"] == "patched"

    # DELETE current quarter → allowed
    rv = client.delete(f"/observations/{obs_id}", headers=authz)
    assert rv.status_code == 204


def test_observations_quarter_lock(client, authz):
    # Create a buoy
    rv = client.post(
        "/buoys",
        json={"name": "BW-OLD", "lat": 0.0, "lon": 0.0, "status": "active"},
        headers=authz,
    )
    assert rv.status_code in (200, 201), rv.get_json()
    buoy_id = rv.get_json()["id"]

    # Create an observation in a PAST quarter (force a date well in the past year)
    past = dt.datetime(2025, 2, 15, 10, 0, 0, tzinfo=dt.timezone.utc)  # Q1 of 2025
    rv = client.post(
        "/observations",
        json=[{
            "buoy_id": buoy_id,
            "observed_at": past.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "timezone": "UTC",
            "lat": 0.1,
            "lon": 0.1,
            "temp_c": 20.0,
            "humidity": 50.0,
            "wind_m_s": 3.0,
            "precipitation_mm": 0.0,
            "haze": False,
            "notes": "old"
        }],
        headers=authz,
    )
    assert rv.status_code == 201, rv.get_json()
    past_id = rv.get_json()["created"][0]

    # PATCH should 409
    rv = client.patch(f"/observations/{past_id}", json={"notes": "should-fail"}, headers=authz)
    assert rv.status_code == 409
    assert "locked" in rv.get_json()["message"].lower()

    # DELETE should 409
    rv = client.delete(f"/observations/{past_id}", headers=authz)
    assert rv.status_code == 409

