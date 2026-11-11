"""
Lab 6 - Part 1: LINE (statement) coverage tests for cloud_storage_tier.py
Author : Madan P
SRN    : PEES1UG24AM374

Goal: execute every line of the module at least once (>= 90% line coverage).
Run  : coverage run -m pytest CodeCoverageTest_cloud_storage_tier.py
       coverage report -m
"""
import pytest
from cloud_storage_tier import process_storage_tenants, monitor_replication_latency


# ---------- process_storage_tenants ----------

def test_single_active_hot_tenant():
    tenants = [{
        "account_active": True, "tier": "hot", "has_backup_vault": False,
        "buckets": [{"size_gb": 100, "corrupted": False, "egress_gb": 50}],
    }]
    result = process_storage_tenants(tenants, 10.0)
    assert result["total_billed"] == 2.5
    assert result["status"] == "BILLED"


def test_invalid_input_raises_value_error():
    with pytest.raises(ValueError):
        process_storage_tenants("not-a-list", 5.0)


def test_inactive_account_is_skipped():
    tenants = [{"account_active": False, "tier": "hot",
                "buckets": [{"size_gb": 100}]}]
    result = process_storage_tenants(tenants, 5.0)
    assert result == {"total_billed": 0.0, "status": "ZERO_USAGE"}


def test_cool_tier_with_egress_and_backup_vault():
    # 200*0.015 = 3.0 ; egress (150-100)*0.08 = 4.0 ; vault fee = 5.0
    tenants = [{
        "account_active": True, "tier": "cool", "has_backup_vault": True,
        "buckets": [{"size_gb": 200, "corrupted": False, "egress_gb": 150}],
    }]
    result = process_storage_tenants(tenants, 5.0)
    assert result == {"total_billed": 12.0, "status": "BILLED"}


def test_archive_tier_large_bucket_discount():
    # 1000 * 0.005 * 0.90 = 4.5
    tenants = [{"account_active": True, "tier": "archive",
                "buckets": [{"size_gb": 1000}]}]
    result = process_storage_tenants(tenants, 0.0)
    assert result == {"total_billed": 4.5, "status": "BILLED"}


def test_archive_corrupted_bucket_breaks_and_zeroes_charge():
    tenants = [{"account_active": True, "tier": "archive",
                "buckets": [{"size_gb": 100}, {"size_gb": 100, "corrupted": True}]}]
    result = process_storage_tenants(tenants, 0.0)
    assert result == {"total_billed": 0.0, "status": "ZERO_USAGE"}


def test_hot_corrupted_bucket_adds_no_storage_charge():
    tenants = [{"account_active": True, "tier": "hot",
                "buckets": [{"size_gb": 100, "corrupted": True}]}]
    result = process_storage_tenants(tenants, 0.0)
    assert result["status"] == "ZERO_USAGE"


def test_unknown_tier_is_flagged_and_skipped():
    tenants = [{"account_active": True, "tier": "platinum",
                "buckets": [{"size_gb": 100}]}]
    result = process_storage_tenants(tenants, 0.0)
    assert result["status"] == "ZERO_USAGE"


def test_non_positive_bucket_size_is_flagged():
    tenants = [{"account_active": True, "tier": "hot",
                "buckets": [{"size_gb": 0}]}]
    result = process_storage_tenants(tenants, 0.0)
    assert result["status"] == "ZERO_USAGE"


def test_audit_flagged_when_more_than_four_flagged_buckets():
    tenants = [{"account_active": True, "tier": "hot",
                "buckets": [{"size_gb": 0}] * 5}]
    result = process_storage_tenants(tenants, 0.0)
    assert result["status"] == "AUDIT_FLAGGED"


# ---------- monitor_replication_latency ----------

def test_monitor_no_data():
    assert monitor_replication_latency([]) == "NO_DATA"


def test_monitor_sync_lag_alert():
    assert monitor_replication_latency([[100, 250, 300]]) == "SYNC_LAG_ALERT"


def test_monitor_synced():
    assert monitor_replication_latency([[100, 150], [90, 80]]) == "SYNCED"
