def test_policy_lists_ready_runs(policy):
    text = policy.get("/policy/runs").text
    assert "20261112-01" in text and "20261109-01" in text
    assert "20261111-01" not in text


def test_policy_home_is_request_list(client):
    from tests.conftest import login

    assert login(client, "policy01", "pw-policy").headers["location"] == "/policy/analyses"


def test_new_analysis_form_lists_runs_and_templates(policy):
    text = policy.get("/policy/analyses/new?run_id=20261109-01").text
    assert '<option value="20261109-01" selected>' in text
    assert "위기가구 지원 연계율" in text and "기초생활보장 수급 현황" in text


def test_params_fragment_follows_template(policy):
    res = policy.get("/policy/analyses/new/params?scenario=basic_living_status", headers={"HX-Request": "true"})
    assert "<html" not in res.text
    assert "가구 유형" in res.text and "위기정보 유형" not in res.text


def test_security_run_status(security):
    text = security.get("/security/runs").text
    assert text.count("반출 완료") >= 2
    assert "격리" in text and "중단" in text


def test_aborted_run_has_no_export(security):
    text = security.get("/security/runs/20261111-01").text
    assert "k-익명성" in text
    assert "반출하지 않았습니다" in text


def test_failures_counts_reasons(security):
    text = security.get("/security/failures").text
    assert "k-익명성" in text and "직접식별자 잔존" in text and "전화번호" in text
