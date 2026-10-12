"""A* search over three-digit states, by Hamdam Aynazarov."""

import argparse
from collections import deque
from dataclasses import dataclass
import heapq
from itertools import count
import sys
from time import perf_counter

State = tuple[str, int]


def normalize_state(value):
    """Return three digits without losing leading zeros."""
    if isinstance(value, int) and not isinstance(value, bool):
        if 0 <= value <= 999:
            return f"{value:03d}"
    elif isinstance(value, str) and len(value) == 3 and value.isascii() and value.isdigit():
        return value
    raise ValueError("States must contain exactly three digits (000–999).")


def parse_blocked_states(text):
    text = text.strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1].strip()
    if not text:
        return set()
    return {normalize_state(part.strip()) for part in text.split(",")}


def get_heuristic(start, goal):
    start, goal = normalize_state(start), normalize_state(goal)
    return sum(abs(int(a) - int(b)) for a, b in zip(start, goal))


def successors(state, last_digit, blocked):
    for index, digit in enumerate(state):
        if index == last_digit:
            continue
        for delta in (1, -1):
            value = int(digit) + delta
            if 0 <= value <= 9:
                candidate = state[:index] + str(value) + state[index + 1:]
                if candidate not in blocked:
                    yield candidate, index


@dataclass(frozen=True)
class SearchStep:
    node: State
    cost: int
    heuristic: int
    discovered: tuple[State, ...]


@dataclass(frozen=True)
class SearchResult:
    path: tuple[str, ...] | None
    expanded: int
    generated: int
    trace: tuple[str, ...]
    steps: tuple[SearchStep, ...]
    elapsed_ms: float
    algorithm: str
    path_states: tuple[State, ...] | None


def solve(start, goal, blocked=(), algorithm="astar"):
    if algorithm not in {"astar", "dijkstra", "bfs"}:
        raise ValueError("Unknown search algorithm.")
    started = perf_counter()
    start, goal = normalize_state(start), normalize_state(goal)
    blocked = {normalize_state(value) for value in blocked}
    if start in blocked or goal in blocked:
        raise ValueError("Start and goal must not be blocked states.")
    initial = (start, -1)
    sequence = count()
    heuristic = get_heuristic(start, goal) if algorithm == "astar" else 0
    frontier = [(heuristic, heuristic, next(sequence), 0, initial)]
    queue = deque([(0, initial)])
    steps = []
    best_cost = {initial: 0}
    parents = {initial: None}
    trace = []
    expanded = generated = 0
    while queue if algorithm == "bfs" else frontier:
        if algorithm == "bfs":
            cost, current = queue.popleft()
        else:
            _, _, _, cost, current = heapq.heappop(frontier)
        if cost != best_cost[current]:
            continue
        state, last_digit = current
        expanded += 1
        trace.append(f"Expanding Node: {state} with cost {cost}; last digit {last_digit}")
        if state == goal:
            steps.append(SearchStep(current, cost, get_heuristic(state, goal) if algorithm == "astar" else 0, ()))
            path = []
            path_states = []
            node = current
            while node is not None:
                path.append(node[0])
                path_states.append(node)
                node = parents[node]
            return SearchResult(tuple(reversed(path)), expanded, generated, tuple(trace), tuple(steps), (perf_counter() - started) * 1000, algorithm, tuple(reversed(path_states)))
        discovered = []
        for candidate, digit in successors(state, last_digit, blocked):
            generated += 1
            key = (candidate, digit)
            new_cost = cost + 1
            if new_cost < best_cost.get(key, float("inf")):
                best_cost[key] = new_cost
                parents[key] = current
                heuristic = get_heuristic(candidate, goal) if algorithm == "astar" else 0
                discovered.append(key)
                if algorithm == "bfs":
                    queue.append((new_cost, key))
                else:
                    heapq.heappush(frontier, (new_cost + heuristic, heuristic, next(sequence), new_cost, key))
                trace.append(f"  Generated successor: {candidate} from digit {digit}; cost {new_cost}")
        steps.append(SearchStep(current, cost, get_heuristic(state, goal) if algorithm == "astar" else 0, tuple(discovered)))
    return SearchResult(None, expanded, generated, tuple(trace), tuple(steps), (perf_counter() - started) * 1000, algorithm, None)


def a_star_search(start, goal, bad):
    """Compatibility interface returning the path and expansion trace."""
    result = solve(start, goal, bad)
    return list(result.path) if result.path is not None else None, list(result.trace)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Find a shortest route between three-digit states.")
    parser.add_argument("--start", required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--blocked", default="")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--algorithm", choices=("astar", "dijkstra", "bfs"), default="astar")
    arguments = sys.argv[1:] if argv is None else argv
    if arguments == ["help"]:
        arguments = ["--help"]
    converted = []
    legacy = {"S": "--start", "G": "--goal", "bad": "--blocked"}
    for argument in arguments:
        key, separator, value = argument.partition("=")
        converted.extend([legacy[key], value] if separator and key in legacy else [argument])
    args = parser.parse_args(converted)
    try:
        result = solve(args.start, args.goal, parse_blocked_states(args.blocked), args.algorithm)
    except ValueError as error:
        parser.error(str(error))
    if args.trace:
        print("\n".join(result.trace))
    if result.path is None:
        print("No route exists under these constraints.")
        return 1
    print("Optimal Path:", " -> ".join(result.path))
    print(f"Moves: {len(result.path) - 1}; expanded search states: {result.expanded}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
