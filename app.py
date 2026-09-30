import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
from pyvis.network import Network
import random
import tempfile
import heapq

st.set_page_config(layout="wide", page_title="Graph Algorithm Visualizer", page_icon="🕸️")

# --- Session State Initialization ---
if 'G' not in st.session_state:
    st.session_state.G = nx.Graph()
if 'heuristics' not in st.session_state:
    st.session_state.heuristics = {}
if 'history' not in st.session_state:
    st.session_state.history = []

def add_edge(u, v, weight):
    u = u.strip()
    v = v.strip()
    if u and v:
        st.session_state.G.add_edge(u, v, weight=weight)
        if u not in st.session_state.heuristics:
            st.session_state.heuristics[u] = 0
        if v not in st.session_state.heuristics:
            st.session_state.heuristics[v] = 0

def set_heuristic(node, h_val):
    node = node.strip()
    if node in st.session_state.G.nodes:
        st.session_state.heuristics[node] = h_val

def generate_random_graph(num_nodes, probability):
    G = nx.erdos_renyi_graph(num_nodes, probability)
    H = nx.Graph()
    for u, v in G.edges():
        H.add_edge(str(u), str(v), weight=random.randint(1, 20))
    st.session_state.G = H
    st.session_state.heuristics = {str(n): random.randint(1, 10) for n in H.nodes()}
    st.session_state.history = [] # reset history

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
            "log": f"Visiting node {node}"
        })
            
        if node == target:
            history.append({
                "highlight_nodes": list(visited),
                "highlight_edges": list(path_edges),
                "current_node": node,
                "log": f"Target {target} found!"
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
                "log": f"Visiting node {node}"
            })
                
            if node == target:
                history.append({
                    "highlight_nodes": list(visited),
                    "highlight_edges": list(path_edges),
                    "current_node": node,
                    "log": f"Target {target} found!"
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
            "log": f"Visiting {node} (Cost from start: {dist})"
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
                "log": f"Shortest path found! Total Cost: {dist}\n\nPath: {' -> '.join(path)}"
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
    pq = [(0 + heuristics.get(start, 0), 0, start)] # (f, g, node)
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
            "log": f"Visiting {node}\n\nCost so far (g): {g}\nHeuristic to target (h): {heuristics.get(node,0)}\nTotal estimated (f=g+h): {f}"
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
                "log": f"A* Path found! Total Cost: {g}\n\nPath: {' -> '.join(path)}"
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
    
    history.append({
        "highlight_nodes": [],
        "highlight_edges": [],
        "current_node": None,
        "log": "Starting Kruskal's MST. Sorted edges by weight."
    })
    
    for u, v, d in edges:
        weight = d.get('weight', 1)
        history.append({
            "highlight_nodes": list(mst_nodes) + [u, v],
            "highlight_edges": list(mst_edges) + [(u, v)],
            "current_node": None,
            "log": f"Inspecting edge {u}-{v} (Weight: {weight})"
        })
        
        if union(u, v):
            mst_edges.append((u, v))
            mst_nodes.add(u)
            mst_nodes.add(v)
            total_cost += weight
            history.append({
                "highlight_nodes": list(mst_nodes),
                "highlight_edges": list(mst_edges),
                "current_node": None,
                "log": f"Added edge {u}-{v} to MST. Total cost so far: {total_cost}"
            })
        else:
            history.append({
                "highlight_nodes": list(mst_nodes),
                "highlight_edges": list(mst_edges),
                "current_node": None,
                "log": f"Edge {u}-{v} creates a cycle. Discarding."
            })
            
    history.append({
        "highlight_nodes": list(mst_nodes),
        "highlight_edges": list(mst_edges),
        "current_node": None,
        "log": f"MST Complete! Total Cost: {total_cost}"
    })
            
    return history

# --- UI ---
st.title("Graph Traversal & Pathfinding Visualizer 🕸️")

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
        st.success(f"Added edge: {u_node} - {v_node} (Weight: {weight})")
        
    st.subheader("Set Heuristic (for A*)")
    nodes = list(st.session_state.G.nodes())
    h_node = st.selectbox("Select Node", options=[""] + nodes if nodes else [""])
    h_val = st.number_input("Heuristic Value", value=0.0)
    if st.button("Set Heuristic"):
        if h_node:
            set_heuristic(h_node, h_val)
            st.session_state.history = []
            st.success(f"Set h({h_node}) = {h_val}")
            
    st.subheader("Quick Start")
    rand_nodes = st.slider("Number of Nodes", 5, 20, 10)
    rand_prob = st.slider("Edge Probability", 0.1, 1.0, 0.3)
    if st.button("Generate Random Graph"):
        generate_random_graph(rand_nodes, rand_prob)
        st.success("Generated random graph!")
        
    if st.button("Clear Graph"):
        st.session_state.G.clear()
        st.session_state.heuristics.clear()
        st.session_state.history = []
        st.success("Graph cleared!")

    st.header("2. Algorithm Selection")
    algo = st.selectbox("Select Algorithm", ["BFS", "DFS", "Dijkstra", "A*", "MST (Kruskal)"])
    
    start_node = st.selectbox("Start Node", options=nodes if nodes else [""])
    target_node = st.selectbox("Target Node", options=nodes if nodes else [""])
    
    run_btn = st.button("Run Visualization", type="primary")

# --- Visualization Logic ---
def create_pyvis_graph(G, highlight_nodes=None, highlight_edges=None, current_node=None):
    if highlight_nodes is None: highlight_nodes = []
    if highlight_edges is None: highlight_edges = []
        
    net = Network(height="600px", width="100%", bgcolor="#0E1117", font_color="white")
    
    for node in G.nodes():
        if node == current_node:
            color = "#f1c40f" # Yellow for current step
            size = 25
        elif node in highlight_nodes:
            if node == start_node and algo != "MST (Kruskal)":
                color = "#2ecc71" # Green
            elif node == target_node and algo != "MST (Kruskal)":
                color = "#e67e22" # Orange
            else:
                color = "#e74c3c" # Red
            size = 20
        else:
            color = "#3498db" # Blue
            size = 15
            
        label = f"{node} (h={st.session_state.heuristics.get(node, 0)})" if algo == "A*" else str(node)
        net.add_node(node, label=label, color=color, title=f"Node: {node}", size=size)
        
    for u, v, d in G.edges(data=True):
        weight = d.get('weight', 1)
        is_highlighted = (u, v) in highlight_edges or (v, u) in highlight_edges
        
        color = "#e74c3c" if is_highlighted else "#555555"
        width = 4 if is_highlighted else 1
        
        net.add_edge(u, v, title=f"Weight: {weight}", label=str(weight), color=color, width=width)
        
    net.set_options("""
    var options = {
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -3000,
          "springLength": 200,
          "springConstant": 0.04
        }
      }
    }
    """)
    return net

col1, col2 = st.columns([1, 3])

if run_btn and st.session_state.G.number_of_nodes() > 0:
    G = st.session_state.G
    
    if algo == "BFS":
        st.session_state.history = bfs(G, start_node, target_node)
    elif algo == "DFS":
        st.session_state.history = dfs(G, start_node, target_node)
    elif algo == "Dijkstra":
        st.session_state.history = dijkstra(G, start_node, target_node)
    elif algo == "A*":
        st.session_state.history = astar(G, start_node, target_node, st.session_state.heuristics)
    elif algo == "MST (Kruskal)":
        st.session_state.history = mst_kruskal(G)

with col1:
    st.markdown("### Traversal Steps")
    
    if st.session_state.history:
        max_step = len(st.session_state.history) - 1
        if max_step >= 0:
            step = st.slider("Timeline (Kéo thanh trượt)", 0, max_step, 0)
            
            state = st.session_state.history[step]
            st.info(state["log"])
            
            highlight_n = state["highlight_nodes"]
            highlight_e = state["highlight_edges"]
            curr_node = state["current_node"]
        else:
            st.warning("No path or steps generated.")
            highlight_n = []
            highlight_e = []
            curr_node = None
    else:
        st.info("Ready. Construct a graph and run an algorithm.")
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
            components.html(source_code, height=650)
    else:
        st.info("Graph is empty. Please add nodes/edges using the sidebar or generate a random graph.")
