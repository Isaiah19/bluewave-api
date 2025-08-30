def test_buoys_crud_flow(client, authz):
    # Create
    rv = client.post(
        "/buoys",
        json={"name": "BW-TEST-01", "lat": 6.43, "lon": 3.41, "status": "active"},
        headers=authz,
    )
    assert rv.status_code == 201, rv.get_json()
    created = rv.get_json()
    buoy_id = created["id"]
    assert created["name"] == "BW-TEST-01"

    # List
    rv = client.get("/buoys?q=BW-", headers=authz)
    assert rv.status_code == 200
    items = rv.get_json()
    assert any(b["id"] == buoy_id for b in items)

    # Get by id
    rv = client.get(f"/buoys/{buoy_id}", headers=authz)
    assert rv.status_code == 200
    assert rv.get_json()["id"] == buoy_id

    # PUT (replace)
    rv = client.put(
        f"/buoys/{buoy_id}",
        json={"name": "BW-TEST-01", "lat": 6.50, "lon": 3.50, "status": "maintenance"},
        headers=authz,
    )
    assert rv.status_code == 200
    assert rv.get_json()["status"] == "maintenance"

    # PATCH (partial)
    rv = client.patch(
        f"/buoys/{buoy_id}",
        json={"status": "inactive"},
        headers=authz,
    )
    assert rv.status_code == 200
    assert rv.get_json()["status"] == "inactive"

    # DELETE
    rv = client.delete(f"/buoys/{buoy_id}", headers=authz)
    assert rv.status_code == 204

    # Ensure gone
    rv = client.get(f"/buoys/{buoy_id}", headers=authz)
    assert rv.status_code == 404

