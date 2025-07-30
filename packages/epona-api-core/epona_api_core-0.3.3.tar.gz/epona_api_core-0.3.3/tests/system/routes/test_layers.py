import json


def test_save_geometry(test_app_with_db, access_token, monkeypatch):
    headers = {"Authorization": f"Bearer {access_token}", "accept": "application/json"}

    payload = {
        "id_entidade": "a12345678-123",
        "entidade": "unidade",
        "coords": '{"type":"Point","coordinates":[-48.23456, 20.12345]}',
        "tipo_geom": "ponto",
    }

    resp = test_app_with_db.post("/layers/save-geometry", json=payload, headers=headers)

    assert resp.status_code == 201


def test_get_geometrias(test_app_with_db, access_token, monkeypatch):
    headers = {"Authorization": f"Bearer {access_token}", "accept": "application/json"}
    payload = {
        "id": "b12345678-123",
        "id_entidade": "c12345678-123",
        "entidade": "entidade",
        "coords": '{"type":"Point","coordinates":[-48.23456, 20.12345]}',
        "tipo_geom": "ponto",
    }

    test_app_with_db.post("/layers/save-geometry", json=payload, headers=headers)

    resp = test_app_with_db.post(
        "/layers/get-geometries", json=payload, headers=headers
    )

    assert resp.status_code == 200
