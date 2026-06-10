# Metal Lathe — The Research Wheel

![Python](https://img.shields.io/badge/language-Python%203.10-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![SuperInstance](https://img.shields.io/badge/fleet-SuperInstance-orange)

Takes experimental results, generates novel questions, develops hypothetical structures, designs experiments, tests on real hardware, and feeds results back in. The wheel turns itself.

## Why This Exists

Research without a loop is just data collection. Metal Lathe enforces a discipline: no speculation without a test, no hypothesis without an observation. Each cycle through the six phases produces testable knowledge grounded in real measurements — real hardware, real numbers, real failures.

It was built to answer questions about the SuperInstance agent ecosystem: call graph topology, conservation law violations in agent behavior graphs, tripartite decision crossover points, and cross-repo structural isomorphism.

## The Six Phases

```
    ┌──────────┐
    │ OBSERVE  │ ← What did we measure? What's surprising?
    └────┬─────┘
         ↓
    ┌──────────┐
    │ QUESTION │ ← What don't we understand? What's the edge case?
    └────┬─────┘
         ↓
    ┌───────────┐
    │HYPOTHESIZE│ ← What structure could explain the surprise?
    └────┬──────┘
         ↓
    ┌──────────┐
    │  DESIGN  │ ← How do we test this on real hardware?
    └────┬─────┘
         ↓
    ┌──────────┐
    │   TEST   │ ← Run the experiment, collect data
    └────┬─────┘
         ↓
    ┌──────────┐
    │   FEED   │ ← Results go back to OBSERVE
    └────┬─────┘
         │
         └──────→ cycle repeats
```

## Installation

```bash
# No package needed — single-file Python script
pip install numpy  # required for conservation-verification.py
python metal_lathe.py
```

## Usage

```python
from metal_lathe import MetalLathe, Observation

# Initialize the wheel
lathe = MetalLathe(state_dir="~/.metal-lathe")

# Phase 1: OBSERVE — record what you measured
lathe.observe(
    source="lever-runner",
    metric="call_degree:process_request",
    value=47,
    unit="edges",
    context={"function": "process_request", "file": "main.rs"},
    surprising=True,
    surprise_reason="47 callers — hub function"
)

# Load observations from open-mind induction results
lathe.observe_from_results("induction-results/lever-runner/functions.json")

# Turn the wheel once: QUESTION → HYPOTHESIZE → DESIGN → TEST → FEED
summary = lathe.turn()
print(f"Cycle {summary['cycle']}: {summary['experiments_ran']} experiments, "
      f"{summary['passed']} passed")
```

### Conservation Verification

The companion script `conservation-verification.py` uses spectral graph theory to verify agent behavior graphs obey conservation laws:

```python
from conservation_verification import compute_laplacian, verify_conservation

L = compute_laplacian(ADJACENCY)
eigenvalues = spectral_budget(L)
lambda_2, h_lower, h_upper = cheeger_constant(L)

# Check for budget leaks: L · f = 0 at steady state
leakage = verify_conservation(L, flow_vector)
# If leakage > 0, an agent is exceeding its budget
```

The conservation law γ + η = C governs the ecosystem: growth plus dissipation equals a constant. The Laplacian eigenvalue spectrum reveals where the budget is spent.

## API Reference

### Core Data Types

```python
class Phase(Enum):
    OBSERVE = "observe"
    QUESTION = "question"
    HYPOTHESIZE = "hypothesize"
    DESIGN = "design"
    TEST = "test"
    FEED = "feed"

@dataclass
class Observation:
    source: str           # experiment/repo/measurement
    metric: str           # what was measured
    value: float          # the number
    unit: str             # ms, tokens, %, etc.
    context: dict         # hardware, config, conditions
    surprising: bool      # did this surprise us?
    surprise_reason: str | None

@dataclass
class Question:
    text: str
    source_observations: list[str]  # hashes of source observations
    novelty_score: float  # 0-1
    testable: bool
    tags: list[str]

@dataclass
class Hypothesis:
    text: str
    questions: list[str]        # question hashes addressed
    predictions: list[str]      # expected outcomes if true
    structure: dict             # formal/mathematical description
    testable_on: list[str]      # hardware targets
    confidence_prior: float     # 0-1

@dataclass
class Experiment:
    hypothesis_hash: str
    procedure: str
    expected_result: str
    code: str                   # actual executable Python
    hardware_required: str
    duration_estimate: str

@dataclass
class TestResult:
    experiment_hash: str
    hypothesis_hash: str
    passed: bool
    data: dict
    surprise_level: float       # 0-1
```

### MetalLathe Methods

| Method | Phase | Description |
|--------|-------|-------------|
| `observe(source, metric, value, unit, context, ...)` | OBSERVE | Record a raw experimental measurement |
| `observe_from_results(results_file)` | OBSERVE | Load observations from induction JSON |
| `generate_questions() → list[Question]` | QUESTION | Detect 7 patterns: surprise clustering, distribution anomalies, conservation violations, cross-repo isomorphism, hardware scaling, power-law degree, tripartite balance |
| `generate_hypotheses() → list[Hypothesis]` | HYPOTHESIZE | Map questions to testable structures with predictions |
| `design_experiments() → list[Experiment]` | DESIGN | Generate runnable Python code for each hypothesis |
| `run_experiment(hash) → TestResult` | TEST | Execute experiment code and collect results |
| `run_all_experiments() → list[TestResult]` | TEST | Run all designed experiments |
| `feed_results()` | FEED | Convert test results into new observations |
| `turn() → dict` | Full cycle | Execute one complete turn of the wheel |

### Question Generation Patterns

The `generate_questions()` method detects seven patterns in observations:

1. **Surprise clustering** — Multiple surprising observations in the same metric domain
2. **Distribution anomalies** — Outliers beyond 2σ in measured values
3. **Conservation violations** — Non-trivial leakage (γ + η ≠ C) in behavior graphs
4. **Cross-repo structural isomorphism** — Observations from multiple sources suggesting shared topology
5. **Hardware-performance correlation** — Performance measurements across different hardware profiles
6. **Power-law degree distribution** — Call graph degrees spanning 2+ orders of magnitude
7. **Tripartite decision balance** — Distribution of HARDCODE/MODEL/CACHED decisions

### Conservation Verification Functions

| Function | Signature | Returns |
|----------|-----------|---------|
| `compute_laplacian(adj)` | `ndarray → ndarray` | Laplacian L = D − A |
| `spectral_budget(L)` | `ndarray → ndarray` | Sorted eigenvalues (conservation budget spectrum) |
| `cheeger_constant(L)` | `ndarray → (λ₂, h_lower, h_upper)` | Algebraic connectivity and Cheeger bounds |
| `verify_conservation(L, f)` | `(ndarray, ndarray) → float` | Leakage ‖Lf‖ — should be ≈0 at steady state |

## Architecture

```
metal-lathe/
├── metal_lathe.py               # The research wheel (MetalLathe class)
│   ├── Phase 1: observe()
│   ├── Phase 2: generate_questions()    — 7 pattern detectors
│   ├── Phase 3: generate_hypotheses()   — question→structure mapping
│   ├── Phase 4: design_experiments()    — hypothesis→runnable code
│   ├── Phase 5: run_experiment()        — exec() on metal
│   └── Phase 6: feed_results()          — results→observations
├── conservation-verification.py  # Spectral graph theory verification
│   ├── compute_laplacian()              # L = D - A
│   ├── spectral_budget()                # eigenvalue spectrum
│   ├── cheeger_constant()               # algebraic connectivity
│   └── verify_conservation()            # ‖Lf‖ leakage check
└── docs/
```

## Related SuperInstance Crates

- **conservation-spectral-topology** — Rust implementation of spectral graph conservation analysis
- **lever-runner** — Execution agent whose call graphs are analyzed by Metal Lathe
- **pincherOS** — Memory/reflex agent in the ecosystem adjacency matrix
- **intelligent-terminal** — Terminal agent tested for spectral isomorphism with other repos
- **open-mind** — Induction engine that produces the `functions.json` files fed into `observe_from_results()`

## License

MIT
