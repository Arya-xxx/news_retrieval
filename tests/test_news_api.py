import pytest
from app import create_app
from app.db.mongodb import get_db

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_category_endpoint(client):
    response = client.get('/api/v1/news/category?name=Technology')
    assert response.status_code == 200
    assert 'articles' in response.json