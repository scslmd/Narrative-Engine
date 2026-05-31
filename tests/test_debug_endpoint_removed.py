def test_debug_endpoint_returns_404(tmp_path):
    """Debug endpoint should not exist."""
    from fastapi.testclient import TestClient
    from app.main import build_app
    client = TestClient(build_app())
    response = client.post('/projects/create/debug', json={'test': 'data'})
    assert response.status_code == 404
