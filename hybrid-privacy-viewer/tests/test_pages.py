def test_policy_lists_only_finished_runs(policy):
    text = policy.get("/policy/runs").text
    assert "20261112-01" in text and "20261109-01" in text
    assert "20261111-01" not in text


def test_scenario_filter_returns_partial(policy):
    url = "/policy/runs/20261112-01/scenarios/1?region=서울 노원구"
    full = policy.get(url)
    part = policy.get(url, headers={"HX-Request": "true"})
    assert full.status_code == part.status_code == 200
    assert "<html" in full.text and "<html" not in part.text
    assert "서울 노원구" in part.text and "서울 강서구" not in part.text


def test_scenario2_renders(policy):
    assert "기초생활보장" in policy.get("/policy/runs/20261112-01/scenarios/2").text


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
