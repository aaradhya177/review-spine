from scripts.simulate_webhook import run_demo


def test_local_demo_queues_review_job() -> None:
    result = run_demo()

    assert result["response"]["status"] == "queued"
    assert result["queued_jobs"][0]["repo_full_name"] == "acme/shop"
    assert result["queued_jobs"][0]["pull_request_number"] == 7

