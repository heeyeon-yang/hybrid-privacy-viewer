import pytest


@pytest.mark.parametrize("path", ["/security/runs", "/security/runs/20261109-01", "/security/failures"])
def test_policy_cannot_open_security_pages(policy, path):
    assert policy.get(path).status_code == 403


@pytest.mark.parametrize("path", ["/policy/runs", "/policy/runs/20261112-01/scenarios/1"])
def test_security_cannot_open_policy_pages(security, path):
    assert security.get(path).status_code == 403


@pytest.mark.parametrize("run_id", ["..", "20261112-01..", "x" * 11])
def test_bad_run_id_is_404(security, run_id):
    assert security.get(f"/security/runs/{run_id}").status_code == 404
