def test_send_email_ok(notification_client):
    headers = {"Authorization": "Bearer mi-token-secreto"}
    data = {"email": "test@mail.com", "message": "Hola"}

    response = notification_client.post("/notification/send-email", json=data, headers=headers)
    assert response.status_code == 201

def test_send_email_missing_token(notification_client):
    data = {"email": "test@mail.com", "message": "Hola"}
    response = notification_client.post("/notification/send-email", json=data)
    assert response.status_code == 401

def test_send_email_wrong_token(notification_client):
    headers = {"Authorization": "Bearer token-incorrecto"}
    data = {"email": "test@mail.com", "message": "Hola"}
    response = notification_client.post("/notification/send-email", json=data, headers=headers)
    assert response.status_code == 401