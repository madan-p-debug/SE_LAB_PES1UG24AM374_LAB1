"""
Lab 6 - Part 2: BRANCH coverage tests for cloud_storage_tier.py
Author : Madan P
SRN    : PEES1UG24AM374

Goal: make every decision evaluate to BOTH True and False (>= 90% branch coverage),
including loop-entered / loop-skipped and boundary values (500, 100, 200, 4).
Run  : coverage run --branch -m pytest BranchCoverageTest_cloud_storage_tier.py
       coverage report -m
"""
import pytest
from cloud_storage_tier import process_storage_tenants, monitor_replication_latency


def tenant(tier="hot", buckets=None, vault=False, active=True):
    return {"account_active": active, "tier": tier,
            "has_backup_vault": vault, "buckets": buckets or []}


# ======== process_storage_tenants : input validation ========

def test_single_active_hot_tenant():
    t = [tenant("hot", [{"size_gb": 100, "corrupted": False, "egress_gb": 50}])]
    result = process_storage_tenants(t, 10.0)
    assert result["total_billed"] == 2.5
    assert result["status"] == "BILLED"


def test_tenants_not_a_list_raises():                 # isinstance(...) False
    with pytest.raises(ValueError):
        process_storage_tenants({"a": 1}, 5.0)


def test_negative_support_fee_raises():               # list OK, fee < 0 True
    with pytest.raises(ValueError):
        process_storage_tenants([], -1.0)


def test_zero_support_fee_is_valid():                 # fee < 0 False (boundary)
    assert process_storage_tenants([], 0.0)["status"] == "ZERO_USAGE"


def test_empty_tenant_list_skips_loop():              # outer for: zero iterations
    assert process_storage_tenants([], 5.0) == {"total_billed": 0.0, "status": "ZERO_USAGE"}


# ======== account_active / defaults ========

def test_inactive_account_skipped():                  # account_active False -> continue
    t = [tenant("hot", [{"size_gb": 100}], active=False)]
    assert process_storage_tenants(t, 5.0)["status"] == "ZERO_USAGE"


def test_missing_account_active_key_defaults_to_inactive():
    t = [{"tier": "hot", "buckets": [{"size_gb": 100}]}]
    assert process_storage_tenants(t, 5.0)["status"] == "ZERO_USAGE"


def test_missing_tier_defaults_to_hot_and_missing_buckets_ok():
    t = [{"account_active": True, "buckets": [{"size_gb": 200}]}]   # default hot
    assert process_storage_tenants(t, 0.0) == {"total_billed": 5.0, "status": "BILLED"}


# ======== tier selection (if / elif / elif / else) ========

def test_cool_tier_rate():
    t = [tenant("cool", [{"size_gb": 100}])]
    assert process_storage_tenants(t, 0.0)["total_billed"] == 1.5


def test_archive_tier_rate():
    t = [tenant("archive", [{"size_gb": 100}])]
    assert process_storage_tenants(t, 0.0)["total_billed"] == 0.5


def test_unknown_tier_flagged_and_skipped():
    t = [tenant("platinum", [{"size_gb": 100}])]
    assert process_storage_tenants(t, 0.0)["status"] == "ZERO_USAGE"


# ======== bucket loop & size checks ========

def test_tenant_with_no_buckets_skips_inner_loop():   # inner for: zero iterations
    t = [tenant("hot", [], vault=True)]
    assert process_storage_tenants(t, 7.5) == {"total_billed": 7.5, "status": "BILLED"}


def test_bucket_size_zero_flagged():                  # size_gb <= 0 True (boundary)
    t = [tenant("hot", [{"size_gb": 0}])]
    assert process_storage_tenants(t, 0.0)["status"] == "ZERO_USAGE"


def test_bucket_size_negative_flagged():
    t = [tenant("hot", [{"size_gb": -10}])]
    assert process_storage_tenants(t, 0.0)["status"] == "ZERO_USAGE"


def test_bucket_missing_size_defaults_to_zero_and_flagged():
    t = [tenant("hot", [{}])]
    assert process_storage_tenants(t, 0.0)["status"] == "ZERO_USAGE"


def test_size_exactly_500_gets_no_discount():         # size_gb > 500 False (boundary)
    t = [tenant("hot", [{"size_gb": 500}])]
    assert process_storage_tenants(t, 0.0)["total_billed"] == 12.5


def test_size_over_500_gets_ten_percent_discount():   # size_gb > 500 True
    t = [tenant("hot", [{"size_gb": 1000}])]
    assert process_storage_tenants(t, 0.0)["total_billed"] == 22.5


# ======== corrupted buckets ========

def test_corrupted_archive_bucket_breaks_and_resets_charge():
    t = [tenant("archive", [{"size_gb": 100}, {"size_gb": 100, "corrupted": True},
                            {"size_gb": 100}])]       # 3rd bucket never reached
    assert process_storage_tenants(t, 0.0) == {"total_billed": 0.0, "status": "ZERO_USAGE"}


def test_corrupted_archive_still_pays_backup_vault_fee():
    t = [tenant("archive", [{"size_gb": 100, "corrupted": True}], vault=True)]
    assert process_storage_tenants(t, 3.0) == {"total_billed": 3.0, "status": "BILLED"}


def test_corrupted_hot_bucket_no_break_continues_to_next_bucket():
    t = [tenant("hot", [{"size_gb": 100, "corrupted": True}, {"size_gb": 100}])]
    assert process_storage_tenants(t, 0.0)["total_billed"] == 2.5


def test_corrupted_hot_bucket_still_pays_egress():    # corrupted + egress > 100
    t = [tenant("hot", [{"size_gb": 100, "corrupted": True, "egress_gb": 150}])]
    assert process_storage_tenants(t, 0.0)["total_billed"] == 4.0


# ======== egress ========

def test_egress_exactly_100_not_charged():            # egress_gb > 100 False (boundary)
    t = [tenant("hot", [{"size_gb": 100, "egress_gb": 100}])]
    assert process_storage_tenants(t, 0.0)["total_billed"] == 2.5


def test_egress_over_100_charged():                   # egress_gb > 100 True
    t = [tenant("hot", [{"size_gb": 100, "egress_gb": 200}])]
    assert process_storage_tenants(t, 0.0)["total_billed"] == 10.5   # 2.5 + 100*0.08


# ======== backup vault ========

def test_backup_vault_fee_added():
    t = [tenant("cool", [{"size_gb": 100}], vault=True)]
    assert process_storage_tenants(t, 10.0)["total_billed"] == 11.5


def test_backup_vault_fee_not_added_when_false():
    t = [tenant("cool", [{"size_gb": 100}], vault=False)]
    assert process_storage_tenants(t, 10.0)["total_billed"] == 1.5


# ======== final status ========

def test_four_flagged_buckets_is_not_audit_flagged():  # flagged > 4 False (boundary)
    t = [tenant("hot", [{"size_gb": 0}] * 4 + [{"size_gb": 100}])]
    assert process_storage_tenants(t, 0.0) == {"total_billed": 2.5, "status": "BILLED"}


def test_five_flagged_buckets_is_audit_flagged():     # flagged > 4 True (boundary)
    t = [tenant("hot", [{"size_gb": 0}] * 5)]
    assert process_storage_tenants(t, 0.0)["status"] == "AUDIT_FLAGGED"


def test_audit_flagged_takes_priority_over_billed():
    t = [tenant("hot", [{"size_gb": 0}] * 5 + [{"size_gb": 100}])]
    assert process_storage_tenants(t, 0.0) == {"total_billed": 2.5, "status": "AUDIT_FLAGGED"}


def test_multiple_tenants_are_summed():
    t = [tenant("hot", [{"size_gb": 100}]), tenant("cool", [{"size_gb": 100}]),
         tenant("archive", [{"size_gb": 100}])]
    assert process_storage_tenants(t, 0.0) == {"total_billed": 4.5, "status": "BILLED"}


# ======== monitor_replication_latency ========

def test_monitor_empty_matrix_no_data():
    assert monitor_replication_latency([]) == "NO_DATA"


def test_monitor_none_matrix_no_data():
    assert monitor_replication_latency(None) == "NO_DATA"


def test_monitor_node_with_no_logs_is_synced():       # inner for: zero iterations
    assert monitor_replication_latency([[]]) == "SYNCED"


def test_monitor_all_latencies_low_synced():
    assert monitor_replication_latency([[10, 20, 30], [50, 60]]) == "SYNCED"


def test_monitor_latency_exactly_200_is_not_lag():    # latency > 200 False (boundary)
    assert monitor_replication_latency([[200, 200, 200]]) == "SYNCED"


def test_monitor_single_spike_is_not_alert():         # streak 1 -> < 2
    assert monitor_replication_latency([[250, 100]]) == "SYNCED"


def test_monitor_streak_resets_between_spikes():      # else branch resets streak
    assert monitor_replication_latency([[250, 100, 250, 100, 250]]) == "SYNCED"


def test_monitor_two_consecutive_spikes_alert():      # streak >= 2 True
    assert monitor_replication_latency([[100, 250, 300]]) == "SYNC_LAG_ALERT"


def test_monitor_alert_on_later_node():
    assert monitor_replication_latency([[10, 20], [500, 500]]) == "SYNC_LAG_ALERT"


def test_monitor_streak_does_not_carry_across_nodes():
    assert monitor_replication_latency([[10, 250], [250, 10]]) == "SYNCED"
