import contextlib
from collections import deque
import io
import random
import unittest

from astar import a_star_search, main, parse_blocked_states, solve


def reference_distance(start, goal, blocked):
    queue = deque([(start, -1, 0)])
    seen = {(start, -1)}
    while queue:
        state, last, distance = queue.popleft()
        if state == goal:
            return distance
        for index in range(3):
            if index == last:
                continue
            for delta in (-1, 1):
                digits = list(state)
                value = int(digits[index]) + delta
                if not 0 <= value <= 9:
                    continue
                digits[index] = str(value)
                next_state = "".join(digits)
                key = (next_state, index)
                if next_state not in blocked and key not in seen:
                    seen.add(key)
                    queue.append((next_state, index, distance + 1))
    return None


class SolverTests(unittest.TestCase):
    def assert_valid_route(self, path, start, goal, blocked):
        self.assertEqual(path[0], start)
        self.assertEqual(path[-1], goal)
        previous = -1
        for a, b in zip(path, path[1:]):
            self.assertNotIn(b, blocked)
            changes = [i for i in range(3) if a[i] != b[i]]
            self.assertEqual(len(changes), 1)
            digit = changes[0]
            self.assertNotEqual(digit, previous)
            self.assertEqual(abs(int(a[digit]) - int(b[digit])), 1)
            previous = digit

    def test_leading_zeros(self):
        result = solve("009", "019")
        self.assertEqual(result.path, ("009", "019"))

    def test_same_digit_requires_intervening_move(self):
        result = solve("000", "002")
        self.assertEqual(len(result.path) - 1, 4)
        self.assert_valid_route(result.path, "000", "002", set())

    def test_start_equals_goal(self):
        self.assertEqual(solve("000", "000").path, ("000",))

    def test_unreachable(self):
        result = solve("000", "999", {"100", "010", "001"})
        self.assertIsNone(result.path)
        self.assertEqual(result.expanded, 1)

    def test_invalid_states(self):
        for value in ("12", "1000", "abc", "-01", "１２３", True, -1, 1000):
            with self.subTest(value=value), self.assertRaises(ValueError):
                solve(value, "123")
        for blocked in ({"123"}, {"456"}, {"x"}):
            with self.subTest(blocked=blocked), self.assertRaises(ValueError):
                solve("123", "456", blocked)

    def test_blocked_input(self):
        self.assertEqual(parse_blocked_states("[]"), set())
        self.assertEqual(parse_blocked_states(" 009, 019 "), {"009", "019"})
        with self.assertRaises(ValueError):
            parse_blocked_states("123,wrong")

    def test_optimality_against_breadth_first_search(self):
        rng = random.Random(42)
        for _ in range(30):
            start, goal = (f"{rng.randrange(1000):03d}" for _ in range(2))
            blocked = {f"{rng.randrange(1000):03d}" for _ in range(80)} - {start, goal}
            expected = reference_distance(start, goal, blocked)
            for algorithm in ("astar", "dijkstra", "bfs"):
                result = solve(start, goal, blocked, algorithm)
                with self.subTest(start=start, goal=goal, algorithm=algorithm):
                    self.assertEqual(None if result.path is None else len(result.path) - 1, expected)
                    self.assertEqual(result.expanded, len(result.steps))
                    if result.path:
                        self.assert_valid_route(result.path, start, goal, blocked)
                        self.assertEqual(tuple(node[0] for node in result.path_states), result.path)

    def test_compatibility_and_trace(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            path, trace = a_star_search("565", "777", {665, 666, 677})
        self.assertEqual(output.getvalue(), "")
        self.assertTrue(trace)
        self.assert_valid_route(path, "565", "777", {"665", "666", "677"})

    def test_command_line_empty_blocked_list(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(["S=000", "G=000", "bad=[]"])
        self.assertEqual(status, 0)
        self.assertIn("Optimal Path: 000", output.getvalue())


if __name__ == "__main__":
    unittest.main()
