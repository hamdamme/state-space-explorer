"""Interactive constrained state search."""

from dataclasses import asdict
import json

import networkx as nx
import plotly.graph_objects as go
import streamlit as st

from astar import get_heuristic, parse_blocked_states, solve, successors

ALGORITHMS = {"A*": "astar", "Dijkstra": "dijkstra", "Breadth-first": "bfs"}
SCENARIOS = {
    "Blocked-state detour": ("565", "777", "665,666,677"),
    "Leading zeros": ("009", "019", ""),
    "Transition constraint": ("000", "002", ""),
    "Unreachable goal": ("000", "999", "100,010,001"),
}

st.set_page_config(page_title="StateSpace Explorer", page_icon=":material/route:", layout="wide")
st.markdown("""<style>
.stApp {background:#f7f6f1;color:#263d36}
h1,h2,h3 {letter-spacing:-.025em}
.stButton button,.stFormSubmitButton button,.stDownloadButton button {border-radius:4px;min-height:44px}
[data-testid="stMetric"] {background:#eeeee6;padding:16px;border:1px solid #d9ddd5;border-radius:4px}
</style>""", unsafe_allow_html=True)
st.caption("ALGORITHMS / INTERACTIVE SYSTEMS")
st.title("StateSpace Explorer")
st.write("Explore how the A* search algorithm finds optimal paths through a state space with transition constraints and blocked states.")
st.caption("Three digits, one change per move. The same digit position cannot change twice in succession.")


def load_scenario():
    start, goal, blocked = SCENARIOS[st.session_state.scenario]
    st.session_state.start = start
    st.session_state.goal = goal
    st.session_state.blocked = blocked


st.selectbox("Example scenario", list(SCENARIOS), key="scenario", on_change=load_scenario)
if "start" not in st.session_state:
    load_scenario()
with st.form("search_form"):
    left, middle, right = st.columns([1, 1, 2])
    left.text_input("Start state", key="start", max_chars=3)
    middle.text_input("Goal state", key="goal", max_chars=3)
    right.text_input("Blocked states", key="blocked", placeholder="123, 456 — or leave empty")
    chosen = st.selectbox("Algorithm for playback", list(ALGORITHMS))
    submitted = st.form_submit_button("Explore search", type="primary")

if submitted:
    try:
        blocked = parse_blocked_states(st.session_state.blocked)
        results = {name: solve(st.session_state.start, st.session_state.goal, blocked, algorithm) for name, algorithm in ALGORITHMS.items()}
        st.session_state.search = {"start": st.session_state.start, "goal": st.session_state.goal, "blocked": blocked, "results": results, "chosen": chosen}
        st.session_state.position = 0
        st.session_state.playing = False
        st.session_state.run_id = st.session_state.get("run_id", 0) + 1
    except ValueError as error:
        st.session_state.search = None
        st.error(str(error))


def snapshot(result, position):
    initial = result.steps[0].node
    costs = {initial: 0}
    frontier = {initial}
    explored = set()
    edges = []
    for step in result.steps[:position]:
        frontier.discard(step.node)
        explored.add(step.node)
        costs[step.node] = step.cost
        for child in step.discovered:
            costs[child] = step.cost + 1
            frontier.add(child)
            edges.append((step.node, child))
    current = result.steps[position - 1].node if position else initial
    return costs, frontier, explored, edges, current


def state_label(node):
    return f"{node[0]} · last position {node[1] + 1 if node[1] >= 0 else 'none'}"


def render_graph(costs, frontier, explored, edges, current, result, position):
    important = list(result.path_states or ()) if position == len(result.steps) else []
    nodes = list(dict.fromkeys([current] + important + list(costs)))[:180]
    graph = nx.Graph()
    graph.add_nodes_from(nodes)
    shown = set(nodes)
    graph.add_edges_from((a, b) for a, b in edges if a in shown and b in shown)
    positions = nx.spring_layout(graph, seed=42, iterations=25)
    xs, ys = [], []
    for a, b in graph.edges:
        xs.extend([positions[a][0], positions[b][0], None])
        ys.extend([positions[a][1], positions[b][1], None])
    colors = ["#ba6b38" if node == current else "#37684f" if node in important else "#608dae" if node in frontier else "#a7ada8" for node in nodes]
    figure = go.Figure([
        go.Scatter(x=xs, y=ys, mode="lines", line={"color": "#ccd2cc", "width": 1}, hoverinfo="skip"),
        go.Scatter(x=[positions[n][0] for n in nodes], y=[positions[n][1] for n in nodes], mode="markers+text", text=[n[0] for n in nodes], textposition="top center", marker={"size": 15, "color": colors, "line": {"color": "white", "width": 1}}, customdata=[[n[0], n[1]] for n in nodes], hovertext=[state_label(n) for n in nodes], hovertemplate="%{hovertext}<extra></extra>", selected={"marker": {"size": 22}}, unselected={"marker": {"opacity": 0.8}}),
    ])
    figure.update_layout(height=470, margin={"l": 10, "r": 10, "t": 25, "b": 10}, showlegend=False, clickmode="event+select", dragmode="pan", plot_bgcolor="#f7f6f1", paper_bgcolor="#f7f6f1", xaxis={"visible": False}, yaxis={"visible": False})
    event = st.plotly_chart(figure, use_container_width=True, on_select="rerun", selection_mode="points", key=f"graph_{st.session_state.run_id}_{position}", config={"scrollZoom": False, "displaylogo": False})
    st.caption(f"Orange: current · Blue: frontier · Gray: explored · Green: final route. Showing {len(nodes)} of {len(costs)} discovered search states; graph lines show discovery connections.")
    points = event.selection.points
    if points and "customdata" in points[0]:
        value = points[0]["customdata"]
        selected = (value[0], int(value[1]))
        if selected in costs:
            return selected
    return None


search = st.session_state.get("search")
if search:
    result = search["results"][search["chosen"]]
    st.caption(f"Result snapshot: {search['start']} → {search['goal']} · {search['chosen']} · {len(search['blocked'])} blocked states. Submit again after changing the inputs.")
    a, b, c = st.columns(3)
    a.metric("Route length", f"{len(result.path) - 1} moves" if result.path else "Unreachable")
    b.metric("Expanded states", result.expanded)
    c.metric("Generated transitions", result.generated)
    if result.path:
        st.subheader("Optimal route")
        st.code(" → ".join(result.path), language=None, wrap_lines=True)
    else:
        st.warning("No route exists under these constraints. The search exhausted all reachable states.")

    st.subheader("Search playback")
    st.caption("Search states include the last changed digit. Two nodes with identical digits can have different legal next moves.")

    @st.fragment(run_every=0.8 if st.session_state.playing else None)
    def playback():
        total = len(result.steps)
        if st.session_state.playing:
            st.session_state.position = min(st.session_state.position + 1, total)
            if st.session_state.position == total:
                st.session_state.playing = False
                st.rerun()
        controls = st.columns(5)
        if controls[0].button("Pause" if st.session_state.playing else "Play", width="stretch"):
            if st.session_state.position == total:
                st.session_state.position = 0
            st.session_state.playing = not st.session_state.playing
            st.rerun()
        if controls[1].button("← Back", width="stretch"):
            st.session_state.position = max(0, st.session_state.position - 1)
            st.session_state.playing = False
            st.rerun()
        if controls[2].button("Next →", width="stretch"):
            st.session_state.position = min(total, st.session_state.position + 1)
            st.session_state.playing = False
            st.rerun()
        if controls[3].button("Replay", width="stretch"):
            st.session_state.position = 0
            st.session_state.playing = True
            st.rerun()
        if controls[4].button("Show result", width="stretch"):
            st.session_state.position = total
            st.session_state.playing = False
            st.rerun()
        def seek_position():
            st.session_state.position = st.session_state.seek

        st.session_state.seek = st.session_state.position
        position = st.slider("Expansion step", 0, total, key="seek", disabled=st.session_state.playing, on_change=seek_position)
        costs, frontier, explored, edges, current = snapshot(result, position)
        st.caption(f"Step {position} of {total} · Frontier {len(frontier)} · Explored {len(explored)}")
        chart, inspector = st.columns([3, 1])
        with chart:
            clicked = render_graph(costs, frontier, explored, edges, current, result, position)
        with inspector:
            st.subheader("Inspect state")
            selected = st.selectbox("Discovered state", list(costs), index=list(costs).index(current), format_func=state_label, key=f"inspect_{st.session_state.run_id}_{position}")
            node = clicked if clicked is not None else selected
            st.write(state_label(node))
            g = costs[node]
            h = get_heuristic(node[0], search["goal"]) if result.algorithm == "astar" else 0
            st.table({"Score": ["g · route cost", "h · heuristic", "f · total"], "Value": [g, h, g + h]})
            st.caption("Legal next transitions")
            moves = [f"{state} · position {digit + 1}" for state, digit in successors(node[0], node[1], search["blocked"])]
            st.write("\n\n".join(moves) if moves else "No legal successors.")
    playback()

    st.subheader("Algorithm comparison")
    rows = [{"Algorithm": name, "Moves": len(value.path) - 1 if value.path else None, "Expanded states": value.expanded, "Generated transitions": value.generated, "Time (ms)": round(value.elapsed_ms, 3)} for name, value in search["results"].items()]
    st.dataframe(rows, hide_index=True, width="stretch")
    st.caption("All algorithms use the same transitions and unit costs. Dijkstra and breadth-first search should agree in this model. Timing measures one instrumented run, including trace recording; it is not a benchmark.")
    with st.expander("Search trace"):
        st.code("\n".join(result.trace[:600]), language=None)
        if len(result.trace) > 600:
            st.caption("Showing the first 600 lines. Download the complete trace below.")
    export = {"start": search["start"], "goal": search["goal"], "blocked": sorted(search["blocked"]), "results": {name: asdict(value) for name, value in search["results"].items()}}
    downloads = st.columns(3)
    downloads[0].download_button("Download results · JSON", json.dumps(export, indent=2), file_name="search-results.json", mime="application/json")
    downloads[1].download_button("Download trace · TXT", "\n".join(result.trace), file_name="search-trace.txt", mime="text/plain")
    if result.path:
        downloads[2].download_button("Download route · CSV", "step,state\n" + "\n".join(f"{i},{state}" for i, state in enumerate(result.path)), file_name="route.csv", mime="text/csv")
else:
    st.info("Choose an example or enter your own states, then select Explore search.")
with st.expander("How the search works"):
    st.write("A* prioritizes f = g + h. Here, g counts moves and h is the sum of digit differences from the goal. Each move changes one digit by one, so h never overestimates the remaining moves. The transition constraint can require extra moves. Dijkstra uses g alone; breadth-first search uses a FIFO queue.")
st.caption("StateSpace Explorer · Hamdam Aynazarov")
st.markdown("[Source and documentation](https://github.com/hamdamme/state-space-explorer)")
