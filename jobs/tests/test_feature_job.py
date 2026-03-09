from jobs.pyspark.feature_job import build_feature_rows


def test_build_feature_rows_counts() -> None:
    rows = [
        {"dt": "2026-03-06", "tenant_id": "T1", "event_type": "click"},
        {"dt": "2026-03-06", "tenant_id": "T1", "event_type": "purchase"},
        {"dt": "2026-03-06", "tenant_id": "T2", "event_type": "click"},
    ]

    out = build_feature_rows(rows)

    assert out == [
        {
            "dt": "2026-03-06",
            "tenant_id": "T1",
            "event_count": 2,
            "purchase_count": 1,
            "click_count": 1,
        },
        {
            "dt": "2026-03-06",
            "tenant_id": "T2",
            "event_count": 1,
            "purchase_count": 0,
            "click_count": 1,
        },
    ]
