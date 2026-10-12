# StateSpace Explorer

An interactive tool that uses the A* search algorithm to find optimal paths through a state space with transition constraints and blocked states.

## Features

- A*, Dijkstra, and breadth-first search on the same state model.
- Play, pause, replay, manual stepping, and seeking through recorded search expansions.
- Interactive discovery graph with frontier, explored states, current state, and final route.
- Node inspection with route cost, heuristic, total score, and legal successors.
- Editable inputs and scenarios covering detours, leading zeros, transition constraints, and unreachable goals.
- Comparison of route lengths, expansions, generated transitions, and elapsed time.
- JSON results, CSV route, and text trace downloads.

## Model and correctness

The example uses three-digit states from `000` to `999`. Each move changes one digit by one, avoids blocked states, and stays within digit bounds. The same position cannot change on consecutive moves. Every transition costs one.

A search state includes the digits and last changed position. This distinction matters: identical digits reached through different positions have different successors. A* uses a heap and relaxes better routes. Dijkstra uses accumulated cost; breadth-first search uses a FIFO queue.

A* uses the sum of digit differences as its heuristic. Each legal move changes that sum by at most one, making the heuristic admissible and consistent. Transition constraints can increase the required moves. Optimality is checked against an independent breadth-first implementation.

This is a bounded state-space demonstration, not a geographic route planner. Graphs show discovery connections rather than every possible transition. The graph displays at most 180 nodes for readability; search, inspection, and exports retain the complete result. The trace preview displays at most 600 lines. Timing includes trace recording and is a single run, not a performance benchmark.

## Setup

Use Python 3.12:

```sh
git clone https://github.com/hamdamme/state-space-explorer.git
cd state-space-explorer
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

On Windows, use `.venv\Scripts\python` instead of `.venv/bin/python`. Open the URL shown by Streamlit.

## Command line

```sh
python astar.py --start 565 --goal 777 --blocked 665,666,677
python astar.py --start 000 --goal 002 --algorithm bfs --trace
```

The original `S=565 G=777 "bad=[665,666,677]"` syntax remains supported. Exit codes: 0 for a route, 1 for unreachable, 2 for invalid arguments.

## Testing

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Tests cover route legality, optimality across 30 reproducible generated scenarios for all three algorithms, invalid input, blocked endpoints, leading zeros, unreachable goals, CLI compatibility, and Streamlit input and playback behavior. GitHub Actions runs the suite on Python 3.12.

## Architecture

- `astar.py`: validation, transitions, algorithms, immutable result and expansion records, CLI.
- `app.py`: controls, playback snapshots, graph, comparison, and exports.
- `tests/`: solver reference checks and Streamlit app tests.
- `.streamlit/config.toml`: application theme.

The interface replays completed searches rather than running an algorithm on every frame. Submitted results retain their original input snapshot until another search is submitted.

## Deployment and license

Existing demo: [a-search.onrender.com](https://a-search.onrender.com/). Render build command: `pip install -r requirements.txt`. Start command:

```sh
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

Deployment verification and planned work are recorded in [ROADMAP.md](ROADMAP.md).

MIT license. Copyright 2025 Hamdam Aynazarov. See [LICENSE](LICENSE).
