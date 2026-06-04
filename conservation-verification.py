#!/usr/bin/env python3
"""
Conservation Law Verification for Agent Behavior Graphs

Uses spectral graph theory to analyze the SuperInstance agent ecosystem.
An agent behavior graph: nodes = agents, edges = data flow between them.
Conservation laws ensure no agent exceeds its resource budget.

Requires: conservation-spectral-topology (Rust, via PyO3 or standalone)
For now: pure Python verification using numpy.
"""

import numpy as np
import json
import time

# ─── Agent Behavior Graph ──────────────────────────────────────
# Nodes: agents in the ecosystem
# Edges: data/communication flow between agents
# Laplacian: L = D - A (degree matrix - adjacency matrix)
# Conservation: sum of all flows = 0 (energy in = energy out)

AGENTS = {
    "lever-runner": {"type": "execution", "budget": 1000},    # tokens/min
    "pincherOS":    {"type": "memory",    "budget": 500},      # reflexes
    "PLATO":        {"type": "intelligence", "budget": 200},   # rooms
    "agent-A":      {"type": "git-native", "budget": 100},     # commands
    "agent-B":      {"type": "git-native", "budget": 100},
    "agent-C":      {"type": "git-native", "budget": 100},
}

# Adjacency: how much data flows between agents
# Rows/cols: [lever-runner, pincherOS, PLATO, agent-A, agent-B, agent-C]
ADJACENCY = np.array([
    # lr    pOS   PLATO  A     B     C
    [0.0,  0.8,  0.3,   0.5,  0.2,  0.1],  # lever-runner
    [0.8,  0.0,  0.4,   0.3,  0.1,  0.0],  # pincherOS
    [0.3,  0.4,  0.0,   0.6,  0.6,  0.6],  # PLATO
    [0.5,  0.3,  0.6,   0.0,  0.2,  0.0],  # agent-A
    [0.2,  0.1,  0.6,   0.2,  0.0,  0.3],  # agent-B
    [0.1,  0.0,  0.6,   0.0,  0.3,  0.0],  # agent-C
], dtype=np.float64)

def compute_laplacian(adj):
    """L = D - A"""
    D = np.diag(adj.sum(axis=1))
    return D - adj

def spectral_budget(L):
    """Eigenvalues of the Laplacian = conservation budget spectrum"""
    eigenvalues = np.sort(np.linalg.eigvalsh(L))
    return eigenvalues

def cheeger_constant(L):
    """
    Cheeger constant h(G) = minimum edge expansion.
    Measures how well-connected the graph is.
    High h = well-connected (hard to partition)
    Low h = bottleneck (single point of failure)
    """
    n = L.shape[0]
    eigenvalues = np.sort(np.linalg.eigvalsh(L))
    
    # λ₁ = 0 always (connected graph has one zero eigenvalue)
    # λ₂ (algebraic connectivity / Fiedler value)
    lambda_2 = eigenvalues[1] if n > 1 else 0
    
    # Cheeger inequality: λ₂/2 ≤ h(G) ≤ √(2λ₂)
    h_lower = lambda_2 / 2
    h_upper = np.sqrt(2 * lambda_2)
    
    return lambda_2, h_lower, h_upper

def verify_conservation(L, flow_vector):
    """
    Conservation law: L · f = 0 for steady-state flow
    If L · f ≠ 0, there's a leak (agent exceeding budget)
    """
    residual = L @ flow_vector
    leakage = np.linalg.norm(residual)
    is_conserved = leakage < 1e-10
    return is_conserved, leakage

def agent_specialization(L):
    """
    Spectral gap = λ_n - λ_2
    Large spectral gap = agents are specialized (distinct roles)
    Small spectral gap = agents are generalists (overlapping roles)
    """
    eigenvalues = np.sort(np.linalg.eigvalsh(L))
    spectral_gap = eigenvalues[-1] - eigenvalues[1]
    return spectral_gap

def resource_allocation(L, budgets):
    """
    Check if the agent graph respects resource budgets.
    Each agent's total flow (degree) should not exceed its budget.
    """
    degrees = L.diagonal()
    agent_names = list(AGENTS.keys())
    results = {}
    for i, (name, info) in enumerate(AGENTS.items()):
        utilization = degrees[i] / info["budget"] * 100
        results[name] = {
            "degree": degrees[i],
            "budget": info["budget"],
            "utilization_pct": utilization,
            "status": "OK" if utilization < 80 else "WARNING" if utilization < 100 else "EXCEEDED"
        }
    return results

# ─── Run Analysis ──────────────────────────────────────────────
print("=" * 60)
print("SUPERINSTANCE ECOSYSTEM — Conservation Law Verification")
print("=" * 60)

L = compute_laplacian(ADJACENCY)
print(f"\nGraph Laplacian:\n{np.round(L, 2)}")

# Spectral budget
eigenvalues = spectral_budget(L)
print(f"\nEigenvalue spectrum (conservation budget):")
for i, ev in enumerate(eigenvalues):
    print(f"  λ_{i+1} = {ev:.4f}")

# Algebraic connectivity
lambda_2, h_lo, h_hi = cheeger_constant(L)
print(f"\nAlgebraic connectivity (λ₂): {lambda_2:.4f}")
print(f"Cheeger constant bounds: [{h_lo:.4f}, {h_hi:.4f}]")
print(f"  → Graph is {'well-connected' if lambda_2 > 1.0 else 'fragile (bottleneck)'}")

# Specialization
gap = agent_specialization(L)
print(f"\nSpectral gap (specialization): {gap:.4f}")
print(f"  → Agents are {'specialized' if gap > 5.0 else 'generalists' if gap < 2.0 else 'moderately specialized'}")

# Conservation verification
flow = np.array([1.0, 0.8, 1.5, 0.7, 0.4, 0.3])  # current activity levels
conserved, leakage = verify_conservation(L, flow)
print(f"\nConservation law check:")
print(f"  Flow vector: {flow}")
print(f"  Leakage: {leakage:.6f}")
print(f"  Status: {'✅ CONSERVED' if conserved else '❌ LEAKING — agent exceeding budget!'}")

# Resource allocation
alloc = resource_allocation(L, AGENTS)
print(f"\nResource allocation:")
for name, info in alloc.items():
    print(f"  {name:15s}: degree={info['degree']:.1f}, budget={info['budget']}, util={info['utilization_pct']:.1f}% [{info['status']}]")

# ─── Ecosystem Health Score ────────────────────────────────
connectivity_score = min(lambda_2 / 2.0, 1.0)  # normalized
specialization_score = min(gap / 8.0, 1.0)     # normalized
conservation_score = 1.0 if conserved else max(0, 1.0 - leakage)
utilization_scores = [1.0 if a['status'] == 'OK' else 0.5 if a['status'] == 'WARNING' else 0.0 for a in alloc.values()]
resource_score = np.mean(utilization_scores)

health = (connectivity_score + specialization_score + conservation_score + resource_score) / 4

print(f"\n{'=' * 60}")
print(f"ECOSYSTEM HEALTH: {health:.2f} / 1.00")
print(f"  Connectivity:    {connectivity_score:.2f}")
print(f"  Specialization:  {specialization_score:.2f}")
print(f"  Conservation:    {conservation_score:.2f}")
print(f"  Resource usage:  {resource_score:.2f}")
print(f"{'=' * 60}")

# Save results
results = {
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "eigenvalues": eigenvalues.tolist(),
    "algebraic_connectivity": lambda_2,
    "cheeger_bounds": [h_lo, h_hi],
    "spectral_gap": gap,
    "conservation_leakage": leakage,
    "health_score": health,
    "resource_allocation": alloc,
}
with open("benchmarks/conservation-results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved to benchmarks/conservation-results.json")
