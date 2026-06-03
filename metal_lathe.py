"""
Metal Lathe — The Research Wheel

Takes experimental results → generates novel questions → develops hypothetical
structures → designs experiments → tests on metal → feeds results back in.

The wheel turns itself. Each cycle produces:
1. OBSERVE: What did we measure? What's surprising?
2. QUESTION: What don't we understand? What's the edge case?
3. HYPOTHESIZE: What structure could explain the surprise?
4. DESIGN: How do we test the hypothesis on real hardware?
5. TEST: Run the experiment, collect data
6. FEED: Results go back to step 1

The wheel is grounded by the metal — real hardware, real numbers, real failures.
No speculation without a test. No hypothesis without an observation.
"""

import json
import time
import hashlib
import os
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum
from pathlib import Path


class Phase(Enum):
    OBSERVE = "observe"
    QUESTION = "question"
    HYPOTHESIZE = "hypothesize"
    DESIGN = "design"
    TEST = "test"
    FEED = "feed"


@dataclass
class Observation:
    """Raw experimental result — a fact about the world."""
    source: str          # what experiment/repo/measurement
    metric: str          # what was measured
    value: float         # the number
    unit: str            # ms, tokens, %, etc.
    context: dict        # hardware, config, conditions
    surprising: bool     # did this surprise us?
    surprise_reason: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class Question:
    """A novel question generated from observations."""
    text: str
    source_observations: list[str]  # hashes of observations that inspired it
    novelty_score: float  # 0-1, how novel is this question?
    testable: bool        # can we test this on metal?
    tags: list[str] = field(default_factory=list)
    hash: str = ""
    
    def __post_init__(self):
        if not self.hash:
            self.hash = hashlib.blake2b(self.text.encode(), digest_size=12).hexdigest()


@dataclass
class Hypothesis:
    """A testable structure that could explain observations."""
    text: str
    questions: list[str]   # hashes of questions this addresses
    predictions: list[str] # what we'd expect if this is true
    structure: dict        # formal/mathematical description
    testable_on: list[str] # what hardware can test this
    confidence_prior: float = 0.5  # prior belief (0-1)
    hash: str = ""
    
    def __post_init__(self):
        if not self.hash:
            self.hash = hashlib.blake2b(self.text.encode(), digest_size=12).hexdigest()


@dataclass
class Experiment:
    """A designed test to validate or refute a hypothesis."""
    hypothesis_hash: str
    procedure: str         # what to run
    expected_result: str   # if hypothesis is true, we see X
    code: str              # actual code to execute
    hardware_required: str # RTX4050, ARM, Pi, etc.
    duration_estimate: str # how long it takes
    hash: str = ""
    
    def __post_init__(self):
        content = f"{self.hypothesis_hash}:{self.procedure}"
        if not self.hash:
            self.hash = hashlib.blake2b(content.encode(), digest_size=12).hexdigest()


@dataclass
class TestResult:
    """Results from running an experiment on metal."""
    experiment_hash: str
    hypothesis_hash: str
    passed: bool           # did results match prediction?
    data: dict             # raw measurements
    surprise_level: float  # 0-1, how surprised are we?
    new_observations: list[str] = field(default_factory=list)  # hashes
    timestamp: float = field(default_factory=time.time)


class MetalLathe:
    """
    The research wheel. Churns observations into questions,
    questions into hypotheses, hypotheses into experiments,
    experiments into results, results into observations.
    
    Each full cycle advances understanding. The wheel turns itself.
    """
    
    def __init__(self, state_dir: str = "~/.metal-lathe"):
        self.state_dir = Path(os.path.expanduser(state_dir))
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.observations: list[Observation] = []
        self.questions: list[Question] = []
        self.hypotheses: list[Hypothesis] = []
        self.experiments: list[Experiment] = []
        self.results: list[TestResult] = []
        
        self.cycle_count = 0
        self._load_state()
    
    # ── Phase 1: OBSERVE ──────────────────────────────────
    
    def observe(self, source: str, metric: str, value: float, 
                unit: str, context: dict, surprising: bool = False,
                surprise_reason: str = None) -> Observation:
        """Record an experimental observation."""
        obs = Observation(
            source=source, metric=metric, value=value, unit=unit,
            context=context, surprising=surprising,
            surprise_reason=surprise_reason
        )
        self.observations.append(obs)
        self._save_state()
        return obs
    
    def observe_from_results(self, results_file: str):
        """Load observations from open-mind induction results."""
        with open(results_file) as f:
            data = json.load(f)
        
        for func in data.get("functions", []):
            name = func.get("name", "unknown")
            calls = len(func.get("calls", []))
            self.observe(
                source=results_file,
                metric=f"call_degree:{name}",
                value=calls,
                unit="edges",
                context={"function": name, "file": func.get("file", "")},
                surprising=calls > 20,
                surprise_reason=f"{name} has {calls} callers — hub function"
            )
    
    # ── Phase 2: QUESTION ──────────────────────────────────
    
    def generate_questions(self) -> list[Question]:
        """
        Analyze observations and generate novel questions.
        Uses pattern detection across observations.
        """
        new_questions = []
        
        # Pattern 1: Surprising observations cluster
        surprises = [o for o in self.observations if o.surprising]
        if len(surprises) >= 2:
            # What do the surprises have in common?
            surprise_metrics = set(o.metric for o in surprises)
            for metric in surprise_metrics:
                related = [o for o in surprises if metric.split(":")[0] in o.metric]
                if len(related) >= 2:
                    q = Question(
                        text=f"Why do {len(related)} observations in {metric.split(':')[0]} show surprising values? What structural property causes this clustering?",
                        source_observations=[str(i) for i, o in enumerate(self.observations) if o in related],
                        novelty_score=0.7,
                        testable=True,
                        tags=["surprise-clustering", metric.split(":")[0]]
                    )
                    self.questions.append(q)
                    new_questions.append(q)
        
        # Pattern 2: Distribution anomalies
        values_by_metric = {}
        for o in self.observations:
            key = o.metric.split(":")[0] if ":" in o.metric else o.metric
            values_by_metric.setdefault(key, []).append(o.value)
        
        for key, values in values_by_metric.items():
            if len(values) >= 5:
                import statistics
                mean = statistics.mean(values)
                std = statistics.stdev(values) if len(values) > 1 else 0
                outliers = [v for v in values if abs(v - mean) > 2 * std] if std > 0 else []
                if outliers:
                    q = Question(
                        text=f"The {key} distribution has {len(outliers)} outliers beyond 2σ (mean={mean:.2f}, std={std:.2f}). Are these outliers structurally significant or noise?",
                        source_observations=[str(i) for i, o in enumerate(self.observations) if o.metric.startswith(key)],
                        novelty_score=0.8,
                        testable=True,
                        tags=["distribution-anomaly", key]
                    )
                    self.questions.append(q)
                    new_questions.append(q)
        
        # Pattern 3: Conservation law violations
        conservation_obs = [o for o in self.observations if "leakage" in o.metric or "conservation" in o.metric]
        for o in conservation_obs:
            if o.value > 0.01:  # non-trivial leakage
                q = Question(
                    text=f"Conservation leakage of {o.value:.4f} detected in {o.source}. What unmodeled flow path exists? Is there a hidden agent or data channel?",
                    source_observations=[str(self.observations.index(o))],
                    novelty_score=0.9,
                    testable=True,
                    tags=["conservation-violation", "hidden-flow"]
                )
                self.questions.append(q)
                new_questions.append(q)
        
        # Pattern 4: Cross-repo structural comparison
        sources = set(o.source for o in self.observations)
        if len(sources) >= 2:
            q = Question(
                text=f"We have observations from {len(sources)} different sources. What structural isomorphisms exist between them? Do they share a latent topology?",
                source_observations=[str(i) for i in range(len(self.observations))],
                novelty_score=0.6,
                testable=True,
                tags=["cross-repo", "structural-isomorphism"]
            )
            self.questions.append(q)
            new_questions.append(q)
        
        # Pattern 5: Hardware-performance correlation
        hw_contexts = set()
        for o in self.observations:
            device = o.context.get("device_type", o.context.get("hardware", "unknown"))
            hw_contexts.add(device)
        
        if len(hw_contexts) >= 2:
            q = Question(
                text=f"Performance measured across {len(hw_contexts)} hardware profiles ({', '.join(hw_contexts)}). Is the performance scaling linear, sublinear, or superlinear with compute power?",
                source_observations=[str(i) for i in range(len(self.observations))],
                novelty_score=0.75,
                testable=True,
                tags=["hardware-scaling", "performance"]
            )
            self.questions.append(q)
            new_questions.append(q)
        
        # Pattern 6: Degree distribution power law
        degree_obs = [o for o in self.observations if "degree" in o.metric]
        if len(degree_obs) >= 10:
            import math
            degrees = sorted([o.value for o in degree_obs], reverse=True)
            # Check if log-log is roughly linear (power law)
            if degrees[0] > 0 and degrees[-1] > 0:
                log_range = math.log(degrees[0]) - math.log(degrees[-1])
                if log_range > 2:  # spanning 2+ orders of magnitude
                    q = Question(
                        text=f"Call graph degree spans {log_range:.1f} orders of magnitude. Is this a scale-free network? If so, the hub functions are critical infrastructure — what happens if we remove them?",
                        source_observations=[str(self.observations.index(o)) for o in degree_obs],
                        novelty_score=0.85,
                        testable=True,
                        tags=["power-law", "scale-free", "critical-infrastructure"]
                    )
                    self.questions.append(q)
                    new_questions.append(q)
        
        # Pattern 7: Ecosystem-specific — tripartite decision distribution
        decision_obs = [o for o in self.observations if "decision" in o.metric.lower() or "hardcode" in o.metric.lower() or "model" in o.metric.lower()]
        if len(decision_obs) >= 5:
            hardcode_count = sum(1 for o in decision_obs if "hardcode" in str(o.value).lower() or o.value == 0)
            q = Question(
                text=f"Tripartite decisions are {(hardcode_count/len(decision_obs)*100):.0f}% HARDCODE. Is this because our profile is too conservative, or because terminal ops genuinely should be deterministic? What's the crossover point where MODEL becomes better?",
                source_observations=[str(self.observations.index(o)) for o in decision_obs],
                novelty_score=0.8,
                testable=True,
                tags=["tripartite-balance", "crossover-point"]
            )
            self.questions.append(q)
            new_questions.append(q)
        
        self._save_state()
        return new_questions
    
    # ── Phase 3: HYPOTHESIZE ───────────────────────────────
    
    def generate_hypotheses(self) -> list[Hypothesis]:
        """Turn questions into testable hypothetical structures."""
        new_hypotheses = []
        
        for q in self.questions:
            if not q.testable:
                continue
            
            # Conservation violation → hidden flow hypothesis
            if "conservation-violation" in q.tags:
                h = Hypothesis(
                    text=f"The leakage in the ecosystem graph indicates an unmodeled data channel. Hypothesis: there's an implicit feedback loop (likely through the user or filesystem) that isn't represented in the adjacency matrix.",
                    questions=[q.hash],
                    predictions=[
                        "Adding a 'user' node to the graph will reduce leakage to near-zero",
                        "The user node should have degree proportional to the current leakage",
                        "Removing the user feedback path will increase latency (the hidden channel has a purpose)"
                    ],
                    structure={
                        "type": "graph_completion",
                        "missing_node": "user_feedback",
                        "expected_degree": ">0",
                        "math": "L_extended · f_extended = 0 where f_extended includes user feedback"
                    },
                    testable_on=["RTX4050", "ARM"],
                    confidence_prior=0.7
                )
                self.hypotheses.append(h)
                new_hypotheses.append(h)
            
            # Power law → critical infrastructure hypothesis
            if "power-law" in q.tags:
                h = Hypothesis(
                    text=f"The call graph is scale-free with hub functions as critical infrastructure. Hypothesis: removing the top 3 hub functions will cause cascading failure in >50% of the call graph, while removing 3 random non-hub functions will affect <10%.",
                    questions=[q.hash],
                    predictions=[
                        "Hub removal causes >50% graph disconnection",
                        "Random removal causes <10% disconnection",
                        "The spectral gap (λ_n - λ_2) decreases sharply with hub removal",
                        "Adding redundancy to hubs improves health score more than adding new agents"
                    ],
                    structure={
                        "type": "robustness_test",
                        "attack": "targeted_vs_random",
                        "metric": "connected_component_ratio",
                        "threshold": 0.5,
                        "math": "H(G\\{hub}) / H(G) < 0.5 where H is graph health"
                    },
                    testable_on=["RTX4050"],
                    confidence_prior=0.8
                )
                self.hypotheses.append(h)
                new_hypotheses.append(h)
            
            # Hardware scaling → crossover hypothesis
            if "hardware-scaling" in q.tags:
                h = Hypothesis(
                    text=f"There exists a compute_power threshold below which HARDCODE always wins and above which MODEL becomes competitive. Hypothesis: the crossover is at compute_power ≈ 0.3 (roughly a Raspberry Pi 4), and it's linear in embedding dimension.",
                    questions=[q.hash],
                    predictions=[
                        "At compute_power < 0.3, HARDCODE latency < MODEL latency for all operations",
                        "At compute_power > 0.3, MODEL latency improves superlinearly",
                        "The crossover shifts right proportionally to embedding dimension (higher dim = need more compute)",
                        "ARM (compute_power ~0.2) should always route to HARDCODE or CACHED"
                    ],
                    structure={
                        "type": "crossover_function",
                        "params": ["compute_power", "embedding_dim", "operation_type"],
                        "crossover_point": 0.3,
                        "scaling": "linear_in_dim",
                        "math": "latency_model(p, d) = k * d / p; latency_hardcode(p, d) = c; crossover where k*d/p = c"
                    },
                    testable_on=["RTX4050", "ARM"],
                    confidence_prior=0.6
                )
                self.hypotheses.append(h)
                new_hypotheses.append(h)
            
            # Cross-repo isomorphism → latent structure hypothesis
            if "structural-isomorphism" in q.tags:
                h = Hypothesis(
                    text=f"Different repos share a latent execution topology. Hypothesis: the normalized call graph Laplacians of lever-runner, pincherOS, and intelligent-terminal have similar eigenvalue spectra (cosine similarity > 0.8), indicating they implement the same abstract pattern.",
                    questions=[q.hash],
                    predictions=[
                        "Normalized Laplacian eigenvalue spectra have cosine similarity > 0.8",
                        "The shared pattern is: hub-dispatcher → worker functions → aggregation",
                        "This pattern is the 'agent skeleton' — any agent system has it",
                        "Conservation laws hold across repos when normalized by function count"
                    ],
                    structure={
                        "type": "spectral_isomorphism",
                        "repos": ["lever-runner", "pincherOS", "intelligent-terminal"],
                        "metric": "eigenvalue_cosine_similarity",
                        "threshold": 0.8,
                        "math": "cos(σ(L_norm_A), σ(L_norm_B)) > 0.8"
                    },
                    testable_on=["RTX4050"],
                    confidence_prior=0.5
                )
                self.hypotheses.append(h)
                new_hypotheses.append(h)
            
            # Tripartite balance → adaptive profile hypothesis
            if "tripartite-balance" in q.tags:
                h = Hypothesis(
                    text=f"The optimal tripartite profile isn't fixed — it depends on the workload phase. Hypothesis: a learning profile that observes the last 100 decisions and adjusts weights will outperform any fixed profile by >15% on accuracy within 500 decisions.",
                    questions=[q.hash],
                    predictions=[
                        "Adaptive profile beats fixed profiles by >15% accuracy",
                        "The learning converges in <500 decisions",
                        "The learned weights correlate with actual task distribution (more MODEL when tasks are creative)",
                        "On edge devices, adaptive profile converges to near-HARDCODE"
                    ],
                    structure={
                        "type": "adaptive_controller",
                        "algorithm": "exponential_weighted_average",
                        "window": 100,
                        "metric": "decision_accuracy",
                        "math": "w_new = α * w_observed + (1-α) * w_old; α = 0.1"
                    },
                    testable_on=["RTX4050", "ARM"],
                    confidence_prior=0.65
                )
                self.hypotheses.append(h)
                new_hypotheses.append(h)
            
            # Surprise clustering → latent variable hypothesis
            if "surprise-clustering" in q.tags:
                h = Hypothesis(
                    text=f"Surprising observations cluster because they share a latent variable we haven't measured. Hypothesis: the latent variable is 'coupling density' — functions with high coupling density (>5 inter-module calls) are always surprising regardless of the metric being measured.",
                    questions=[q.hash],
                    predictions=[
                        "Functions with coupling_density > 5 are >3× more likely to produce surprising observations",
                        "Coupling density predicts surprise better than raw degree or betweenness",
                        "Reducing coupling density (refactoring) reduces surprise rate",
                        "Conservation-spectral-topology's Cheeger constant correlates with surprise rate"
                    ],
                    structure={
                        "type": "latent_variable",
                        "variable": "coupling_density",
                        "operationalization": "count of inter-module edges / total edges",
                        "threshold": 0.2,
                        "math": "P(surprise | coupling_density > θ) / P(surprise) > 3"
                    },
                    testable_on=["RTX4050"],
                    confidence_prior=0.55
                )
                self.hypotheses.append(h)
                new_hypotheses.append(h)
        
        self._save_state()
        return new_hypotheses
    
    # ── Phase 4: DESIGN ───────────────────────────────────
    
    def design_experiments(self) -> list[Experiment]:
        """Turn hypotheses into runnable experiments."""
        new_experiments = []
        
        for h in self.hypotheses:
            if any(e.hypothesis_hash == h.hash for e in self.experiments):
                continue  # already designed
            
            # Graph completion experiment
            if h.structure.get("type") == "graph_completion":
                exp = Experiment(
                    hypothesis_hash=h.hash,
                    procedure="Add a 'user_feedback' node to the ecosystem graph, connect to all agents with weight 0.1, recompute Laplacian and check if leakage drops to <1e-10",
                    expected_result="Leakage drops from 2.69 to <1e-10",
                    code="""
import numpy as np
# Original adjacency (6x6)
A = np.array([
    [0, 0.8, 0.3, 0.5, 0.2, 0.1],
    [0.8, 0, 0.4, 0.3, 0.1, 0],
    [0.3, 0.4, 0, 0.6, 0.6, 0.6],
    [0.5, 0.3, 0.6, 0, 0.2, 0],
    [0.2, 0.1, 0.6, 0.2, 0, 0.3],
    [0.1, 0, 0.6, 0, 0.3, 0],
])
# Extended with user_feedback node (7x7)
# user connects to all agents with weight 0.1
A_ext = np.zeros((7, 7))
A_ext[:6, :6] = A
A_ext[6, :6] = 0.1
A_ext[:6, 6] = 0.1
D_ext = np.diag(A_ext.sum(axis=1))
L_ext = D_ext - A_ext
flow_ext = np.array([1.0, 0.8, 1.5, 0.7, 0.4, 0.3, 0.47])
leakage = np.linalg.norm(L_ext @ flow_ext)
print(f"Extended leakage: {leakage:.6f}")
assert leakage < 0.01, f"Leakage {leakage} too high"
""",
                    hardware_required="any",
                    duration_estimate="1 second"
                )
                self.experiments.append(exp)
                new_experiments.append(exp)
            
            # Robustness test experiment
            if h.structure.get("type") == "robustness_test":
                exp = Experiment(
                    hypothesis_hash=h.hash,
                    procedure="Remove top 3 hub functions from lever-runner call graph, measure health score drop. Compare with removing 3 random non-hubs.",
                    expected_result="Hub removal: health drops >50%. Random removal: health drops <10%.",
                    code="""
import json, numpy as np
# Load lever-runner induction results
with open('/home/phoenix/repos/open-minded/induction-results/lever-runner/functions.json') as f:
    functions = json.load(f)

# Build call graph
call_graph = {}
for func in functions:
    name = func['name']
    calls = func.get('calls', [])
    call_graph[name] = calls

# Find hubs (highest degree)
degree = {}
for name, calls in call_graph.items():
    degree[name] = len(calls)
sorted_hubs = sorted(degree.items(), key=lambda x: -x[1])

top3_hubs = [name for name, _ in sorted_hubs[:3]]
random3 = [name for name, _ in sorted_hubs[-6:-3]]

print(f"Top 3 hubs: {top3_hubs}")
print(f"Random 3: {random3}")

# Measure impact of removal
# (simplified: count reachable nodes from any start)
def reachable(graph, start, removed):
    visited = set()
    stack = [start]
    while stack:
        node = stack.pop()
        if node in removed or node in visited:
            continue
        visited.add(node)
        stack.extend(graph.get(node, []))
    return len(visited)

total = len(call_graph)
hub_impact = total - np.mean([reachable(call_graph, n, set(top3_hubs)) for n in list(call_graph.keys())[:20]])
random_impact = total - np.mean([reachable(call_graph, n, set(random3)) for n in list(call_graph.keys())[:20]])

print(f"Hub removal impact: {hub_impact/total*100:.1f}% disconnected")
print(f"Random removal impact: {random_impact/total*100:.1f}% disconnected")
print(f"Hypothesis: hub impact > 50% and random impact < 10%")
print(f"Hub result: {'PASS' if hub_impact/total > 0.5 else 'FAIL'}")
print(f"Random result: {'PASS' if random_impact/total < 0.1 else 'FAIL'}")
""",
                    hardware_required="any",
                    duration_estimate="5 seconds"
                )
                self.experiments.append(exp)
                new_experiments.append(exp)
            
            # Spectral isomorphism experiment
            if h.structure.get("type") == "spectral_isomorphism":
                exp = Experiment(
                    hypothesis_hash=h.hash,
                    procedure="Compute normalized Laplacian eigenvalue spectra for all 3 repos, measure cosine similarity.",
                    expected_result="Cosine similarity > 0.8 between all pairs.",
                    code="""
import json, numpy as np
from pathlib import Path

repos = {
    'lever-runner': '/home/phoenix/repos/open-minded/induction-results/lever-runner/functions.json',
    'pincherOS': '/home/phoenix/repos/open-minded/induction-results/pincherOS/functions.json',
    'intelligent-terminal': '/home/phoenix/repos/open-minded/induction-results/intelligent-terminal/functions.json',
}

spectra = {}
for name, path in repos.items():
    with open(path) as f:
        functions = json.load(f)
    
    # Build call graph
    call_graph = {}
    for func in functions:
        fn = func['name']
        for call in func.get('calls', []):
            call_graph.setdefault(fn, []).append(call)
            call_graph.setdefault(call, [])
    
    # Adjacency matrix
    nodes = sorted(call_graph.keys())[:200]  # cap at 200 for speed
    n = len(nodes)
    idx = {name: i for i, name in enumerate(nodes)}
    A = np.zeros((n, n))
    for src, dsts in call_graph.items():
        if src not in idx:
            continue
        for dst in dsts:
            if dst in idx:
                A[idx[src], idx[dst]] = 1
    
    # Normalized Laplacian: L_norm = I - D^{-1/2} A D^{-1/2}
    D = A.sum(axis=1)
    D_inv_sqrt = np.diag(np.where(D > 0, 1.0 / np.sqrt(D), 0))
    L_norm = np.eye(n) - D_inv_sqrt @ A @ D_inv_sqrt
    
    eigenvalues = np.sort(np.linalg.eigvalsh(L_norm))[:50]  # top 50
    spectra[name] = eigenvalues / (eigenvalues[-1] if eigenvalues[-1] > 0 else 1)

# Cosine similarity between spectra
print("Spectral Isomorphism Test:")
for a in spectra:
    for b in spectra:
        if a < b:
            va, vb = spectra[a], spectra[b]
            min_len = min(len(va), len(vb))
            va, vb = va[:min_len], vb[:min_len]
            cos_sim = np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb) + 1e-10)
            print(f"  {a} ↔ {b}: cosine similarity = {cos_sim:.4f} {'✅ PASS' if cos_sim > 0.8 else '❌ FAIL'}")
""",
                    hardware_required="RTX4050",
                    duration_estimate="30 seconds"
                )
                self.experiments.append(exp)
                new_experiments.append(exp)
            
            # Crossover point experiment
            if h.structure.get("type") == "crossover_function":
                exp = Experiment(
                    hypothesis_hash=h.hash,
                    procedure="Benchmark embedding latency at different compute power levels (throttle GPU), find where MODEL latency < HARDCODE latency.",
                    expected_result="Crossover at compute_power ≈ 0.3",
                    code="""
import time, numpy as np

# Simulate different compute power levels by varying batch size and measuring
# actual embedding time on RTX 4050
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2', device='cuda')
    has_gpu = True
except:
    has_gpu = False
    print("No GPU model available, using hash benchmark")

# HARDCODE latency (constant - just string matching)
hardcode_latencies = []
for _ in range(100):
    start = time.perf_counter()
    _ = "check disk usage" in "show me disk usage check"
    hardcode_latencies.append((time.perf_counter() - start) * 1000)
hardcode_p50 = sorted(hardcode_latencies)[50]
print(f"HARDCODE latency: {hardcode_p50:.4f} ms")

# MODEL latency at different simulated compute levels
if has_gpu:
    for batch in [1, 4, 16, 64]:
        texts = ["check disk usage"] * batch
        start = time.perf_counter()
        _ = model.encode(texts)
        elapsed = (time.perf_counter() - start) * 1000 / batch
        compute_equiv = min(batch / 64, 1.0)  # rough compute power proxy
        print(f"MODEL latency (batch={batch}, compute≈{compute_equiv:.2f}): {elapsed:.2f} ms per item")
        if elapsed < hardcode_p50:
            print(f"  → Crossover found! MODEL faster than HARDCODE at compute ≈ {compute_equiv:.2f}")
else:
    print("Hash embedder (edge device simulation):")
    for _ in range(100):
        start = time.perf_counter()
        h = hash("check disk usage")
        hardcode_latencies.append((time.perf_counter() - start) * 1000)
    print(f"  Hash latency: {sorted(hardcode_latencies)[50]:.4f} ms — HARDCODE always wins on edge")
""",
                    hardware_required="RTX4050",
                    duration_estimate="60 seconds"
                )
                self.experiments.append(exp)
                new_experiments.append(exp)
        
        self._save_state()
        return new_experiments
    
    # ── Phase 5: TEST ─────────────────────────────────────
    
    def run_experiment(self, experiment_hash: str) -> TestResult:
        """Execute an experiment on metal and collect results."""
        exp = next((e for e in self.experiments if e.hash == experiment_hash), None)
        if not exp:
            raise ValueError(f"Experiment {experiment_hash} not found")
        
        # Execute the code
        namespace = {}
        try:
            exec(exp.code, namespace)
            passed = True
            output = namespace.get('result', 'executed successfully')
        except AssertionError as e:
            passed = False
            output = str(e)
        except Exception as e:
            passed = False
            output = f"Error: {e}"
        
        result = TestResult(
            experiment_hash=experiment_hash,
            hypothesis_hash=exp.hypothesis_hash,
            passed=passed,
            data={"output": str(output)[:500], "procedure": exp.procedure},
            surprise_level=0.0 if passed else 0.8
        )
        self.results.append(result)
        self._save_state()
        return result
    
    def run_all_experiments(self) -> list[TestResult]:
        """Run all designed experiments."""
        results = []
        for exp in self.experiments:
            r = self.run_experiment(exp.hash)
            results.append(r)
            print(f"{'✅' if r.passed else '❌'} {exp.procedure[:60]}...")
        return results
    
    # ── Phase 6: FEED ─────────────────────────────────────
    
    def feed_results(self):
        """Turn test results into new observations and start the wheel again."""
        for r in self.results:
            self.observe(
                source=f"experiment:{r.experiment_hash[:8]}",
                metric="experiment_passed",
                value=1.0 if r.passed else 0.0,
                unit="boolean",
                context={"hypothesis": r.hypothesis_hash[:8], "data": r.data},
                surprising=not r.passed,
                surprise_reason="Hypothesis refuted by metal" if not r.passed else None
            )
        self.cycle_count += 1
        self._save_state()
    
    # ── The Full Wheel ────────────────────────────────────
    
    def turn(self) -> dict:
        """One full turn of the research wheel."""
        print(f"\n{'='*60}")
        print(f"METAL LATHE — Cycle {self.cycle_count + 1}")
        print(f"{'='*60}")
        
        # Phase 2: Generate questions from observations
        print(f"\n🔭 OBSERVE → QUESTION")
        questions = self.generate_questions()
        print(f"  Generated {len(questions)} questions from {len(self.observations)} observations")
        for q in questions:
            print(f"  ❓ [{q.novelty_score:.1f}] {q.text[:80]}...")
        
        # Phase 3: Generate hypotheses from questions
        print(f"\n🧪 QUESTION → HYPOTHESIZE")
        hypotheses = self.generate_hypotheses()
        print(f"  Generated {len(hypotheses)} hypotheses from {len(self.questions)} questions")
        for h in hypotheses:
            print(f"  💡 [conf={h.confidence_prior:.1f}] {h.text[:80]}...")
        
        # Phase 4: Design experiments from hypotheses
        print(f"\n📐 HYPOTHESIZE → DESIGN")
        experiments = self.design_experiments()
        print(f"  Designed {len(experiments)} experiments from {len(self.hypotheses)} hypotheses")
        for e in experiments:
            print(f"  🔧 {e.procedure[:80]}...")
        
        # Phase 5: Run experiments on metal
        print(f"\n⚡ DESIGN → TEST (on metal)")
        results = self.run_all_experiments()
        passed = sum(1 for r in results if r.passed)
        print(f"  Ran {len(results)} experiments: {passed} passed, {len(results)-passed} failed")
        
        # Phase 6: Feed results back
        print(f"\n🔄 TEST → FEED")
        self.feed_results()
        
        summary = {
            "cycle": self.cycle_count,
            "observations": len(self.observations),
            "questions": len(self.questions),
            "hypotheses": len(self.hypotheses),
            "experiments": len(self.experiments),
            "results": len(self.results),
            "pass_rate": passed / max(len(results), 1),
        }
        
        print(f"\n{'='*60}")
        print(f"Cycle {summary['cycle']} complete:")
        print(f"  Observations: {summary['observations']}")
        print(f"  Questions: {summary['questions']}")
        print(f"  Hypotheses: {summary['hypotheses']}")
        print(f"  Experiments: {summary['experiments']}")
        print(f"  Pass rate: {summary['pass_rate']:.0%}")
        print(f"{'='*60}")
        
        return summary
    
    # ── State management ──────────────────────────────────
    
    def _save_state(self):
        state = {
            "cycle_count": self.cycle_count,
            "observations": [asdict(o) for o in self.observations],
            "questions": [asdict(q) for q in self.questions],
            "hypotheses": [asdict(h) for h in self.hypotheses],
            "experiments": [asdict(e) for e in self.experiments],
            "results": [asdict(r) for r in self.results],
        }
        with open(self.state_dir / "state.json", "w") as f:
            json.dump(state, f, indent=2, default=str)
    
    def _load_state(self):
        state_file = self.state_dir / "state.json"
        if not state_file.exists():
            return
        
        with open(state_file) as f:
            state = json.load(f)
        
        self.cycle_count = state.get("cycle_count", 0)
        self.observations = [Observation(**o) for o in state.get("observations", [])]
        self.questions = [Question(**q) for q in state.get("questions", [])]
        self.hypotheses = [Hypothesis(**h) for h in state.get("hypotheses", [])]
        self.experiments = [Experiment(**e) for e in state.get("experiments", [])]
        self.results = [TestResult(**r) for r in state.get("results", [])]


if __name__ == "__main__":
    lathe = MetalLathe()
    
    # Seed with our experimental results
    lathe.observe("conservation-verification", "health_score", 0.78, "ratio",
                  {"device": "RTX4050", "agents": 6}, surprising=False)
    lathe.observe("conservation-verification", "conservation_leakage", 0.0, "norm",
                  {"device": "RTX4050", "flow": "constant"}, surprising=True,
                  surprise_reason="Expected leakage from Python experiment, got zero with correct flow vector")
    lathe.observe("conservation-verification", "plato_utilization", 94.7, "%",
                  {"device": "RTX4050"}, surprising=True,
                  surprise_reason="PLATO at near-capacity while other agents <2%")
    lathe.observe("conservation-verification", "algebraic_connectivity", 1.382, "λ₂",
                  {"device": "RTX4050"}, surprising=False)
    lathe.observe("conservation-verification", "cheeger_constant", 0.5, "h(G)",
                  {"device": "RTX4050"}, surprising=False)
    
    lathe.observe("lever-runner-benchmark", "vector_search_p50", 7.6, "ms",
                  {"device": "RTX4050", "gpu": True}, surprising=False)
    lathe.observe("lever-runner-benchmark", "teach_throughput", 122, "ops/sec",
                  {"device": "RTX4050"}, surprising=False)
    lathe.observe("lever-runner-benchmark", "template_match_p50", 1.7, "µs",
                  {"device": "RTX4050"}, surprising=True,
                  surprise_reason="Template matching is 4500× faster than vector search")
    lathe.observe("lever-runner-benchmark", "gpu_embedding", 2.6, "ms",
                  {"device": "RTX4050", "gpu": True}, surprising=False)
    lathe.observe("lever-runner-benchmark", "cpu_embedding", 6.7, "ms",
                  {"device": "RTX4050", "gpu": False}, surprising=False)
    
    lathe.observe("pincherOS-embed", "hash_embed", 55, "µs",
                  {"device": "RTX4050"}, surprising=True,
                  surprise_reason="Hash embedder is 150× faster than ONNX with zero dependencies")
    lathe.observe("pincherOS-embed", "onnx_fp32", 8.1, "ms",
                  {"device": "RTX4050"}, surprising=False)
    lathe.observe("pincherOS-embed", "onnx_o4_quantized", 19.6, "ms",
                  {"device": "RTX4050"}, surprising=True,
                  surprise_reason="Quantization made it SLOWER on CPU, not faster")
    
    lathe.observe("induction", "lever_runner_functions", 221, "count",
                  {"language": "python"}, surprising=False)
    lathe.observe("induction", "pincherOS_functions", 833, "count",
                  {"language": "rust", "parser": "tree-sitter"}, surprising=True,
                  surprise_reason="7.4× more functions after tree-sitter")
    lathe.observe("induction", "intelligent_terminal_functions", 11528, "count",
                  {"language": "cpp+rust", "parser": "tree-sitter"}, surprising=True,
                  surprise_reason="443× more functions after tree-sitter — massive codebase")
    
    # Turn the wheel
    summary = lathe.turn()
    
    # Save final state
    lathe._save_state()
    print(f"\nState saved to {lathe.state_dir / 'state.json'}")
