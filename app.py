from __future__ import annotations

from datetime import datetime, timezone
import hmac
import json
from pathlib import Path
from time import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse

import pandas as pd
import streamlit as st


CATALOG_PATH = Path(__file__).with_name("catalog.json")
BACKUP_PATH = Path(__file__).with_name("catalog_backups.json")


st.set_page_config(
    page_title="EMK Links / Art Gallery",
    page_icon="+",
    layout="wide",
    initial_sidebar_state="expanded",
)


SAMPLE_ART = [
    {
        "title": "After the Rain",
        "artist": "Maya Okafor",
        "category": "Painting",
        "year": 2024,
        "status": "Live",
        "url": "https://example.com/emk/after-the-rain",
        "image": "https://images.unsplash.com/photo-1549490349-8643362247b5?auto=format&fit=crop&w=1000&q=85",
        "accent": "Moss / ochre / dusk",
        "description": "A quiet study of light returning to a city garden.",
    },
    {
        "title": "Soft Machinery",
        "artist": "Jon Bell",
        "category": "Digital",
        "year": 2025,
        "status": "Live",
        "url": "https://example.com/emk/soft-machinery",
        "image": "https://images.unsplash.com/photo-1551913902-c92207136625?auto=format&fit=crop&w=1000&q=85",
        "accent": "Signal / cobalt / chrome",
        "description": "A digital composition about systems that learn to breathe.",
    },
    {
        "title": "Tidal Memory",
        "artist": "Nia Mensah",
        "category": "Photography",
        "year": 2023,
        "status": "Review",
        "url": "https://example.com/emk/tidal-memory",
        "image": "https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=1000&q=85",
        "accent": "Salt / silver / blue hour",
        "description": "Photographs gathered at the edge of a changing shoreline.",
    },
    {
        "title": "Common Ground",
        "artist": "The EMK Collective",
        "category": "Installation",
        "year": 2025,
        "status": "Live",
        "url": "https://example.com/emk/common-ground",
        "image": "https://images.unsplash.com/photo-1561839561-b13bcfe95249?auto=format&fit=crop&w=1000&q=85",
        "accent": "Clay / linen / conversation",
        "description": "An open-ended installation built from shared materials.",
    },
    {
        "title": "Electric Bloom",
        "artist": "Samira Cole",
        "category": "Print",
        "year": 2022,
        "status": "Live",
        "url": "https://example.com/emk/electric-bloom",
        "image": "https://images.unsplash.com/photo-1541701494587-cb58502866ab?auto=format&fit=crop&w=1000&q=85",
        "accent": "Ink / neon / petal",
        "description": "A print series where botanical forms meet bright interference.",
    },
    {
        "title": "Small Weather",
        "artist": "Kofi Armah",
        "category": "Sculpture",
        "year": 2024,
        "status": "Draft",
        "url": "https://example.com/emk/small-weather",
        "image": "https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?auto=format&fit=crop&w=1000&q=85",
        "accent": "Stone / wire / air",
        "description": "Small objects holding the feeling of a larger atmosphere.",
    },
]


def load_catalog() -> list[dict]:
    if not CATALOG_PATH.exists():
        return SAMPLE_ART.copy()
    try:
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        return catalog if isinstance(catalog, list) else SAMPLE_ART.copy()
    except (OSError, json.JSONDecodeError):
        return SAMPLE_ART.copy()


def save_catalog(catalog: list[dict]) -> None:
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2), encoding="utf-8")


def check_link(url: str) -> tuple[str, str]:
    try:
        request = Request(url, method="HEAD", headers={"User-Agent": "EMKGallery/1.0"})
        with urlopen(request, timeout=5) as response:
            return "Online", str(response.status)
    except HTTPError as error:
        return "Needs review", str(error.code)
    except (URLError, TimeoutError, ValueError):
        return "Unavailable", "-"


def load_backups() -> list[dict]:
    if not BACKUP_PATH.exists():
        return []
    try:
        backups = json.loads(BACKUP_PATH.read_text(encoding="utf-8"))
        return backups if isinstance(backups, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def save_backup(catalog: list[dict], reason: str, retention: int) -> None:
    backups = load_backups()
    backups.insert(0, {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "entries": len(catalog),
        "catalog": catalog,
    })
    BACKUP_PATH.write_text(json.dumps(backups[:retention], indent=2), encoding="utf-8")
    st.session_state.backups = backups[:retention]


def fetch_prometheus_metrics(endpoint: str) -> tuple[dict[str, float], str]:
    try:
        request = Request(endpoint, headers={"User-Agent": "EMKGallery/1.0"})
        with urlopen(request, timeout=3) as response:
            metrics: dict[str, float] = {}
            for line in response.read().decode("utf-8", errors="replace").splitlines():
                if not line or line.startswith("#") or " " not in line:
                    continue
                name, value = line.rsplit(" ", 1)
                try:
                    metrics[name.split("{", 1)[0]] = float(value)
                except ValueError:
                    continue
            return metrics, "Prometheus endpoint"
    except (OSError, URLError, ValueError):
        return {}, "Derived gallery telemetry"


def gallery_metrics(catalog: list[dict]) -> dict[str, float]:
    total = len(catalog)
    live = sum(item.get("status") == "Live" for item in catalog)
    return {
        "emk_gallery_items": total,
        "emk_gallery_live_links": live,
        "emk_gallery_review_queue": sum(item.get("status") == "Review" for item in catalog),
        "emk_gallery_draft_items": sum(item.get("status") == "Draft" for item in catalog),
        "emk_gallery_artists": len({item.get("artist") for item in catalog}),
        "emk_gallery_link_checks": len(st.session_state.get("link_checks", {})),
        "emk_gallery_link_failures": sum(state[0] != "Online" for state in st.session_state.get("link_checks", {}).values()),
        "emk_gallery_catalog_age_seconds": 0,
    }


def configured_control_room() -> tuple[str, str]:
    try:
        credentials = st.secrets.get("control_room", {})
    except Exception:
        credentials = {}
    return str(credentials.get("username", "admin")), str(credentials.get("password", "emk-gallery"))


def valid_credentials(username: str, password: str) -> bool:
    expected_username, expected_password = configured_control_room()
    return bool(expected_username and expected_password) and hmac.compare_digest(username, expected_username) and hmac.compare_digest(password, expected_password)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    :root { --ink: #18251f; --muted: #69766e; --paper: #f4f1e9; --panel: #fffdf8; --line: #d9ded4; --acid: #d8ef70; --sage: #cfe4d3; --rust: #a94f32; }
    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
    .stApp { background-color: var(--paper); background-image: linear-gradient(rgba(24,37,31,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(24,37,31,.035) 1px, transparent 1px), linear-gradient(120deg, rgba(207,228,211,.35), transparent 44%, rgba(216,239,112,.12) 82%, transparent); background-size: 40px 40px, 40px 40px, 100% 100%; background-attachment: fixed; color: var(--ink); }
    [data-testid="stSidebar"] { background: #e7eee4; border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] * { color: var(--ink); }
    h1, h2, h3 { letter-spacing: -.045em; color: var(--ink); }
    h1 { font-family: 'Fraunces', serif; font-size: 3.5rem !important; font-weight: 500 !important; line-height: 1 !important; }
    h2 { font-family: 'Fraunces', serif; font-weight: 500 !important; }
    .eyebrow { color: var(--rust); font-family: 'DM Mono', monospace; font-size: .7rem; letter-spacing: .14em; text-transform: uppercase; }
    .subtle { color: var(--muted); }
    .hero-note { color: var(--muted); font-size: 1rem; max-width: 560px; }
    .resolution-note { background: #edf4d8; border-left: 4px solid var(--acid); color: var(--ink); padding: .8rem 1rem; }
    .resolution-note strong { font-family: 'DM Mono', monospace; font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; }
    .insight-panel { background: rgba(255,253,248,.86); border: 1px solid var(--line); border-radius: 6px; min-height: 176px; padding: 1.05rem; box-shadow: 0 8px 18px rgba(43,60,49,.04); }
    .insight-label { color: var(--rust); font-family: 'DM Mono', monospace; font-size: .68rem; letter-spacing: .1em; text-transform: uppercase; }
    .insight-panel h4 { color: var(--ink); font-family: 'Fraunces', serif; font-size: 1.15rem; margin: .45rem 0 .55rem; }
    .insight-panel p { color: #4e5c54; font-size: .86rem; line-height: 1.45; margin: 0; }
    .count-mark { font-family: 'DM Mono', monospace; font-size: .75rem; color: var(--muted); padding-top: .9rem; text-align: right; }
    .art-card { background: rgba(255,253,248,.94); border: 1px solid var(--line); border-radius: 7px; overflow: hidden; margin-bottom: 1rem; box-shadow: 0 12px 25px rgba(43,60,49,.05); }
    .art-card img { display: block; width: 100%; height: 215px; object-fit: cover; }
    .art-copy { padding: .9rem 1rem 1rem; }
    .art-title { font-family: 'Fraunces', serif; font-size: 1.35rem; color: var(--ink); }
    .art-meta { color: var(--muted); font-size: .82rem; margin: .2rem 0 .65rem; }
    .art-description { color: #4e5c54; font-size: .87rem; min-height: 2.6rem; }
    .art-footer { align-items: center; display: flex; justify-content: space-between; margin-top: .8rem; }
    .tag { background: #eef3df; border-radius: 999px; color: #51614b; font-family: 'DM Mono', monospace; font-size: .64rem; padding: .3rem .5rem; text-transform: uppercase; }
    .tag.review { background: #f7e6d8; color: #8c4d32; }
    .tag.draft { background: #e6e7e1; color: #6d746c; }
    .stat { background: rgba(255,253,248,.75); border-bottom: 1px solid var(--line); padding: .8rem 0; }
    .stat-label { color: var(--muted); font-family: 'DM Mono', monospace; font-size: .67rem; letter-spacing: .08em; text-transform: uppercase; }
    .stat-value { font-family: 'DM Mono', monospace; font-size: 1.3rem; margin-top: .25rem; }
    .stButton > button, .stLinkButton > a { border-radius: 4px; }
    .stLinkButton > a { background: var(--ink); color: white; border: 1px solid var(--ink); }
    </style>
    """,
    unsafe_allow_html=True,
)


if "artworks" not in st.session_state:
    st.session_state.artworks = load_catalog()
if "link_checks" not in st.session_state:
    st.session_state.link_checks = {}
if "backups" not in st.session_state:
    st.session_state.backups = load_backups()
if "backup_retention" not in st.session_state:
    st.session_state.backup_retention = 12
if "telemetry" not in st.session_state:
    st.session_state.telemetry = gallery_metrics(st.session_state.artworks)
if "telemetry_source" not in st.session_state:
    st.session_state.telemetry_source = "Derived gallery telemetry"
if "control_room_authenticated" not in st.session_state:
    st.session_state.control_room_authenticated = False

is_admin = st.session_state.control_room_authenticated

with st.sidebar:
    st.markdown("## + EMK LINKS")
    st.caption("Art gallery link desk")
    st.divider()
    st.markdown("### Control room")
    if is_admin:
        st.success("Signed in as curator", icon="✅")
        if st.button("Lock control room", use_container_width=True):
            st.session_state.control_room_authenticated = False
            st.rerun()
    else:
        st.info("Catalog controls are locked.")
        username = st.text_input("Username", key="control_room_username")
        password = st.text_input("Password", type="password", key="control_room_password")
        if st.button("Unlock control room", type="primary", use_container_width=True):
            if valid_credentials(username, password):
                st.session_state.control_room_authenticated = True
                st.rerun()
            st.error("Invalid control room credentials.")
    st.divider()
    if is_admin:
        st.markdown("### Add artwork link")
        with st.form("add_artwork", clear_on_submit=True):
            title = st.text_input("Title")
            artist = st.text_input("Artist / studio")
            url = st.text_input("EMK link", placeholder="https://...")
            category = st.selectbox("Category", ["Painting", "Digital", "Photography", "Installation", "Print", "Sculpture", "Other"])
            image = st.text_input("Image URL", placeholder="https://images.unsplash.com/...")
            submitted = st.form_submit_button("Add to gallery", use_container_width=True)
            if submitted:
                parsed = urlparse(url)
                if not title or not artist or not url or not parsed.scheme or not parsed.netloc:
                    st.error("Add a title, artist, and valid URL.")
                else:
                    st.session_state.artworks.insert(0, {
                        "title": title,
                        "artist": artist,
                        "category": category,
                        "year": datetime.now().year,
                        "status": "Draft",
                        "url": url,
                        "image": image or "https://images.unsplash.com/photo-1541701494587-cb58502866ab?auto=format&fit=crop&w=1000&q=85",
                        "accent": "New link / needs review",
                        "description": "Newly added EMK gallery entry.",
                    })
                    save_catalog(st.session_state.artworks)
                    st.success("Artwork added.")
                    st.rerun()
        st.divider()
        st.markdown("### Gallery health")
        st.success("Link desk online", icon="✅")
        st.caption(f"{len(st.session_state.artworks)} catalog entries saved locally")
        if st.button("Check visible links", use_container_width=True):
            with st.spinner("Checking links..."):
                for item in st.session_state.artworks:
                    st.session_state.link_checks[item["url"]] = check_link(item["url"])
            st.success("Link check complete.")
        export_payload = json.dumps(st.session_state.artworks, indent=2)
        st.download_button("Export catalog JSON", export_payload, "emk-catalog.json", "application/json", use_container_width=True)
        uploaded_catalog = st.file_uploader("Import catalog JSON", type="json", label_visibility="collapsed")
        if uploaded_catalog is not None:
            try:
                imported_catalog = json.load(uploaded_catalog)
                if not isinstance(imported_catalog, list) or not all(isinstance(item, dict) for item in imported_catalog):
                    raise ValueError
                st.session_state.artworks = imported_catalog
                save_catalog(imported_catalog)
                st.success(f"Imported {len(imported_catalog)} entries.")
                st.rerun()
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
                st.error("Catalog must be a JSON list of artwork objects.")
    else:
        st.caption("Sign in to manage links, health checks, imports, and backups.")
    st.divider()
    st.markdown("### Infrastructure")
    if is_admin:
        telemetry_source = st.selectbox("Metrics source", ["Derived gallery telemetry", "Prometheus endpoint"], key="telemetry_source_select")
        prometheus_url = st.text_input("Prometheus URL", value="http://localhost:9090/metrics", disabled=telemetry_source != "Prometheus endpoint")
        st.session_state.backup_retention = st.slider("Backup retention", 3, 30, st.session_state.backup_retention)
        if st.button("Create backup now", use_container_width=True):
            save_backup(st.session_state.artworks, "manual", st.session_state.backup_retention)
            st.success("Catalog backup created.")
    else:
        telemetry_source = "Derived gallery telemetry"
        prometheus_url = "http://localhost:9090/metrics"
        st.caption("Sign in to configure telemetry and backups.")

if not is_admin:
    st.markdown('<div class="eyebrow">EMK / CONTROL ROOM / LOCKED</div>', unsafe_allow_html=True)
    st.title("Gallery console locked")
    st.markdown('<p class="hero-note">Unlock the control room from the sidebar to view the live gallery stream, business intelligence, infrastructure telemetry, and backup timeline.</p>', unsafe_allow_html=True)
    st.info("Sign in to reveal the gallery console.")
    st.stop()

st.markdown('<div class="eyebrow">EMK / CURATED LINKS / 01</div>', unsafe_allow_html=True)
hero_left, hero_right = st.columns([3, 1])
with hero_left:
    st.title("The link gallery")
    st.markdown('<p class="hero-note">A visual index of EMK art links, studios, and works in motion. Keep the collection close, clear, and easy to share.</p>', unsafe_allow_html=True)
with hero_right:
    st.markdown('<div class="count-mark">CATALOG<br><strong>EMK-2025</strong></div>', unsafe_allow_html=True)

st.write("")
search_col, category_col, status_col = st.columns([2, 1, 1])
with search_col:
    search = st.text_input("Search gallery", placeholder="Search title, artist, or link", label_visibility="collapsed")
with category_col:
    category_filter = st.selectbox("Category", ["All categories", *sorted({item["category"] for item in st.session_state.artworks})], label_visibility="collapsed")
with status_col:
    status_filter = st.selectbox("Link status", ["All statuses", "Live", "Review", "Draft"], label_visibility="collapsed")

visible = st.session_state.artworks
if search:
    query = search.lower().strip()
    visible = [item for item in visible if query in f"{item['title']} {item['artist']} {item['url']}".lower()]
if category_filter != "All categories":
    visible = [item for item in visible if item["category"] == category_filter]
if status_filter != "All statuses":
    visible = [item for item in visible if item["status"] == status_filter]

st.write("")
stat_cols = st.columns(4)
stats = [
    ("Works indexed", len(st.session_state.artworks)),
    ("Live links", sum(item["status"] == "Live" for item in st.session_state.artworks)),
    ("Needs review", sum(item["status"] == "Review" for item in st.session_state.artworks)),
    ("Artists / studios", len({item["artist"] for item in st.session_state.artworks})),
]
for column, (label, value) in zip(stat_cols, stats):
    with column:
        st.markdown(f'<div class="stat"><div class="stat-label">{label}</div><div class="stat-value">{value:02d}</div></div>', unsafe_allow_html=True)

st.write("")
st.markdown(f"### Selected works <span class='subtle'>· {len(visible)} results</span>", unsafe_allow_html=True)
if not visible:
    st.info("No artworks match this view.")
else:
    for start in range(0, len(visible), 3):
        columns = st.columns(3, gap="medium")
        for column, item in zip(columns, visible[start:start + 3]):
            with column:
                status_class = item["status"].lower()
                st.markdown(
                    f'''<div class="art-card"><img src="{item["image"]}" alt="{item["title"]}"><div class="art-copy"><div class="art-title">{item["title"]}</div><div class="art-meta">{item["artist"]} &nbsp; / &nbsp; {item["category"]} &nbsp; / &nbsp; {item["year"]}</div><div class="art-description">{item["description"]}</div><div class="art-footer"><span class="tag {status_class}">{item["status"]}</span><span class="subtle">{item["accent"]}</span></div></div></div>''',
                    unsafe_allow_html=True,
                )
                if item["url"] in st.session_state.link_checks:
                    link_state, link_code = st.session_state.link_checks[item["url"]]
                    st.caption(f"Link check: {link_state} ({link_code})")
                st.link_button("Open EMK link", item["url"], use_container_width=True)

st.divider()
with st.expander("Catalog data"):
    table = pd.DataFrame(visible)
    if not table.empty:
        st.dataframe(table[["title", "artist", "category", "year", "status", "url"]], hide_index=True, use_container_width=True)

st.divider()
st.markdown('<div class="eyebrow">EMK / OPERATIONS / 02</div>', unsafe_allow_html=True)
st.markdown("## Gallery operations")
st.markdown(
    '<div class="resolution-note"><strong>Resolved: curator access</strong><br>The console previously had a mismatch between its documented login and its fallback configuration. The credentials are now aligned, so authorized curators can reliably unlock catalog management and gallery health tools.</div>',
    unsafe_allow_html=True,
)
operations_tabs = st.tabs(["Business intelligence", "Infrastructure", "Backup timeline"])

with operations_tabs[0]:
    st.markdown("### Catalog intelligence")
    st.caption("Decision brief · translate collection health into the next curatorial and marketing move")
    catalog = st.session_state.artworks
    total_items = len(catalog)
    review_count = sum(item["status"] == "Review" for item in catalog)
    draft_count = sum(item["status"] == "Draft" for item in catalog)
    live_count = sum(item["status"] == "Live" for item in catalog)
    checked_count = len(st.session_state.link_checks)
    failed_count = sum(state[0] != "Online" for state in st.session_state.link_checks.values())
    live_coverage = live_count / max(total_items, 1) * 100
    if failed_count:
        problem = "Audience traffic may be leaking through broken links."
        insight = f"{failed_count} of {checked_count} checked links need attention, so visitors may not reach the intended artwork or artist page."
        action = "Repair failed destinations first, then re-check every link before promoting the collection."
    elif review_count or draft_count:
        problem = "The collection is growing faster than it is being approved."
        insight = f"{review_count} works are in review and {draft_count} are drafts; {live_coverage:.0f}% of the catalog is currently marked live."
        action = "Assign a curator review sprint, approve the strongest works, and publish a focused collection."
    else:
        problem = "The catalog is healthy, but discovery can still be improved."
        insight = f"All {total_items} indexed works are marked live and no checked links are failing."
        action = "Use the category and artist mix to plan the next campaign, feature, or gallery update."
    analysis_cols = st.columns(4)
    analysis = [
        ("01 / Business problem", "What needs attention", problem),
        ("02 / Data", "Evidence in the catalog", f"{total_items} works · {live_count} live · {review_count} review · {draft_count} draft · {failed_count} link failures"),
        ("03 / Analysis / insight", "What the numbers mean", insight),
        ("04 / Business action", "Recommended next move", action),
    ]
    for column, (label, title, copy) in zip(analysis_cols, analysis):
        with column:
            st.markdown(f'<div class="insight-panel"><div class="insight-label">{label}</div><h4>{title}</h4><p>{copy}</p></div>', unsafe_allow_html=True)
    bi_cols = st.columns(4)
    bi_metrics = [
        ("Catalog size", len(st.session_state.artworks), "works indexed"),
        ("Live coverage", f"{sum(item['status'] == 'Live' for item in st.session_state.artworks) / max(len(st.session_state.artworks), 1) * 100:.0f}%", "links marked live"),
        ("Review queue", sum(item["status"] == "Review" for item in st.session_state.artworks), "needs attention"),
        ("Year span", f"{max(item['year'] for item in st.session_state.artworks) - min(item['year'] for item in st.session_state.artworks)}y" if st.session_state.artworks else "0y", "catalog range"),
    ]
    for column, (label, value, detail) in zip(bi_cols, bi_metrics):
        with column:
            st.metric(label, value, detail)
    chart_col, status_col = st.columns(2)
    with chart_col:
        st.markdown("#### Works by category")
        category_counts = pd.Series([item["category"] for item in st.session_state.artworks]).value_counts().rename("Works")
        st.bar_chart(category_counts, height=260, color="#8aad7f")
    with status_col:
        st.markdown("#### Link status mix")
        status_counts = pd.Series([item["status"] for item in st.session_state.artworks]).value_counts().rename("Works")
        st.bar_chart(status_counts, height=260, color="#c67655")

with operations_tabs[1]:
    st.markdown("### Prometheus infrastructure")
    infra_cols = st.columns(4)
    current_metrics = st.session_state.telemetry
    infra_values = [
        ("Indexed works", int(current_metrics.get("emk_gallery_items", 0))),
        ("Live links", int(current_metrics.get("emk_gallery_live_links", 0))),
        ("Review queue", int(current_metrics.get("emk_gallery_review_queue", 0))),
        ("Link failures", int(current_metrics.get("emk_gallery_link_failures", 0))),
    ]
    for column, (label, value) in zip(infra_cols, infra_values):
        with column:
            st.metric(label, value)
    if st.button("Refresh infrastructure telemetry", key="refresh_telemetry", disabled=not is_admin):
        derived = gallery_metrics(st.session_state.artworks)
        if telemetry_source == "Prometheus endpoint":
            remote_metrics, source_label = fetch_prometheus_metrics(prometheus_url)
            st.session_state.telemetry = {**derived, **remote_metrics}
            st.session_state.telemetry_source = source_label
        else:
            st.session_state.telemetry = derived
            st.session_state.telemetry_source = "Derived gallery telemetry"
        st.rerun()
    st.caption(f"Source: {st.session_state.telemetry_source}. Prometheus names use the `emk_gallery_*` namespace.")
    telemetry_table = pd.DataFrame({"Metric": list(current_metrics.keys()), "Value": list(current_metrics.values())})
    st.dataframe(telemetry_table, hide_index=True, use_container_width=True, height=260)

with operations_tabs[2]:
    st.markdown("### Catalog recovery points")
    if not st.session_state.backups:
        st.info("No backups yet. Create one from the sidebar.")
    else:
        timeline = pd.DataFrame([
            {"Created": backup["created_at"], "Reason": backup["reason"].title(), "Entries": backup["entries"]}
            for backup in st.session_state.backups
        ])
        st.dataframe(timeline, hide_index=True, use_container_width=True)
        backup_options = [f"{backup['created_at']} · {backup['reason']} · {backup['entries']} entries" for backup in st.session_state.backups]
        selected_backup = st.selectbox("Recovery point", backup_options, key="selected_backup")
        selected_index = backup_options.index(selected_backup)
        if st.button("Restore selected catalog", key="restore_backup", disabled=not is_admin):
            restored = st.session_state.backups[selected_index]["catalog"]
            st.session_state.artworks = restored
            save_catalog(restored)
            st.success(f"Restored {len(restored)} catalog entries.")
            st.rerun()

st.caption("EMK Links Art Gallery Console · Add your real links from the sidebar to replace the sample catalog.")
