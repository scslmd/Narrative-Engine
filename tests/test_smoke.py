from pathlib import Path
from time import sleep

import pytest
from fastapi.testclient import TestClient

from app.main import build_app

pytestmark = [
    pytest.mark.integration,
    pytest.mark.xdist_group(name="serial-smoke"),
]


def _create_project(client: TestClient, project_name: str) -> str:
    response = client.post('/projects/create', json={'project_name': project_name})
    assert response.status_code == 201
    return response.json()['project_id']


def _poll_json(client: TestClient, path: str, *, terminal_statuses: set[str], attempts: int = 12, delay_seconds: float = 0.2) -> dict:
    payload = {}
    for _ in range(attempts):
        response = client.get(path)
        assert response.status_code == 200
        payload = response.json()
        if payload['status'] in terminal_statuses:
            return payload
        sleep(delay_seconds)
    return payload


def test_health_endpoint() -> None:
    client = TestClient(build_app())
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_projects_endpoint_lists_projects() -> None:
    client = TestClient(build_app())
    first_project_id = _create_project(client, 'Smoke Science Fantasy Project')
    second_project_id = _create_project(client, 'Smoke Romance Project')

    response = client.get('/projects')
    assert response.status_code == 200
    payload = response.json()
    ids = {item['project_id'] for item in payload}
    assert first_project_id in ids
    assert second_project_id in ids


def test_models_endpoint_returns_workflow_preferences() -> None:
    client = TestClient(build_app())
    response = client.get('/models')
    assert response.status_code == 200
    payload = response.json()
    assert payload['workflow_order'] == ['architect', 'sequencer', 'drafter', 'critic']
    assert payload['default_critic_profile'] == 'minimal_context'


def test_role_model_checker_stub_runs() -> None:
    with TestClient(build_app()) as client:
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

        status_payload = _poll_json(
            client,
            f"/role-model-checker/{payload['run_id']}/status",
            terminal_statuses={'COMPLETED', 'FAILED'},
        )
        assert status_payload['status'] == 'COMPLETED'
        assert len(status_payload['results']) == 2
        assert status_payload['report_path']
        assert Path(status_payload['report_path']).exists()


def test_job_stub_runs() -> None:
    with TestClient(build_app()) as client:
        project_id = _create_project(client, 'Smoke Job Project')
        response = client.post('/jobs/create', json={'phase': 'P-100', 'payload': {'project_id': project_id}})
        assert response.status_code == 202
        payload = response.json()
        assert payload['status'] == 'PENDING'
        assert response.headers['Location'].endswith(f"/jobs/{payload['id']}/status")

        status_payload = _poll_json(
            client,
            f"/jobs/{payload['id']}/status",
            terminal_statuses={'COMPLETED', 'FAILED'},
        )
        assert status_payload['status'] == 'COMPLETED'
