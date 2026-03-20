from pathlib import Path

from fastapi.testclient import TestClient

from app.main import build_app


def test_health_endpoint() -> None:
    client = TestClient(build_app())
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_projects_endpoint_lists_projects() -> None:
    client = TestClient(build_app())
    response = client.get('/projects')
    assert response.status_code == 200
    payload = response.json()
    names = {item['project_name'] for item in payload}
    assert 'Science Fantasy Test Project' in names
    assert 'Romance Test Project' in names


def test_models_endpoint_returns_workflow_preferences() -> None:
    client = TestClient(build_app())
    response = client.get('/models')
    assert response.status_code == 200
    payload = response.json()
    assert payload['workflow_order'] == ['architect', 'sequencer', 'drafter', 'critic']
    assert payload['default_critic_profile'] == 'minimal_context'


def test_role_model_checker_stub_runs() -> None:
    client = TestClient(build_app())
    response = client.post(
        '/role-model-checker/run',
        json={
            'roles': ['architect', 'critic'],
            'model_selection': {},
            'critic_profile': 'minimal_context',
            'save_report': True,
        },
    )
    assert response.status_code == 202
    payload = response.json()
    assert payload['status'] == 'PENDING'
    assert response.headers['Location'].endswith(f"/role-model-checker/{payload['run_id']}/status")

    status_response = client.get(f"/role-model-checker/{payload['run_id']}/status")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload['status'] == 'COMPLETED'
    assert len(status_payload['results']) == 2
    assert status_payload['report_path']
    assert Path(status_payload['report_path']).exists()


def test_job_stub_runs() -> None:
    client = TestClient(build_app())
    response = client.post('/jobs/create', json={'phase': 'P-100', 'payload': {'project_id': 'science-fantasy-test'}})
    assert response.status_code == 202
    payload = response.json()
    assert payload['status'] == 'PENDING'
    assert response.headers['Location'].endswith(f"/jobs/{payload['id']}/status")

    status_response = client.get(f"/jobs/{payload['id']}/status")
    assert status_response.status_code == 200
    assert status_response.json()['status'] == 'COMPLETED'
