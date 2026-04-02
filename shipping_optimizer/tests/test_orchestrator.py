"""
====================
Full integration test for the multi-agent liner shipping optimization pipeline.

Pipeline under test:
  OrchestratorAgent
    → PortClustering + RegionalSplitter  (problem decomposition)
    → RegionalAgent × 3  (Asia / Europe / Americas)
        → ServiceGeneratorAgent           (candidate service pool)
        → HierarchicalGA                  (service selection)
        → HubMILP × N clusters            (flow optimisation)
        → LLM strategy + explanation      (qualitative analysis)
    → aggregate_results                   (global roll-up)
    → LLM executive summary              (orchestrator synthesis)

Run:
    python -m tests.test_orchestrator
    pytest tests/test_orchestrator.py -v
"""

import json
import sys
import time
import re
from pathlib import Path
from typing import Dict, Any, List

# ── Path setup ─────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.network_loader import NetworkLoader
from src.agents.orchestrator_agent import OrchestratorAgent
from src.optimization.data import Problem, Port, Service, Demand


# ===========================================================================
# ANSI helpers (work on Windows with modern terminal / VSCode)
# ===========================================================================
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    DIM    = "\033[2m"

def ok(msg: str)   -> str: return f"{C.GREEN}✓{C.RESET}  {msg}"
def fail(msg: str) -> str: return f"{C.RED}✗{C.RESET}  {msg}"
def warn(msg: str) -> str: return f"{C.YELLOW}⚠{C.RESET}  {msg}"
def hdr(msg: str)  -> str: return f"\n{C.BOLD}{C.CYAN}{msg}{C.RESET}"
def sep(char="─", n=70) -> str: return char * n


# ===========================================================================
# Assertion helpers
# ===========================================================================

_PASS = _FAIL = _WARN = 0

def assert_true(condition: bool, label: str, detail: str = "") -> bool:
    global _PASS, _FAIL
    if condition:
        _PASS += 1
        print(f"  {ok(label)}")
        return True
    else:
        _FAIL += 1
        msg = f"  {fail(label)}"
        if detail:
            msg += f"\n      {C.DIM}{detail}{C.RESET}"
        print(msg)
        return False

def assert_gt(value, threshold, label: str) -> bool:
    return assert_true(
        value > threshold,
        label,
        f"Expected > {threshold:,}  |  Got: {value:,}"
    )

def assert_ge(value, threshold, label: str) -> bool:
    return assert_true(
        value >= threshold,
        label,
        f"Expected >= {threshold}  |  Got: {value}"
    )

def assert_range(value, lo, hi, label: str) -> bool:
    return assert_true(
        lo <= value <= hi,
        label,
        f"Expected [{lo}, {hi}]  |  Got: {value}"
    )

def assert_contains(text: str, keyword: str, label: str) -> bool:
    return assert_true(
        keyword.lower() in text.lower(),
        label,
        f"Expected '{keyword}' in output"
    )

def assert_has_number(text: str, label: str) -> bool:
    return assert_true(
        bool(re.search(r"\d{2,}", text)),
        label,
        "LLM output must contain at least one number with 2+ digits"
    )

def warn_if(condition: bool, label: str):
    global _WARN
    if condition:
        _WARN += 1
        print(f"  {warn(label)}")


# ===========================================================================
# Problem loader
# ===========================================================================

def load_problem(filename: str) -> Problem:
    with open(filename) as f:
        data = json.load(f)
    ports    = [Port(**p)    for p in data["ports"]]
    services = [Service(**s) for s in data["services"]]
    demands  = [Demand(**d)  for d in data["demands"]]
    DEMAND_SCALE = 6
    for d in demands:
        d.weekly_teu *= DEMAND_SCALE
    loader   = NetworkLoader()
    distance_matrix = loader.load_distance_matrix()
    return Problem(
        ports=ports,
        services=services,
        demands=demands,
        distance_matrix=distance_matrix,
    )


# ===========================================================================
# Display helpers
# ===========================================================================

def print_kv(label: str, value: str, width: int = 26):
    """Print a key-value line, label left-padded to width."""
    print(f"  {C.DIM}{label:<{width}}{C.RESET}{value}")

def print_table_row(cells: List[str], widths: List[int], bold_first: bool = False):
    parts = []
    for i, (cell, w) in enumerate(zip(cells, widths)):
        if i == 0 and bold_first:
            parts.append(f"{C.BOLD}{cell:<{w}}{C.RESET}")
        else:
            parts.append(f"{cell:<{w}}")
    print("  " + "  ".join(parts))

def print_section_header(title: str):
    print(hdr(title))
    print(f"  {sep()}")


# ===========================================================================
# Section 1 — Problem statistics
# ===========================================================================

def section_problem_stats(problem: Problem) -> Dict[str, Any]:
    print_section_header("1 · PROBLEM STATISTICS")

    total_demand   = sum(d.weekly_teu for d in problem.demands)
    num_ports      = len(problem.ports)
    num_services   = len(problem.services)
    num_lanes      = len(problem.demands)
    avg_demand     = total_demand / num_lanes if num_lanes else 0
    density        = num_lanes / (num_ports * (num_ports - 1) / 2) * 100 \
                     if num_ports > 1 else 0

    top5 = sorted(problem.demands, key=lambda d: d.weekly_teu, reverse=True)[:5]
    top3_teu   = sum(d.weekly_teu for d in top5[:3])
    top3_share = top3_teu / total_demand * 100 if total_demand else 0

    print_kv("Ports",              f"{num_ports:,}")
    print_kv("Candidate services", f"{num_services:,}")
    print_kv("Demand lanes",       f"{num_lanes:,}")
    print_kv("Total weekly demand",f"{total_demand:,.0f} TEU")
    print_kv("Avg demand/lane",    f"{avg_demand:,.1f} TEU")
    print_kv("Network density",    f"{density:.1f}%")
    print_kv("Top-3 corridor share",f"{top3_share:.1f}% of total demand")

    print(f"\n  {'#':<4} {'Origin':>8} {'Destination':>12} {'TEU/week':>12}  {'Share':>8}")
    print(f"  {sep('-', 50)}")
    for i, d in enumerate(top5, 1):
        share = d.weekly_teu / total_demand * 100
        print(f"  {i:<4} {d.origin:>8} {d.destination:>12} "
              f"{d.weekly_teu:>12,.0f}  {share:>7.1f}%")

    print(f"\n  {sep()}")
    assert_gt(num_ports,   0,  "Ports loaded")
    assert_gt(num_lanes,   0,  "Demand lanes loaded")
    assert_gt(total_demand, 0, "Total demand > 0 TEU")
    assert_gt(num_services, 0, "Candidate services loaded")
    warn_if(density < 5,  f"Network density {density:.1f}% — sparse network")
    warn_if(top3_share > 60, f"Top-3 share {top3_share:.1f}% — highly concentrated demand")

    return {
        "total_demand":  total_demand,
        "num_ports":     num_ports,
        "num_lanes":     num_lanes,
        "num_services":  num_services,
        "density":       density,
        "top3_share":    top3_share,
        "top5":          top5,
    }


# ===========================================================================
# Section 2 — Problem analysis (LLM output)
# ===========================================================================

def section_problem_analysis(result: Dict, stats: Dict):
    print_section_header("2 · PROBLEM ANALYSIS  (Orchestrator LLM)")

    analysis = result.get("problem_analysis", "")
    print(analysis)
    print(f"\n  {sep()}")

    assert_true(len(analysis) > 80, "Analysis is non-trivial (>80 chars)")
    assert_true(
        any(kw in analysis for kw in ("Small", "Medium", "Large")),
        "Analysis contains size classification",
    )
    assert_has_number(analysis, "Analysis cites at least one specific number")
    assert_true(
        any(kw in analysis.lower() for kw in
            ("port", "lane", "demand", "teu", "service", "density", "corridor")),
        "Analysis references domain-specific terms",
    )

    # Check that the size label is correct
    num_ports = stats["num_ports"]
    expected  = "Large" if num_ports > 200 else "Medium" if num_ports > 50 else "Small"
    assert_contains(analysis, expected, f"Size classification is '{expected}' for {num_ports} ports")

    # Check it's not the fallback boilerplate
    warn_if(
        "LLM analysis unavailable" in analysis,
        "Analysis fell back to static text — LLM call may have failed",
    )


# ===========================================================================
# Section 3 — Regional agent results
# ===========================================================================

def section_regional_results(result: Dict, stats: Dict):
    print_section_header("3 · REGIONAL AGENT RESULTS")

    regional_results: List[Dict] = result.get("regional_results", [])

    assert_ge(len(regional_results), 1, f"At least 1 regional agent returned a result")

    # ── Per-region table ─────────────────────────────────────────────────────
    cols   = ["Region", "Services", "Profit/wk", "Coverage", "Cost/wk",
              "Margin%", "$/svc/wk", "Uncov TEU"]
    widths = [12, 10, 14, 10, 14, 8, 10, 12]

    print(f"\n  {sep()}")
    print_table_row(cols, widths, bold_first=True)
    print(f"  {sep()}")

    for r in regional_results:
        region   = r.get("region", "?")
        svcs     = r.get("services_selected", 0)
        profit   = r.get("weekly_profit", 0)
        cov      = r.get("coverage_percent", 0)
        cost     = r.get("operating_cost", 0)
        margin   = r.get("profit_margin_pct",
                         round(profit / (profit + cost) * 100, 1) if (profit + cost) > 0 else 0)
        pps      = r.get("profit_per_service",
                         round(profit / svcs, 0) if svcs else 0)
        uncov    = r.get("uncovered_teu",
                         stats["total_demand"] * (100 - cov) / 100)

        print_table_row([
            region,
            f"{svcs:,}",
            f"${profit:,.0f}",
            f"{cov:.1f}%",
            f"${cost:,.0f}",
            f"{margin:.1f}%",
            f"${pps:,.0f}",
            f"{uncov:,.0f}",
        ], widths)

    print(f"  {sep()}")

    # ── Per-region assertions ────────────────────────────────────────────────
    for r in regional_results:
        region = r.get("region", "?")
        profit = r.get("weekly_profit", 0)
        cov    = r.get("coverage_percent", 0)
        svcs   = r.get("services_selected", 0)
        cost   = r.get("operating_cost", 0)
        annual = r.get("annual_profit", profit * 52)

        print(f"\n  {C.BOLD}── {region} ──{C.RESET}")

        assert_gt(profit, 0, f"[{region}] Weekly profit > 0")
        assert_gt(svcs,   0, f"[{region}] Services selected > 0")
        assert_range(cov, 0, 100, f"[{region}] Coverage in [0, 100]%")
        assert_true(
            abs(annual - profit * 52) < profit * 0.01 + 1,
            f"[{region}] Annual profit ≈ weekly × 52",
            f"annual={annual:,.0f}  weekly×52={profit*52:,.0f}",
        )
        warn_if(cov < 10, f"[{region}] Coverage {cov:.1f}% is very low (<10%)")
        warn_if(cov > 80, f"[{region}] Coverage {cov:.1f}% is unusually high (>80%)")
        warn_if(svcs == 0, f"[{region}] No services selected — GA may have failed")

        # ── Strategy output quality ────────────────────────────────────
        strategy = r.get("strategy", "")
        print(f"\n  {C.DIM}Strategy output:{C.RESET}")
        # Indent each line
        for line in strategy.strip().splitlines():
            print(f"    {line}")

        assert_true(len(strategy) > 30, f"[{region}] Strategy output is non-trivial")
        assert_has_number(strategy, f"[{region}] Strategy cites specific numbers")
        assert_true(
            any(kw in strategy for kw in ("hub_and_spoke", "direct", "hybrid", "A", "B", "C")),
            f"[{region}] Strategy contains strategy label",
        )
        assert_true(
            any(kw in strategy.lower() for kw in ("reason", "port", "teu", "demand", "corridor")),
            f"[{region}] Strategy references shipping domain terms",
        )
        # Check for vague language (should NOT be present)
        vague = ["consider", "explore", "may ", "could potentially", "perhaps"]
        has_vague = any(v in strategy.lower() for v in vague)
        assert_true(not has_vague, f"[{region}] Strategy avoids vague language")

        # ── Explanation output quality ─────────────────────────────────
        explanation = r.get("explanation", "")
        print(f"\n  {C.DIM}Explanation output:{C.RESET}")
        for line in explanation.strip().splitlines():
            print(f"    {line}")

        assert_true(len(explanation) > 60, f"[{region}] Explanation is non-trivial")
        assert_has_number(explanation, f"[{region}] Explanation cites specific numbers")
        assert_true(
            any(kw in explanation for kw in ("Verdict:", "Good", "Moderate", "Poor")),
            f"[{region}] Explanation contains verdict",
        )
        assert_true(
            any(kw in explanation for kw in
                ("Strength", "Weakness", "Improvement", "Action")),
            f"[{region}] Explanation has structured sections",
        )
        has_vague_exp = any(v in explanation.lower() for v in vague)
        assert_true(not has_vague_exp, f"[{region}] Explanation avoids vague language")

        # ── New fields added by hardened agent ─────────────────────────
        print(f"\n  {C.DIM}Hardened-agent fields:{C.RESET}")
        for field, label in [
            ("profit_margin_pct",  "Profit margin %"),
            ("profit_per_service", "Profit per service"),
            ("cost_per_service",   "Cost per service"),
            ("uncovered_teu",      "Uncovered TEU"),
            ("hub_ports",          "Hub port IDs"),
        ]:
            value = r.get(field)
            present = value is not None and (not isinstance(value, list) or len(value) > 0)
            assert_true(present, f"[{region}] {label} present in result")
            if present:
                print_kv(f"  {label}", str(value))


# ===========================================================================
# Section 4 — Global aggregated metrics
# ===========================================================================

def section_global_metrics(result: Dict, stats: Dict):
    print_section_header("4 · GLOBAL AGGREGATED METRICS")

    metrics = result["summary_metrics"]

    weekly_profit  = float(metrics["weekly_profit"])
    annual_profit  = float(metrics["annual_profit"])
    weekly_cost    = float(metrics["cost"])
    coverage       = float(metrics["coverage"])
    total_services = metrics["total_services"]

    # Derived
    profit_margin   = weekly_profit / (weekly_profit + weekly_cost) * 100 \
                      if (weekly_profit + weekly_cost) > 0 else 0
    profit_per_svc  = weekly_profit / total_services if total_services else 0
    cost_per_svc    = weekly_cost   / total_services if total_services else 0
    uncovered_teu   = stats["total_demand"] * (100 - coverage) / 100
    uncovered_pct   = 100 - coverage

    print_kv("Services deployed",   f"{total_services:,}")
    print_kv("Weekly profit",       f"${weekly_profit:,.0f}")
    print_kv("Annual profit",       f"${annual_profit:,.0f}")
    print_kv("Weekly operating cost",f"${weekly_cost:,.0f}")
    print_kv("Profit margin",       f"{profit_margin:.1f}%")
    print_kv("Profit per service",  f"${profit_per_svc:,.0f}/wk")
    print_kv("Cost per service",    f"${cost_per_svc:,.0f}/wk")
    print_kv("Demand coverage",     f"{coverage:.1f}%")
    print_kv("Uncovered demand",    f"{uncovered_pct:.1f}%  ({uncovered_teu:,.0f} TEU/wk)")

    print(f"\n  {sep()}")

    # Assertions
    assert_gt(weekly_profit,  0,   "Global weekly profit > 0")
    assert_gt(total_services, 0,   "Total services deployed > 0")
    assert_range(coverage,    0, 100, "Global coverage in [0, 100]%")
    assert_true(
        abs(annual_profit - weekly_profit * 52) < weekly_profit * 0.01 + 1,
        "Annual profit = weekly × 52",
        f"annual={annual_profit:,.0f}  weekly×52={weekly_profit*52:,.0f}",
    )
    assert_gt(weekly_profit, weekly_cost,
              "Network is profitable (profit > operating cost)")

    warn_if(coverage < 15,       f"Global coverage {coverage:.1f}% < 15% — very low")
    warn_if(profit_margin < 20,  f"Profit margin {profit_margin:.1f}% < 20% — low")
    warn_if(uncovered_teu > stats["total_demand"] * 0.7,
            f"{uncovered_pct:.0f}% of demand ({uncovered_teu:,.0f} TEU) is unserved")


# ===========================================================================
# Section 5 — Executive summary quality
# ===========================================================================

def section_executive_summary(result: Dict, metrics: Dict):
    print_section_header("5 · EXECUTIVE SUMMARY  (Orchestrator LLM)")

    summary = result.get("executive_summary", "")
    print(summary)
    print(f"\n  {sep()}")

    weekly_profit = float(metrics["weekly_profit"])
    coverage      = float(metrics["coverage"])
    total_services = metrics["total_services"]

    # Structure checks
    assert_true(len(summary) > 100, "Summary is non-trivial (>100 chars)")
    assert_true(
        any(v in summary for v in ("Good", "Moderate", "Poor")),
        "Summary contains verdict (Good / Moderate / Poor)",
    )
    assert_true(
        any(kw in summary for kw in ("Strength", "Weakness", "Priority", "Action")),
        "Summary has structured sections",
    )

    # Quantitative grounding checks
    assert_has_number(summary, "Summary cites specific numbers")

    # Key figures that MUST appear (or close approximation)
    profit_str = f"{weekly_profit:,.0f}".replace(",", "")  # strip commas for search
    assert_true(
        re.search(r"\$[\d,]+", summary) is not None,
        "Summary references a dollar figure",
    )
    assert_true(
        re.search(r"\d+\.?\d*%", summary) is not None,
        "Summary references a percentage figure",
    )

    # Anti-vague checks
    vague = ["consider", "explore", "may ", "could potentially", "perhaps",
             "renegotiating contracts", "more efficient technologies"]
    has_vague = any(v in summary.lower() for v in vague)
    assert_true(not has_vague, "Summary avoids generic/vague language")

    warn_if(
        "executive summary unavailable" in summary.lower(),
        "Summary fell back to static text — LLM call may have failed",
    )


# ===========================================================================
# Section 6 — Pipeline integrity
# ===========================================================================

def section_pipeline_integrity(result: Dict, regional_results: List[Dict], stats: Dict):
    print_section_header("6 · PIPELINE INTEGRITY")

    # Top-level keys
    for key in ("status", "problem_analysis", "regional_results",
                "executive_summary", "summary_metrics"):
        assert_true(key in result, f"Top-level key '{key}' present")

    assert_true(result["status"] == "complete", "Status == 'complete'")

    # Regional result keys (new hardened agent fields included)
    required_regional_keys = [
        "agent", "region", "status", "services_generated",
        "services_filtered", "services_selected",
        "weekly_profit", "coverage_percent", "operating_cost",
        "strategy", "explanation",
    ]
    hardened_keys = [
        "annual_profit", "profit_margin_pct",
        "profit_per_service", "cost_per_service",
        "uncovered_teu", "hub_ports",
    ]

    for r in regional_results:
        region = r.get("region", "?")
        for key in required_regional_keys:
            assert_true(key in r, f"[{region}] Required key '{key}' present")
        for key in hardened_keys:
            assert_true(key in r, f"[{region}] Hardened key '{key}' present")

    # Services funnel: generated >= filtered >= selected
    for r in regional_results:
        region = r.get("region", "?")
        gen    = r.get("services_generated", 0)
        flt    = r.get("services_filtered",  0)
        sel    = r.get("services_selected",  0)
        assert_true(
            gen >= flt >= 0,
            f"[{region}] Service funnel: generated({gen}) >= filtered({flt})",
        )
        assert_true(
            sel <= flt + 1,   # +1 tolerance for rounding
            f"[{region}] Service funnel: selected({sel}) <= filtered({flt})",
        )

    # Profit cross-check: sum of regional profits ≈ global total (within 1%)
    metrics = result["summary_metrics"]
    regional_profit_sum = sum(r.get("weekly_profit", 0) for r in regional_results)
    global_profit       = float(metrics["weekly_profit"])
    if global_profit > 0:
        deviation = abs(regional_profit_sum - global_profit) / global_profit
        assert_true(
            deviation < 0.02,
            "Regional profit sum ≈ global total (within 2%)",
            f"Regional sum=${regional_profit_sum:,.0f}  Global=${global_profit:,.0f}  "
            f"deviation={deviation*100:.1f}%",
        )


# ===========================================================================
# Section 7 — Performance benchmarks
# ===========================================================================

def section_performance(elapsed: float, stats: Dict):
    print_section_header("7 · PERFORMANCE")

    num_ports  = stats["num_ports"]
    num_lanes  = stats["num_lanes"]
    throughput = num_lanes / elapsed if elapsed > 0 else 0

    print_kv("Total elapsed time",  f"{elapsed:.1f}s")
    print_kv("Demand lanes",        f"{num_lanes:,}")
    print_kv("Throughput",          f"{throughput:,.0f} lanes/second")
    print_kv("Time per port",       f"{elapsed/num_ports*1000:.1f}ms" if num_ports else "N/A")

    warn_if(elapsed > 600, f"Pipeline took {elapsed:.0f}s — over 10 minutes")
    warn_if(elapsed > 300, f"Pipeline took {elapsed:.0f}s — over 5 minutes")
    assert_true(elapsed < 3600, "Pipeline completed within 1 hour")


# ===========================================================================
# Final summary table
# ===========================================================================

def print_final_summary(stats: Dict, metrics: Dict, regional_results: List[Dict]):
    print_section_header("OPTIMIZATION RESULTS SUMMARY")

    weekly_profit  = float(metrics["weekly_profit"])
    annual_profit  = float(metrics["annual_profit"])
    weekly_cost    = float(metrics["cost"])
    coverage       = float(metrics["coverage"])
    total_services = metrics["total_services"]
    profit_margin  = weekly_profit / (weekly_profit + weekly_cost) * 100 \
                     if (weekly_profit + weekly_cost) > 0 else 0
    uncovered_teu  = stats["total_demand"] * (100 - coverage) / 100

    print(f"""
  ┌─────────────────────────────────────────────────────────────────┐
  │  {C.BOLD}GLOBAL NETWORK PERFORMANCE{C.RESET}                                      │
  ├─────────────────────────────────────────────────────────────────┤
  │  Services deployed    {total_services:>8,}                                  │
  │  Weekly profit        ${weekly_profit:>14,.0f}                          │
  │  Annual profit        ${annual_profit:>14,.0f}                          │
  │  Operating cost/wk    ${weekly_cost:>14,.0f}                          │
  │  Profit margin        {profit_margin:>13.1f}%                          │
  │  Demand coverage      {coverage:>13.1f}%                          │
  │  Unserved demand      {uncovered_teu:>12,.0f} TEU/wk                   │
  └─────────────────────────────────────────────────────────────────┘""")

    print(f"\n  {C.BOLD}REGIONAL BREAKDOWN{C.RESET}")
    print(f"  {'Region':<12}  {'Profit/wk':>14}  {'Coverage':>9}  "
          f"{'Services':>9}  {'Margin%':>8}  {'Hub Ports'}")
    print(f"  {sep()}")
    for r in regional_results:
        region  = r.get("region", "?")
        profit  = r.get("weekly_profit", 0)
        cov     = r.get("coverage_percent", 0)
        svcs    = r.get("services_selected", 0)
        cost    = r.get("operating_cost", 0)
        margin  = r.get("profit_margin_pct",
                        round(profit / (profit + cost) * 100, 1) if (profit + cost) > 0 else 0)
        hubs    = r.get("hub_ports", [])
        hub_str = str(hubs[:3])[1:-1] if hubs else "—"
        print(f"  {region:<12}  ${profit:>13,.0f}  {cov:>8.1f}%  "
              f"{svcs:>9,}  {margin:>7.1f}%  [{hub_str}]")


# ===========================================================================
# Main test entry point
# ===========================================================================

def test_orchestrator():
    global _PASS, _FAIL, _WARN

    print(f"\n{C.BOLD}{'=' * 70}{C.RESET}")
    print(f"{C.BOLD}  LINER SHIPPING OPTIMIZER — FULL PIPELINE TEST{C.RESET}")
    print(f"{C.BOLD}{'=' * 70}{C.RESET}")

    # ── Step 1: Create orchestrator ────────────────────────────────────────
    print(hdr("0 · INITIALISATION"))
    print(f"  {sep()}")
    orchestrator = OrchestratorAgent()
    print(ok("OrchestratorAgent created"))
    print(ok(f"Regional agents: {[a.name for a in orchestrator.regional_agents]}"))

    # ── Step 2: Load problem ───────────────────────────────────────────────
    dataset = "data/datasets/large_shipping_problem.json"
    problem = load_problem(dataset)
    print(ok(f"Dataset loaded: {dataset}"))

    # ── Step 3: Problem statistics ─────────────────────────────────────────
    stats = section_problem_stats(problem)

    # ── Step 4: Run pipeline ───────────────────────────────────────────────
    print_section_header("RUNNING PIPELINE")
    print(f"  {C.DIM}Steps:{C.RESET}")
    for step in [
        "Orchestrator LLM — problem analysis",
        "PortClustering → RegionalSplitter — decomposition",
        "RegionalAgent × 3 — GA + MILP + LLM",
        "Orchestrator LLM — executive summary",
    ]:
        print(f"  {C.DIM}  → {step}{C.RESET}")

    print(f"\n  {C.YELLOW}Running... (this may take several minutes){C.RESET}\n")
    t0     = time.perf_counter()
    result = orchestrator.process({"problem": problem})
    elapsed = time.perf_counter() - t0
    print(f"\n  {ok(f'Pipeline complete in {elapsed:.1f}s')}")

    # ── Step 5: Validate all sections ──────────────────────────────────────
    section_problem_analysis(result, stats)
    section_regional_results(result, stats)
    section_global_metrics(result, stats)
    section_executive_summary(result, result["summary_metrics"])

    regional_results = result.get("regional_results", [])
    section_pipeline_integrity(result, regional_results, stats)
    section_performance(elapsed, stats)

    # ── Final summary ──────────────────────────────────────────────────────
    print_final_summary(stats, result["summary_metrics"], regional_results)

    # ── Test scorecard ─────────────────────────────────────────────────────
    print_section_header("TEST SCORECARD")
    total = _PASS + _FAIL
    pct   = _PASS / total * 100 if total else 0

    print(f"  {C.GREEN}Passed  : {_PASS:>4}/{total}{C.RESET}")
    print(f"  {C.RED}Failed  : {_FAIL:>4}/{total}{C.RESET}")
    print(f"  {C.YELLOW}Warnings: {_WARN:>4}{C.RESET}")
    print(f"  Score   : {pct:.0f}%")
    print(f"\n  {sep()}")

    if _FAIL == 0:
        print(f"\n  {C.GREEN}{C.BOLD}✓ ALL ASSERTIONS PASSED{C.RESET}")
        print(f"  {C.GREEN}Pipeline is operating correctly.{C.RESET}")
    else:
        print(f"\n  {C.RED}{C.BOLD}✗ {_FAIL} ASSERTION(S) FAILED{C.RESET}")
        print(f"  {C.RED}Review the FAIL lines above for details.{C.RESET}")

    if _WARN:
        print(f"\n  {C.YELLOW}{_WARN} warning(s) noted — review above.{C.RESET}")

    print(f"\n{'=' * 70}\n")

    # Hard assert so pytest catches failures
    assert _FAIL == 0, f"{_FAIL} assertion(s) failed — see output above."

    return result


# ===========================================================================
# Run directly
# ===========================================================================

if __name__ == "__main__":
    test_orchestrator()