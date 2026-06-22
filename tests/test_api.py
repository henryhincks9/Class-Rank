import os
import tempfile
import json
import pytest
import server as app_server
from server import app, init_db, get_db

@pytest.fixture(scope='function')
def client():
    # Reset the default DB file so tests run on a clean database
    with app.app_context():
        app_server.sa_db.session.remove()
        try:
            app_server.sa_db.engine.dispose()
        except Exception:
            pass
        try:
            conn = app_server.get_db()
            for table in ("reviews", "users", "migrations"):
                try:
                    conn.execute(f"DELETE FROM {table}")
                except Exception:
                    pass
            conn.commit()
            conn.close()
        except Exception:
            pass
        init_db()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_register_login_logout(client):
    username = 'testuser1'
    password = 'password123'
    # Register
    rv = client.post('/api/register', json={'username': username, 'email': 'testuser1@go.dsdmail.net', 'password': password})
    # OK if created or already exists
    assert rv.status_code in (200, 201, 400)

    # Login by username
    rv = client.post('/api/login', json={'username': username, 'password': password})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['user']['username'] == username
    assert data['user']['email'] == 'testuser1@go.dsdmail.net'

    # Login by email
    rv = client.post('/api/login', json={'username': 'testuser1@go.dsdmail.net', 'password': password})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['user']['username'] == username

    # Logout
    rv = client.get('/api/logout')
    assert rv.status_code == 200


def test_post_and_get_review(client):
    # login as admin
    rv = client.post('/api/login', json={'username': 'admin', 'password': 'admin123'})
    assert rv.status_code == 200

    # post review
    rv = client.post('/api/reviews', json={'courseId': 1030, 'difficulty': 3, 'enjoyment': 4, 'workload': 2, 'review': 'pytest review'})
    assert rv.status_code == 201
    data = rv.get_json()
    assert 'id' in data

    # get reviews
    rv = client.get('/api/reviews?courseId=1030')
    assert rv.status_code == 200
    arr = rv.get_json()
    assert isinstance(arr, list)


def test_admin_user_listing_and_role_change(client):
    # login as admin
    rv = client.post('/api/login', json={'username': 'admin', 'password': 'admin123'})
    assert rv.status_code == 200

    # list users
    rv = client.get('/api/admin/users')
    assert rv.status_code == 200
    users = rv.get_json()
    assert isinstance(users, list)

    # pick a user (create one first)
    rv = client.post('/api/register', json={'username': 'promote_me', 'email': 'promote_me@go.dsdmail.net', 'password': 'password123'})
    # OK if created or already exists
    assert rv.status_code in (200, 201, 400)

    # promote to teacher
    # ensure admin session remains by logging back in
    rv = client.post('/api/login', json={'username': 'admin', 'password': 'admin123'})
    assert rv.status_code == 200
    # find the user's id
    rv = client.get('/api/admin/users')
    users = rv.get_json()
    target = next((u for u in users if u['username'] == 'promote_me'), None)
    assert target is not None
    uid = target['id']

    rv = client.post(f'/api/admin/users/{uid}/role', json={'role': 'teacher'})
    assert rv.status_code == 200


def test_flag_and_delete_review(client):
    # create and login as regular user, then post a review
    rv = client.post('/api/register', json={'username': 'promote_me', 'email': 'promote_me@go.dsdmail.net', 'password': 'password123'})
    assert rv.status_code in (200, 201)
    rv = client.post('/api/login', json={'username': 'promote_me', 'password': 'password123'})
    assert rv.status_code == 200
    rv = client.post('/api/reviews', json={'courseId': 1030, 'difficulty': 3, 'enjoyment': 3, 'workload': 3, 'review': 'to be flagged'})
    assert rv.status_code == 201
    rid = rv.get_json().get('id')

    # flag the review
    rv = client.post(f'/api/reviews/{rid}/flag')
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'flagged' in data

    # admin deletes the review
    rv = client.post('/api/login', json={'username': 'admin', 'password': 'admin123'})
    assert rv.status_code == 200
    rv = client.delete(f'/api/reviews/{rid}')
    assert rv.status_code == 200

def test_invalid_school_email_registration(client):
    rv = client.post('/api/register', json={
        'username': 'invalid_email_user',
        'email': 'user@example.com',
        'password': 'password123'
    })
    assert rv.status_code == 400
    data = rv.get_json()
    assert 'Davis School District' in data.get('message', '')


def test_health(client):
    rv = client.get('/api/health')
    assert rv.status_code == 200
    assert rv.get_json().get('status') == 'ok'
