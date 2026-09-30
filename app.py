import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
from pyvis.network import Network
import random
import tempfile
import heapq
import time

st.set_page_config(layout="wide", page_title="Graph Algorithm Visualizer", page_icon="🕸️")

# --- Session State Initialization ---
if 'G' not in st.session_state:
    st.session_state.G = nx.Graph()
if 'heuristics' not in st.session_state:
    st.session_state.heuristics = {}
if 'history' not in st.session_state:
    st.session_state.history = []
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'playing' not in st.session_state:
    st.session_state.playing = False
if 'speed' not in st.session_state:
    st.session_state.speed = 1.0
if 'positions' not in st.session_state:
    st.session_state.positions = {}

def update_positions():
    if st.session_state.G.number_of_nodes() > 0:
        pos = nx.spring_layout(st.session_state.G, seed=42)
        st.session_state.positions = {n: (coords[0]*400, coords[1]*400) for n, coords in pos.items()}

def add_edge(u, v, weight):
    u = u.strip()
    v = v.strip()
    if u and v:
        st.session_state.G.add_edge(u, v, weight=weight)
        if u not in st.session_state.heuristics:
            st.session_state.heuristics[u] = 0
        if v not in st.session_state.heuristics:
            st.session_state.heuristics[v] = 0
        update_positions()

def set_heuristic(node, h_val):
    node = node.strip()
    if node in st.session_state.G.nodes:
        st.session_state.heuristics[node] = h_val

def generate_random_graph(num_nodes, probability):
    G = nx.erdos_renyi_graph(num_nodes, probability, seed=random.randint(0, 1000))
    H = nx.Graph()
    for u, v in G.edges():
        H.add_edge(str(u), str(v), weight=random.randint(1, 20))
    st.session_state.G = H
    st.session_state.heuristics = {str(n): random.randint(1, 10) for n in H.nodes()}
    update_positions()
    st.session_state.history = [] 
    st.session_state.playing = False
    st.session_state.step = 0

# --- Tracking Tables ---
def get_bfs_table(G, queue, visited_set, parent):
    table = []
    for n in G.nodes():
        if n in queue: status = "In Queue"
        elif n in visited_set: status = "Visited"
        else: status = "Unvisited"
        table.append({"Node": str(n), "Status": status, "Parent Node": str(parent.get(n, "-"))})
    return table

def get_dijkstra_table(G, distances, visited, parent):
    table = []
    for n in G.nodes():
        dist = distances[n] if distances[n] != float('inf') else "∞"
        if n in visited: status = "Visited"
        elif distances[n] != float('inf'): status = "In Priority Queue"
        else: status = "Unvisited"
        table.append({"Node": str(n), "Shortest Distance": str(dist), "Status": status, "Parent Node": str(parent.get(n, "-"))})
    return table

def get_astar_table(G, distances, heuristics, visited, parent):
    table = []
    for n in G.nodes():
        g_val = distances[n] if distances[n] != float('inf') else "∞"
        h_val = heuristics.get(n, 0)
        f_val = (distances[n] + h_val) if distances[n] != float('inf') else "∞"
        if n in visited: status = "Visited"
        elif distances[n] != float('inf'): status = "In Priority Queue"
        else: status = "Unvisited"
        table.append({"Node": str(n), "g(n) - Cost": str(g_val), "h(n) - Heuristic": str(h_val), "f(n) = g+h": str(f_val), "Status": status, "Parent Node": str(parent.get(n, "-"))})
    return table

def get_kruskal_table(edges, edge_status):
    table = []
    for u, v, d in edges:
        weight = d.get('weight', 1)
        table.append({"Edge": f"{u} - {v}", "Weight": str(weight), "Status": edge_status.get((u, v), "Pending")})
    return table

# --- Algorithms ---
def bfs(G, start, target=None):
    if start not in G: return []
    visited = []
    queue = [start]
    visited_set = {start}
    path_edges = []
    parent = {}
    history = []
    
    while queue:
        node = queue.pop(0)
        visited.append(node)
        if node in parent:
            path_edges.append((parent[node], node))
            
        history.append({
            "highlight_nodes": list(visited),
            "highlight_edges": list(path_edges),
            "current_node": node,
            "log": f"Visiting node {node}...",
            "table": get_bfs_table(G, queue, visited_set, parent)
        })
            
        if node == target:
            history.append({
                "highlight_nodes": list(visited),
                "highlight_edges": list(path_edges),
                "current_node": node,
                "log": f"Target {target} found!",
                "table": get_bfs_table(G, queue, visited_set, parent)
            })
            break
            
        for neighbor in G.neighbors(node):
            if neighbor not in visited_set:
                visited_set.add(neighbor)
                parent[neighbor] = node
                queue.append(neighbor)
                
    return history

def dfs(G, start, target=None):
    if start not in G: return []
    visited = []
    stack = [start]
    visited_set = set()
    path_edges = []
    parent = {}
    history = []
    
    def get_dfs_table():
        table = []
        for n in G.nodes():
            if n in stack: status = "In Stack"
            elif n in visited_set: status = "Visited"
            else: status = "Unvisited"
            table.append({"Node": str(n), "Status": status, "Parent Node": str(parent.get(n, "-"))})
        return table
        
    while stack:
        node = stack.pop()
        if node not in visited_set:
            visited_set.add(node)
            visited.append(node)
            
            if node in parent:
                path_edges.append((parent[node], node))
                
            history.append({
                "highlight_nodes": list(visited),
                "highlight_edges": list(path_edges),
                "current_node": node,
                "log": f"Visiting node {node}...",
                "table": get_dfs_table()
            })
                
            if node == target:
                history.append({
                    "highlight_nodes": list(visited),
                    "highlight_edges": list(path_edges),
                    "current_node": node,
                    "log": f"Target {target} found!",
                    "table": get_dfs_table()
                })
                break
                
            for neighbor in list(G.neighbors(node))[::-1]:
                if neighbor not in visited_set:
                    stack.append(neighbor)
                    parent[neighbor] = node
                    
    return history

def dijkstra(G, start, target):
    if start not in G or target not in G: return []
    
    distances = {n: float('inf') for n in G.nodes()}
    distances[start] = 0
    pq = [(0, start)]
    visited = set()
    parent = {}
    
    history = []
    highlight_edges = []
    visited_list = []
    
    while pq:
        dist, node = heapq.heappop(pq)
        
        if node in visited:
            continue
            
        visited.add(node)
        visited_list.append(node)
        
        if node in parent:
            highlight_edges.append((parent[node], node))
            
        history.append({
            "highlight_nodes": list(visited_list),
            "highlight_edges": list(highlight_edges),
            "current_node": node,
            "log": f"Visiting node {node} (Accumulated cost from start: {dist})",
            "table": get_dijkstra_table(G, distances, visited, parent)
        })
        
        if node == target:
            path = []
            curr = target
            while curr in parent:
                path.append(curr)
                curr = parent[curr]
            path.append(start)
            path.reverse()
            path_e = list(zip(path, path[1:]))
            history.append({
                "highlight_nodes": path,
                "highlight_edges": path_e,
                "current_node": target,
                "log": f"Shortest path found! Total Cost: {dist}\n\nPath: {' -> '.join(path)}",
                "table": get_dijkstra_table(G, distances, visited, parent)
            })
            break
            
        for neighbor in G.neighbors(node):
            weight = G[node][neighbor].get('weight', 1)
            new_dist = dist + weight
            
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                parent[neighbor] = node
                heapq.heappush(pq, (new_dist, neighbor))
                
    return history

def astar(G, start, target, heuristics):
    if start not in G or target not in G: return []
    
    distances = {n: float('inf') for n in G.nodes()}
    distances[start] = 0
    pq = [(0 + heuristics.get(start, 0), 0, start)]
    visited = set()
    parent = {}
    
    history = []
    highlight_edges = []
    visited_list = []
    
    while pq:
        f, g, node = heapq.heappop(pq)
        
        if node in visited:
            continue
            
        visited.add(node)
        visited_list.append(node)
        
        if node in parent:
            highlight_edges.append((parent[node], node))
            
        history.append({
            "highlight_nodes": list(visited_list),
            "highlight_edges": list(highlight_edges),
            "current_node": node,
            "log": f"Visiting node {node}\n- Cost from start (g): {g}\n- Heuristic to target (h): {heuristics.get(node,0)}\n- Estimated total (f=g+h): {f}",
            "table": get_astar_table(G, distances, heuristics, visited, parent)
        })
        
        if node == target:
            path = []
            curr = target
            while curr in parent:
                path.append(curr)
                curr = parent[curr]
            path.append(start)
            path.reverse()
            path_e = list(zip(path, path[1:]))
            history.append({
                "highlight_nodes": path,
                "highlight_edges": path_e,
                "current_node": target,
                "log": f"A* Path found! Total Cost: {g}\n\nPath: {' -> '.join(path)}",
                "table": get_astar_table(G, distances, heuristics, visited, parent)
            })
            break
            
        for neighbor in G.neighbors(node):
            weight = G[node][neighbor].get('weight', 1)
            new_g = g + weight
            new_f = new_g + heuristics.get(neighbor, 0)
            
            if new_g < distances[neighbor]:
                distances[neighbor] = new_g
                parent[neighbor] = node
                heapq.heappush(pq, (new_f, new_g, neighbor))
                
    return history

def mst_kruskal(G):
    if G.number_of_nodes() == 0: return []
    
    edges = list(G.edges(data=True))
    edges.sort(key=lambda x: x[2].get('weight', 1))
    
    parent = {n: n for n in G.nodes()}
    def find(i):
        if parent[i] == i:
            return i
        parent[i] = find(parent[i])
        return parent[i]
        
    def union(i, j):
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            parent[root_i] = root_j
            return True
        return False
        
    history = []
    mst_edges = []
    mst_nodes = set()
    total_cost = 0
    edge_status = {(u, v): "Pending" for u,v,d in edges}
    
    history.append({
        "highlight_nodes": [],
        "highlight_edges": [],
        "current_node": None,
        "log": "Starting Kruskal's MST (Edges sorted by weight).",
        "table": get_kruskal_table(edges, edge_status)
    })
    
    for u, v, d in edges:
        weight = d.get('weight', 1)
        edge_status[(u, v)] = "Inspecting..."
        
        history.append({
            "highlight_nodes": list(mst_nodes) + [u, v],
            "highlight_edges": list(mst_edges) + [(u, v)],
            "current_node": None,
            "log": f"Inspecting edge: {u}-{v} (Weight: {weight})",
            "table": get_kruskal_table(edges, edge_status)
        })
        
        if union(u, v):
            mst_edges.append((u, v))
            mst_nodes.add(u)
            mst_nodes.add(v)
            total_cost += weight
            edge_status[(u, v)] = "Added to MST"
            
            history.append({
                "highlight_nodes": list(mst_nodes),
                "highlight_edges": list(mst_edges),
                "current_node": None,
                "log": f"Accepted edge {u}-{v} into MST. Current total weight: {total_cost}",
                "table": get_kruskal_table(edges, edge_status)
            })
        else:
            edge_status[(u, v)] = "Discarded (Creates Cycle)"
            history.append({
                "highlight_nodes": list(mst_nodes),
                "highlight_edges": list(mst_edges),
                "current_node": None,
                "log": f"Edge {u}-{v} creates a cycle. Discarded!",
                "table": get_kruskal_table(edges, edge_status)
            })
            
    history.append({
        "highlight_nodes": list(mst_nodes),
        "highlight_edges": list(mst_edges),
        "current_node": None,
        "log": f"Minimum Spanning Tree (MST) Complete! Total Weight: {total_cost}",
        "table": get_kruskal_table(edges, edge_status)
    })
            
    return history

# --- UI ---
st.title("Graph Traversal Visualizer 🕸️")

with st.sidebar:
    st.header("1. Graph Construction")
    
    st.subheader("Add Edge")
    col1, col2 = st.columns(2)
    with col1:
        u_node = st.text_input("Node A")
    with col2:
        v_node = st.text_input("Node B")
    weight = st.number_input("Weight", value=1.0, min_value=0.0)
    if st.button("Add Edge"):
        add_edge(u_node, v_node, weight)
        st.session_state.history = []
        st.session_state.playing = False
        st.session_state.step = 0
        st.success(f"Added: {u_node} - {v_node} (Weight: {weight})")
        
    st.subheader("Set Heuristic (for A*)")
    nodes = list(st.session_state.G.nodes())
    h_node = st.selectbox("Select Node", options=[""] + nodes if nodes else [""])
    h_val = st.number_input("Heuristic Value", value=0.0)
    if st.button("Save Heuristic"):
        if h_node:
            set_heuristic(h_node, h_val)
            st.session_state.history = []
            st.success(f"Saved h({h_node}) = {h_val}")
            
    st.subheader("Random Graph Generator")
    rand_nodes = st.slider("Number of Nodes", 5, 20, 8)
    rand_prob = st.slider("Edge Probability", 0.1, 1.0, 0.3)
    if st.button("Generate Random Graph"):
        generate_random_graph(rand_nodes, rand_prob)
        st.success("Graph generated successfully!")
        
    if st.button("Clear Entire Graph", type="primary"):
        st.session_state.G.clear()
        st.session_state.heuristics.clear()
        st.session_state.history = []
        st.session_state.positions.clear()
        st.session_state.playing = False
        st.session_state.step = 0
        st.success("Graph cleared!")

    st.header("2. Algorithm Selection")
    algo = st.selectbox("Algorithm:", ["BFS", "DFS", "Dijkstra", "A*", "MST (Kruskal)"])
    
    start_node = st.selectbox("Start Node", options=nodes if nodes else [""])
    target_node = st.selectbox("Target Node", options=nodes if nodes else [""])
    
    if st.button("Run Visualization 🚀", type="primary"):
        G = st.session_state.G
        if G.number_of_nodes() > 0:
            if algo == "BFS": st.session_state.history = bfs(G, start_node, target_node)
            elif algo == "DFS": st.session_state.history = dfs(G, start_node, target_node)
            elif algo == "Dijkstra": st.session_state.history = dijkstra(G, start_node, target_node)
            elif algo == "A*": st.session_state.history = astar(G, start_node, target_node, st.session_state.heuristics)
            elif algo == "MST (Kruskal)": st.session_state.history = mst_kruskal(G)
            
            st.session_state.step = 0
            st.session_state.playing = False

# --- Visualization Logic ---
def create_pyvis_graph(G, highlight_nodes=None, highlight_edges=None, current_node=None):
    if highlight_nodes is None: highlight_nodes = []
    if highlight_edges is None: highlight_edges = []
        
    net = Network(height="600px", width="100%", bgcolor="#0E1117", font_color="white")
    # Completely disable physics so nodes stay absolutely still between frames!
    net.toggle_physics(False)
    
    for node in G.nodes():
        if node == current_node:
            color = "#f1c40f" # Yellow
            size = 35
        elif node in highlight_nodes:
            if node == start_node and algo != "MST (Kruskal)":
                color = "#2ecc71" # Green
            elif node == target_node and algo != "MST (Kruskal)":
                color = "#e67e22" # Orange
            else:
                color = "#e74c3c" # Red
            size = 25
        else:
            color = "#3498db" # Blue
            size = 15
            
        label = f"{node} (h={st.session_state.heuristics.get(node, 0)})" if algo == "A*" else str(node)
        
        # Get frozen positions generated by networkx layout
        x, y = st.session_state.positions.get(node, (random.randint(-200, 200), random.randint(-200, 200)))
        
        net.add_node(node, label=label, color=color, title=f"Node: {node}", size=size,
                     x=x, y=y, fixed=True, physics=False, # Pin node in place
                     font={"color": "white", "size": 20, "bold": True})
        
    for u, v, d in G.edges(data=True):
        weight = d.get('weight', 1)
        is_highlighted = (u, v) in highlight_edges or (v, u) in highlight_edges
        
        color = "#e74c3c" if is_highlighted else "#888888"
        width = 5 if is_highlighted else 2
        
        net.add_edge(u, v, title=f"Weight: {weight}", label=str(weight), color=color, width=width,
                     physics=False, # Disable edge physics too
                     font={"color": "white", "size": 16, "background": "rgba(231, 76, 60, 0.7)" if is_highlighted else "rgba(100, 100, 100, 0.7)", "strokeWidth": 0})
        
    return net


# Handle auto play logic before rendering
max_step = len(st.session_state.history) - 1 if st.session_state.history else -1

def update_slider_manual():
    st.session_state.step = st.session_state.timeline_slider
    st.session_state.playing = False

col1, col2 = st.columns([2, 3])

with col1:
    st.markdown("### Simulation Dashboard")
    if max_step >= 0:
        c1, c2, c3 = st.columns([1,1,2])
        with c1:
            if st.button("▶️ Auto Play"):
                st.session_state.playing = True
                if st.session_state.step >= max_step:
                    st.session_state.step = 0
                st.rerun()
        with c2:
            if st.button("⏸️ Pause"):
                st.session_state.playing = False
                st.rerun()
        with c3:
            st.session_state.speed = st.slider("Speed (sec/step)", 0.3, 3.0, st.session_state.speed, 0.1)

        # Handle playing loop
        if st.session_state.playing:
            if st.session_state.step < max_step:
                time.sleep(st.session_state.speed)
                st.session_state.step += 1
                st.session_state.timeline_slider = st.session_state.step
                st.rerun()
            else:
                st.session_state.playing = False

        st.slider("Timeline (Steps)", 0, max_step, value=st.session_state.step, key="timeline_slider", on_change=update_slider_manual)
        
        state = st.session_state.history[st.session_state.step]
        st.info(f"**Step {st.session_state.step} Log:**\n\n{state['log']}")
        
        st.markdown("#### State Table")
        if "table" in state:
            st.dataframe(state["table"], use_container_width=True, hide_index=True)
            
        highlight_n = state["highlight_nodes"]
        highlight_e = state["highlight_edges"]
        curr_node = state["current_node"]
    else:
        st.info("Ready! Build a graph and click 'Run Visualization'.")
        highlight_n = []
        highlight_e = []
        curr_node = None

with col2:
    st.markdown("### Interactive Graph")
    if st.session_state.G.number_of_nodes() > 0:
        net = create_pyvis_graph(st.session_state.G, highlight_nodes=highlight_n, highlight_edges=highlight_e, current_node=curr_node)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp:
            net.save_graph(tmp.name)
            with open(tmp.name, 'r', encoding='utf-8') as f:
                source_code = f.read()
            components.html(source_code, height=750)
    else:
        st.warning("Graph is empty. Please add nodes/edges using the left sidebar.")
