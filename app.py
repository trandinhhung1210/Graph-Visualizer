import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
from pyvis.network import Network
import random
import tempfile

st.set_page_config(layout="wide", page_title="Graph Algorithm Visualizer", page_icon="🕸️")

# --- Session State Initialization ---
if 'G' not in st.session_state:
    st.session_state.G = nx.Graph()
if 'heuristics' not in st.session_state:
    st.session_state.heuristics = {}

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

# --- Algorithms ---
def bfs(G, start, target=None):
    if start not in G: return [], []
    visited = []
    queue = [start]
    visited_set = {start}
    path_edges = []
    parent = {}
    
    while queue:
        node = queue.pop(0)
        visited.append(node)
        if node in parent:
            path_edges.append((parent[node], node))
            
        if node == target:
            break
            
        for neighbor in G.neighbors(node):
            if neighbor not in visited_set:
                visited_set.add(neighbor)
                parent[neighbor] = node
                queue.append(neighbor)
                
    return visited, path_edges

def dfs(G, start, target=None):
    if start not in G: return [], []
    visited = []
    stack = [start]
    visited_set = set()
    path_edges = []
    parent = {}
    
    while stack:
        node = stack.pop()
        if node not in visited_set:
            visited_set.add(node)
            visited.append(node)
            
            if node in parent:
                path_edges.append((parent[node], node))
                
            if node == target:
                break
                
            for neighbor in list(G.neighbors(node))[::-1]:
                if neighbor not in visited_set:
                    stack.append(neighbor)
                    parent[neighbor] = node
                    
    return visited, path_edges

def dijkstra(G, start, target):
    if start not in G or target not in G: return [], [], 0
    try:
        path = nx.shortest_path(G, source=start, target=target, weight='weight')
        cost = nx.shortest_path_length(G, source=start, target=target, weight='weight')
        path_edges = list(zip(path, path[1:]))
        return path, path_edges, cost
    except nx.NetworkXNoPath:
        return [], [], float('inf')
    except nx.NodeNotFound:
        return [], [], float('inf')

def astar(G, start, target, heuristics):
    if start not in G or target not in G: return [], [], 0
    def heuristic(u, v):
        return heuristics.get(u, 0)
        
    try:
        path = nx.astar_path(G, source=start, target=target, heuristic=heuristic, weight='weight')
        cost = nx.astar_path_length(G, source=start, target=target, heuristic=heuristic, weight='weight')
        path_edges = list(zip(path, path[1:]))
        return path, path_edges, cost
    except nx.NetworkXNoPath:
        return [], [], float('inf')
    except nx.NodeNotFound:
        return [], [], float('inf')

def mst_kruskal(G):
    if G.number_of_nodes() == 0: return [], [], 0
    T = nx.minimum_spanning_tree(G, algorithm='kruskal', weight='weight')
    return list(T.nodes()), list(T.edges(data=True)), sum(d.get('weight', 1) for u, v, d in T.edges(data=True))

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
        st.success(f"Added edge: {u_node} - {v_node} (Weight: {weight})")
        
    st.subheader("Set Heuristic (for A*)")
    nodes = list(st.session_state.G.nodes())
    h_node = st.selectbox("Select Node", options=[""] + nodes if nodes else [""])
    h_val = st.number_input("Heuristic Value", value=0.0)
    if st.button("Set Heuristic"):
        if h_node:
            set_heuristic(h_node, h_val)
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
        st.success("Graph cleared!")

    st.header("2. Algorithm Selection")
    algo = st.selectbox("Select Algorithm", ["BFS", "DFS", "Dijkstra", "A*", "MST (Kruskal)"])
    
    start_node = st.selectbox("Start Node", options=nodes if nodes else [""])
    target_node = st.selectbox("Target Node", options=nodes if nodes else [""])
    
    run_btn = st.button("Run Visualization", type="primary")

# --- Visualization Logic ---
def create_pyvis_graph(G, highlight_nodes=None, highlight_edges=None):
    if highlight_nodes is None: highlight_nodes = []
    if highlight_edges is None: highlight_edges = []
        
    net = Network(height="600px", width="100%", bgcolor="#0E1117", font_color="white")
    
    for node in G.nodes():
        if node in highlight_nodes:
            if node == highlight_nodes[0] and algo in ["BFS", "DFS", "Dijkstra", "A*"]:
                color = "#2ecc71" # Start node (Green)
            elif node == highlight_nodes[-1] and algo in ["BFS", "DFS", "Dijkstra", "A*"]:
                color = "#e67e22" # Target node (Orange)
            else:
                color = "#e74c3c" # Path node (Red)
        else:
            color = "#3498db" # Default node (Blue)
            
        label = f"{node} (h={st.session_state.heuristics.get(node, 0)})" if algo == "A*" else str(node)
        net.add_node(node, label=label, color=color, title=f"Node: {node}")
        
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

with col1:
    st.markdown("### Output Logs")
    if not run_btn:
        st.info("Ready. Construct a graph and run an algorithm.")

with col2:
    st.markdown("### Interactive Graph")

if run_btn and st.session_state.G.number_of_nodes() > 0:
    G = st.session_state.G
    logs = ""
    highlight_n = []
    highlight_e = []
    
    if algo == "BFS":
        visited, path_edges = bfs(G, start_node, target_node)
        highlight_n = visited
        highlight_e = path_edges
        logs = f"**BFS Traversal Order:**\n\n{' -> '.join(map(str, visited))}"
    elif algo == "DFS":
        visited, path_edges = dfs(G, start_node, target_node)
        highlight_n = visited
        highlight_e = path_edges
        logs = f"**DFS Traversal Order:**\n\n{' -> '.join(map(str, visited))}"
    elif algo == "Dijkstra":
        path, path_edges, cost = dijkstra(G, start_node, target_node)
        highlight_n = path
        highlight_e = path_edges
        if path:
            logs = f"**Shortest Path:**\n\n{' -> '.join(map(str, path))}\n\n**Total Cost:** {cost}"
        else:
            logs = "No path found."
    elif algo == "A*":
        path, path_edges, cost = astar(G, start_node, target_node, st.session_state.heuristics)
        highlight_n = path
        highlight_e = path_edges
        if path:
            logs = f"**A* Shortest Path:**\n\n{' -> '.join(map(str, path))}\n\n**Total Cost:** {cost}"
        else:
            logs = "No path found."
    elif algo == "MST (Kruskal)":
        mst_nodes, mst_edges, total_cost = mst_kruskal(G)
        highlight_n = mst_nodes
        highlight_e = [(u, v) for u, v, d in mst_edges]
        logs = f"**MST Total Weight:** {total_cost}\n\n**Edges included:** {len(highlight_e)}"

    with col1:
        st.success(logs)
    
    with col2:
        net = create_pyvis_graph(st.session_state.G, highlight_nodes=highlight_n, highlight_edges=highlight_e)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp:
            net.save_graph(tmp.name)
            with open(tmp.name, 'r', encoding='utf-8') as f:
                source_code = f.read()
            components.html(source_code, height=650)
            
elif st.session_state.G.number_of_nodes() > 0:
    with col2:
        net = create_pyvis_graph(st.session_state.G)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp:
            net.save_graph(tmp.name)
            with open(tmp.name, 'r', encoding='utf-8') as f:
                source_code = f.read()
            components.html(source_code, height=650)
else:
    with col2:
        st.info("Graph is empty. Please add nodes/edges using the sidebar or generate a random graph.")
