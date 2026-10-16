"""
Social Network Analysis - Streamlit Web Application

Interactive dashboard for exploring, analyzing, managing, and visualizing
social network structures using NetworkX.
"""

# Compatibility guard for Starlette < 0.45 with Streamlit 1.57+
try:
    import starlette.middleware.gzip as _smg

    if not hasattr(_smg, "DEFAULT_EXCLUDED_CONTENT_TYPES"):
        _smg.DEFAULT_EXCLUDED_CONTENT_TYPES = ("text/event-stream",)
    if not hasattr(_smg, "IdentityResponder"):

        class _IdentityResponder:
            def __init__(self, app):
                self.app = app

            async def __call__(self, scope, receive, send):
                await self.app(scope, receive, send)

        _smg.IdentityResponder = _IdentityResponder
except Exception:
    pass

from pathlib import Path
import networkx as nx
import pandas as pd
import streamlit as st

import data_manager as dm
import graph_operations as go
import visualization as viz

# -----------------------------------------------------------------------------
# Configuration & Constants
# -----------------------------------------------------------------------------

DATA_PATH = Path(__file__).parent / "social_network.json"

st.set_page_config(
    page_title="Social Network Analysis",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Custom Styling
# -----------------------------------------------------------------------------

st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #6c757d;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .kpi-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .placeholder-box {
        background: rgba(128, 128, 128, 0.05);
        border: 2px dashed rgba(128, 128, 128, 0.3);
        border-radius: 10px;
        padding: 2.5rem 1.5rem;
        text-align: center;
        margin-top: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Session State & Feedback Management
# -----------------------------------------------------------------------------

if "feedback_message" not in st.session_state:
    st.session_state.feedback_message = None


def set_feedback(msg_type: str, msg_text: str):
    """Store flash feedback message across Streamlit reruns."""
    st.session_state.feedback_message = (msg_type, msg_text)


def render_feedback():
    """Render and clear flash feedback messages."""
    if st.session_state.feedback_message:
        msg_type, msg_text = st.session_state.feedback_message
        if msg_type == "success":
            st.success(msg_text)
        elif msg_type == "error":
            st.error(msg_text)
        elif msg_type == "info":
            st.info(msg_text)
        st.session_state.feedback_message = None


def initialize_network():
    """Load network from disk via data_manager and cache in session state."""
    st.session_state.graph = dm.load_graph(DATA_PATH)


if "graph" not in st.session_state:
    initialize_network()

graph: nx.Graph = st.session_state.graph

# -----------------------------------------------------------------------------
# Sidebar Navigation
# -----------------------------------------------------------------------------

st.sidebar.title("🕸️ Navigation")
page = st.sidebar.radio(
    "Go to",
    options=[
        "Overview",
        "Manage Network",
        "Friend Analysis",
        "Graph Analysis",
        "Network Statistics",
    ],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.subheader("Network Info")
st.sidebar.caption(f"**Data File:** `{DATA_PATH.name}`")
st.sidebar.caption(f"**Vertices:** {graph.number_of_nodes()}")
st.sidebar.caption(f"**Edges:** {graph.number_of_edges()}")

if st.sidebar.button("🔄 Reload from JSON", use_container_width=True):
    initialize_network()
    set_feedback("info", "Network state reloaded from storage.")
    st.rerun()

# -----------------------------------------------------------------------------
# Page: Overview (Dashboard)
# -----------------------------------------------------------------------------

if page == "Overview":
    st.markdown('<div class="main-header">Social Network Analysis</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Graph metrics, connectivity, and structural overview</div>',
        unsafe_allow_html=True,
    )
    render_feedback()

    # 1. KPI Cards
    total_people = graph.number_of_nodes()
    total_friendships = graph.number_of_edges()
    components = go.get_connected_components(graph) if total_people > 0 else []
    total_components = len(components)
    isolates = go.get_isolated_vertices(graph) if total_people > 0 else []
    total_isolates = len(isolates)

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric(label="Total People", value=total_people)
    with kpi2:
        st.metric(label="Total Friendships", value=total_friendships)
    with kpi3:
        st.metric(label="Connected Components", value=total_components)
    with kpi4:
        st.metric(label="Isolated Users", value=total_isolates)

    st.markdown("---")

    # 2. Most-Connected Person(s)
    st.subheader("🌟 Most Connected")
    if total_people == 0:
        st.info("The social network is currently empty. Add people in 'Manage Network' to discover top connections.")
    else:
        most_connected = go.get_most_connected_people(graph)
        max_deg = go.get_max_degree(graph)

        if max_deg == 0:
            st.warning(
                f"No friendships recorded yet. All {total_people} member(s) currently have 0 connections."
            )
        else:
            names_display = ", ".join(f"`{name}`" for name in most_connected)
            plural_conn = "friendship" if max_deg == 1 else "friendships"
            if len(most_connected) == 1:
                st.success(
                    f"**{names_display}** is the most connected member with **{max_deg} {plural_conn}**."
                )
            else:
                st.success(
                    f"**Tie for most connected!** {names_display} each have **{max_deg} {plural_conn}**."
                )

    st.markdown("---")

    # 3. Person Degree Table
    st.subheader("👥 Member Degree Distribution")
    degrees = go.get_vertex_degrees(graph) if total_people > 0 else {}

    if not degrees:
        empty_df = pd.DataFrame(columns=["Person", "Degree", "Status"])
        st.dataframe(empty_df, use_container_width=True, hide_index=True)
        st.caption("No members available in the network.")
    else:
        degree_records = [
            {
                "Person": person,
                "Degree": deg,
                "Status": "Isolated" if deg == 0 else "Connected",
            }
            for person, deg in degrees.items()
        ]
        degree_records.sort(key=lambda r: (-r["Degree"], r["Person"]))
        degree_df = pd.DataFrame(degree_records)
        st.dataframe(degree_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 4. Overview Placeholders for Upcoming Modules
    st.subheader("📌 Network Modules")
    m_col1, m_col2 = st.columns(2)

    with m_col1:
        with st.container(border=True):
            st.markdown("#### 👥 Manage Network")
            st.caption("Add or remove members and friendships safely with real-time validation.")

        with st.container(border=True):
            st.markdown("#### 🔍 Friend Analysis")
            st.caption("Examine mutual friends and examine direct neighbor connections.")

    with m_col2:
        with st.container(border=True):
            st.markdown("#### 🕸️ Graph Analysis")
            st.caption("Detect cycles, explore connected components, and find isolated nodes.")

        with st.container(border=True):
            st.markdown("#### 📈 Network Statistics")
            st.caption("Inspect consistent adjacency matrices and network-wide density metrics.")

# -----------------------------------------------------------------------------
# Page: Manage Network
# -----------------------------------------------------------------------------

elif page == "Manage Network":
    st.markdown('<div class="main-header">👥 Manage Network</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Add or remove individuals and friendship connections with safety validation</div>',
        unsafe_allow_html=True,
    )
    render_feedback()

    col_people, col_friends = st.columns(2, gap="large")

    # Column 1: People Management
    with col_people:
        st.subheader("👤 People Management")

        # 1. Add Person Form
        with st.container(border=True):
            st.markdown("##### Add New Person")
            with st.form("add_person_form", clear_on_submit=True):
                new_name = st.text_input(
                    "Person Name",
                    placeholder="Enter unique person name...",
                    key="input_new_person",
                )
                submit_add_person = st.form_submit_button("Add Person", use_container_width=True)

                if submit_add_person:
                    try:
                        go.add_person(graph, new_name)
                        dm.save_graph(graph, DATA_PATH)
                        set_feedback("success", f"Added **{new_name.strip()}** to the network.")
                        st.rerun()
                    except ValueError as err:
                        st.error(str(err))

        # 2. Remove Person Form
        with st.container(border=True):
            st.markdown("##### Remove Person")
            nodes = sorted(list(graph.nodes()))
            if not nodes:
                st.info("No people in the network to remove.")
            else:
                with st.form("remove_person_form"):
                    target_person = st.selectbox(
                        "Select Person to Remove",
                        options=nodes,
                        key="select_remove_person",
                    )
                    submit_remove_person = st.form_submit_button(
                        "Remove Person", use_container_width=True
                    )

                    if submit_remove_person:
                        try:
                            go.remove_person(graph, target_person)
                            dm.save_graph(graph, DATA_PATH)
                            set_feedback(
                                "success",
                                f"Removed **{target_person}** and all associated friendships.",
                            )
                            st.rerun()
                        except ValueError as err:
                            st.error(str(err))

    # Column 2: Friendship Management
    with col_friends:
        st.subheader("🤝 Friendship Management")

        # 3. Add Friendship Form
        with st.container(border=True):
            st.markdown("##### Add Friendship")
            nodes = sorted(list(graph.nodes()))
            if len(nodes) < 2:
                st.info("At least two people are needed to create a friendship.")
            else:
                with st.form("add_friendship_form"):
                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        p1 = st.selectbox("Person 1", options=nodes, index=0, key="select_f_p1")
                    with col_p2:
                        p2 = st.selectbox(
                            "Person 2",
                            options=nodes,
                            index=1 if len(nodes) > 1 else 0,
                            key="select_f_p2",
                        )

                    submit_add_friend = st.form_submit_button(
                        "Establish Friendship", use_container_width=True
                    )

                    if submit_add_friend:
                        try:
                            go.add_friendship(graph, p1, p2)
                            dm.save_graph(graph, DATA_PATH)
                            set_feedback(
                                "success",
                                f"Created friendship between **{p1}** and **{p2}**.",
                            )
                            st.rerun()
                        except ValueError as err:
                            st.error(str(err))

        # 4. Remove Friendship Form
        with st.container(border=True):
            st.markdown("##### Remove Friendship")
            edges = sorted([sorted([u, v]) for u, v in graph.edges()])
            if not edges:
                st.info("No friendships currently exist to remove.")
            else:
                with st.form("remove_friendship_form"):
                    edge_labels = [f"{u} ⟷ {v}" for u, v in edges]
                    selected_edge_str = st.selectbox(
                        "Select Friendship to Remove",
                        options=edge_labels,
                        key="select_remove_edge",
                    )
                    submit_remove_friend = st.form_submit_button(
                        "Remove Friendship", use_container_width=True
                    )

                    if submit_remove_friend:
                        try:
                            u_str, v_str = selected_edge_str.split(" ⟷ ")
                            go.remove_friendship(graph, u_str.strip(), v_str.strip())
                            dm.save_graph(graph, DATA_PATH)
                            set_feedback(
                                "success",
                                f"Removed friendship between **{u_str.strip()}** and **{v_str.strip()}**.",
                            )
                            st.rerun()
                        except ValueError as err:
                            st.error(str(err))

    st.markdown("---")
    st.subheader("📋 Current Network Roster")
    tab_people, tab_friends = st.tabs(["People List", "Friendships List"])
    with tab_people:
        if graph.number_of_nodes() == 0:
            st.caption("No members in the network.")
        else:
            roster_df = pd.DataFrame(
                [
                    {
                        "Person": node,
                        "Friends Count": graph.degree(node),
                        "Status": "Isolated" if graph.degree(node) == 0 else "Connected",
                    }
                    for node in sorted(graph.nodes())
                ]
            )
            st.dataframe(roster_df, use_container_width=True, hide_index=True)

    with tab_friends:
        if graph.number_of_edges() == 0:
            st.caption("No active friendships in the network.")
        else:
            friendships_df = pd.DataFrame(
                [
                    {"Person 1": u, "Person 2": v}
                    for u, v in sorted([sorted([u, v]) for u, v in graph.edges()])
                ]
            )
            st.dataframe(friendships_df, use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# Page: Friend Analysis
# -----------------------------------------------------------------------------

elif page == "Friend Analysis":
    st.markdown('<div class="main-header">🔍 Friend Analysis</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Discover mutual friends and compare social circles</div>',
        unsafe_allow_html=True,
    )
    render_feedback()

    nodes = sorted(list(graph.nodes()))
    total_people = len(nodes)

    if total_people == 0:
        st.info("The social network is currently empty. Please add members in **Manage Network** first.")
    elif total_people < 2:
        st.warning("At least two people are required to analyze friendships and find mutual connections.")
    else:
        with st.container(border=True):
            st.subheader("Select Members to Compare")
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                person1 = st.selectbox("Select Person 1", options=nodes, index=0, key="fa_person1")
            with col_sel2:
                default_idx2 = 1 if len(nodes) > 1 else 0
                person2 = st.selectbox("Select Person 2", options=nodes, index=default_idx2, key="fa_person2")

        if person1 == person2:
            st.warning("Please select two different people to compare mutual friends.")
        else:
            try:
                mutual_friends = sorted(list(go.get_mutual_friends(graph, person1, person2)))
                p1_friends = sorted(list(graph.neighbors(person1)))
                p2_friends = sorted(list(graph.neighbors(person2)))
                are_direct_friends = graph.has_edge(person1, person2)

                st.markdown("---")

                # Connection Summary Metrics
                st.subheader("🤝 Connection Overview")
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric(label=f"{person1}'s Friends", value=len(p1_friends))
                with m2:
                    st.metric(label=f"{person2}'s Friends", value=len(p2_friends))
                with m3:
                    st.metric(label="Mutual Friends", value=len(mutual_friends))
                with m4:
                    st.metric(
                        label="Direct Connection",
                        value="Friends" if are_direct_friends else "Not Connected",
                    )

                st.markdown("---")

                # Mutual Friends Section
                st.subheader("👥 Mutual Friends")
                if not mutual_friends:
                    st.info(f"No mutual friends found between **{person1}** and **{person2}**.")
                else:
                    st.success(
                        f"**{person1}** and **{person2}** share **{len(mutual_friends)}** mutual friend(s): "
                        + ", ".join(f"`{f}`" for f in mutual_friends)
                    )
                    mutual_df = pd.DataFrame(
                        [
                            {
                                "Mutual Friend": f,
                                f"Connected to {person1}": "Yes",
                                f"Connected to {person2}": "Yes",
                                "Total Friends": graph.degree(f),
                            }
                            for f in mutual_friends
                        ]
                    )
                    st.dataframe(mutual_df, use_container_width=True, hide_index=True)

                st.markdown("---")

                # Individual Friends Comparison
                st.subheader("📋 Friends Comparison")
                col_f1, col_f2 = st.columns(2)

                with col_f1:
                    st.markdown(f"##### {person1}'s Friends ({len(p1_friends)})")
                    if not p1_friends:
                        st.caption(f"{person1} has no friends yet.")
                    else:
                        df_p1 = pd.DataFrame(
                            [
                                {
                                    "Friend": f,
                                    f"Also friends with {person2}": (
                                        "Yes" if f in mutual_friends else "No"
                                    ),
                                }
                                for f in p1_friends
                            ]
                        )
                        st.dataframe(df_p1, use_container_width=True, hide_index=True)

                with col_f2:
                    st.markdown(f"##### {person2}'s Friends ({len(p2_friends)})")
                    if not p2_friends:
                        st.caption(f"{person2} has no friends yet.")
                    else:
                        df_p2 = pd.DataFrame(
                            [
                                {
                                    "Friend": f,
                                    f"Also friends with {person1}": (
                                        "Yes" if f in mutual_friends else "No"
                                    ),
                                }
                                for f in p2_friends
                            ]
                        )
                        st.dataframe(df_p2, use_container_width=True, hide_index=True)

            except ValueError as err:
                st.error(f"Analysis error: {err}")

# -----------------------------------------------------------------------------
# Page: Graph Analysis
# -----------------------------------------------------------------------------

elif page == "Graph Analysis":
    st.markdown('<div class="main-header">🕸️ Graph Analysis</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Shortest path navigation, components, cycle detection, and adjacency matrix</div>',
        unsafe_allow_html=True,
    )
    render_feedback()

    nodes = sorted(list(graph.nodes()))
    total_people = len(nodes)
    total_edges = graph.number_of_edges()

    # High-level Metrics Row
    components = go.get_connected_components(graph) if total_people > 0 else []
    isolates = go.get_isolated_vertices(graph) if total_people > 0 else []
    cycle_exists = go.has_cycle(graph) if total_people > 0 else False

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    with metric_col1:
        st.metric(label="Total Vertices", value=total_people)
    with metric_col2:
        st.metric(label="Connected Components", value=len(components))
    with metric_col3:
        st.metric(label="Isolated Individuals", value=len(isolates))
    with metric_col4:
        st.metric(label="Cycle Detected", value="Yes" if cycle_exists else "No")

    st.markdown("---")

    # Section 1: BFS Shortest Path Finder
    st.subheader("🧭 Shortest Path Finder (BFS)")
    if total_people == 0:
        st.info("The social network is currently empty. Add people in **Manage Network** to find paths.")
    elif total_people == 1:
        st.warning("At least two people are required to analyze paths between different members.")
    else:
        with st.container(border=True):
            col_s, col_d = st.columns(2)
            with col_s:
                source = st.selectbox("Source Person", options=nodes, index=0, key="ga_source")
            with col_d:
                default_d_idx = 1 if len(nodes) > 1 else 0
                destination = st.selectbox(
                    "Destination Person", options=nodes, index=default_d_idx, key="ga_destination"
                )

            if source == destination:
                st.info(
                    f"Source and destination are identical (**{source}**). Path length is **0 edges** (0 hops)."
                )
                st.markdown(f"**Path:** `{source}`")
            else:
                try:
                    path = go.find_shortest_path_bfs(graph, source, destination)

                    if path is not None:
                        num_edges = len(path) - 1
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.metric(label="Status", value="Connected")
                        with c2:
                            st.metric(label="Shortest Distance (Edges)", value=num_edges)
                        with c3:
                            st.metric(label="Members in Path", value=len(path))

                        path_display = " ➔ ".join(f"`{p}`" for p in path)
                        st.success(f"**Shortest Path:** {path_display}")

                        steps_data = [
                            {
                                "Hop #": i + 1,
                                "From": path[i],
                                "To": path[i + 1],
                                "Friendship": f"{path[i]} ⟷ {path[i + 1]}",
                            }
                            for i in range(len(path) - 1)
                        ]
                        st.dataframe(pd.DataFrame(steps_data), use_container_width=True, hide_index=True)
                    else:
                        c1, c2 = st.columns(2)
                        with c1:
                            st.metric(label="Status", value="Disconnected")
                        with c2:
                            st.metric(label="Shortest Distance", value="No path (None)")

                        st.error(
                            f"❌ **No path exists** between **{source}** and **{destination}**. "
                            "They belong to separate, disconnected components of the social network."
                        )
                except ValueError as err:
                    st.error(f"Path calculation error: {err}")

    st.markdown("---")

    # Section 2: Connected Components & Isolated Users
    st.subheader("🧩 Components & Isolated Users")
    comp_col, iso_col = st.columns(2, gap="large")

    with comp_col:
        with st.container(border=True):
            st.markdown("#### Connected Components")
            if not components:
                st.caption("No connected components in the network.")
            else:
                comp_records = []
                for idx, comp in enumerate(components, start=1):
                    members_sorted = sorted(list(comp))
                    comp_records.append(
                        {
                            "Component #": f"Component {idx}",
                            "Size": len(members_sorted),
                            "Members": ", ".join(members_sorted),
                        }
                    )
                st.dataframe(pd.DataFrame(comp_records), use_container_width=True, hide_index=True)

    with iso_col:
        with st.container(border=True):
            st.markdown("#### Isolated Individuals (Degree 0)")
            if not isolates:
                st.success("None! All members have at least one friendship in the network.")
            else:
                st.warning(f"Found **{len(isolates)}** isolated member(s) with 0 friendships.")
                iso_records = [
                    {"Isolated Person": person, "Status": "0 Friendships (Disconnected)"}
                    for person in isolates
                ]
                st.dataframe(pd.DataFrame(iso_records), use_container_width=True, hide_index=True)

    st.markdown("---")

    # Section 3: Cycle Detection
    st.subheader("🔄 Cycle Detection")
    with st.container(border=True):
        if total_people == 0:
            st.info("The network is currently empty. Add connections to analyze cycles.")
        elif not cycle_exists:
            st.success("✅ **No cycles detected.** The network graph is an acyclic forest (or tree).")
        else:
            cycle_edges = go.find_cycle(graph)
            if cycle_edges:
                cycle_nodes = [u for u, v in cycle_edges]
                cycle_display = " ➔ ".join(f"`{u}`" for u in cycle_nodes) + f" ➔ `{cycle_nodes[0]}`"
                st.warning(
                    f"⚠️ **Cycle Detected!** The graph contains closed connection loops.\n\n"
                    f"**Example Cycle:** {cycle_display}"
                )
                cycle_df = pd.DataFrame(
                    [
                        {"Step": i + 1, "From": u, "To": v, "Edge": f"{u} ⟷ {v}"}
                        for i, (u, v) in enumerate(cycle_edges)
                    ]
                )
                st.dataframe(cycle_df, use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ **Cycle Detected!** The graph contains closed connection loops.")

    st.markdown("---")

    # Section 4: Adjacency Matrix
    st.subheader("📊 Network Adjacency Matrix")
    with st.container(border=True):
        st.caption(
            "Consistent binary adjacency matrix where 1 represents a friendship and 0 represents no connection. "
            "Rows and columns are arranged in consistent alphabetical order."
        )
        if total_people == 0:
            empty_adj = pd.DataFrame(dtype=int)
            st.dataframe(empty_adj, use_container_width=True)
            st.caption("Network is empty (0 × 0 adjacency matrix).")
        else:
            adj_df = go.get_adjacency_matrix(graph)
            st.dataframe(adj_df, use_container_width=True)
            st.caption(f"Matrix dimensions: **{adj_df.shape[0]} × {adj_df.shape[1]}**")

# -----------------------------------------------------------------------------
# Page: Network Statistics
# -----------------------------------------------------------------------------

elif page == "Network Statistics":
    st.markdown('<div class="main-header">📈 Network Statistics & Visualization</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Interactive network topology map and high-level graph metrics</div>',
        unsafe_allow_html=True,
    )
    render_feedback()

    nodes = sorted(list(graph.nodes()))
    total_people = len(nodes)
    total_edges = graph.number_of_edges()

    # 1. High-Level Metrics
    density = nx.density(graph) if total_people > 1 else 0.0
    avg_degree = (2.0 * total_edges / total_people) if total_people > 0 else 0.0

    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    with stat_col1:
        st.metric(label="Total People", value=total_people)
    with stat_col2:
        st.metric(label="Total Friendships", value=total_edges)
    with stat_col3:
        st.metric(label="Network Density", value=f"{density * 100:.1f}%")
    with stat_col4:
        st.metric(label="Average Degree", value=f"{avg_degree:.2f}")

    st.markdown("---")

    # 2. Network Graph Visualization
    st.subheader("🗺️ Social Network Graph")
    st.caption(
        "Visual map of members (nodes) and friendships (edges). "
        "Amber highlights the most connected member(s), Red highlights isolated individuals, and Blue denotes connected members."
    )

    with st.container(border=True):
        fig = viz.plot_network(
            graph,
            figsize=(11, 7),
            title="Social Network Analysis - Topology Map",
        )
        st.pyplot(fig, use_container_width=True)
        import matplotlib.pyplot as _plt
        _plt.close(fig)

    st.markdown("---")

    # 3. Network Structure Summary Table
    st.subheader("📊 Network Topology Details")
    detail_c1, detail_c2 = st.columns(2)

    with detail_c1:
        with st.container(border=True):
            st.markdown("##### Node Category Breakdown")
            if total_people == 0:
                st.caption("No members in the network.")
            else:
                degrees = dict(graph.degree())
                max_d = max(degrees.values()) if degrees else 0
                isolates_count = len(go.get_isolated_vertices(graph))
                top_count = len(go.get_most_connected_people(graph)) if max_d > 0 else 0
                regular_count = total_people - isolates_count - top_count

                cat_df = pd.DataFrame(
                    [
                        {"Category": "🌟 Most Connected", "Count": top_count, "Color": "Amber / Gold"},
                        {"Category": "🔵 Connected Members", "Count": regular_count, "Color": "Blue"},
                        {"Category": "🔴 Isolated Members", "Count": isolates_count, "Color": "Red / Coral"},
                    ]
                )
                st.dataframe(cat_df, use_container_width=True, hide_index=True)

    with detail_c2:
        with st.container(border=True):
            st.markdown("##### Adjacency Matrix Preview")
            if total_people == 0:
                st.caption("Network is empty (0 × 0).")
            else:
                adj = go.get_adjacency_matrix(graph)
                st.dataframe(adj, use_container_width=True)
                st.caption(f"Binary Adjacency Matrix ({adj.shape[0]} × {adj.shape[1]})")
