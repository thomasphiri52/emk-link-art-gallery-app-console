# EMK Links Art Gallery Console

A Streamlit visual index for EMK art links, artists, studios, and gallery works.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Visitor link

Use the public embed URL when sharing the gallery with visitors:

https://emk-links-art-gallery-console-yq2mayvjbdiappem9wjnjf.streamlit.app/?embed=true

The `embed=true` link opens the gallery directly and avoids the Streamlit Cloud dashboard redirect.

The initial catalog includes sample entries and public image references so the interface is immediately visible. Use the sidebar form to add real EMK links and image URLs.

The catalog is saved locally in `catalog.json` after each addition. The sidebar also supports JSON export/import and a live HEAD-request check for every catalog link. Replace the sample links with your real EMK URLs before publishing the app.

## Operations console

The gallery includes three operational views below the catalog:

- **Business intelligence**: catalog size, live coverage, review queue, year span, category mix, and status mix.
- **Infrastructure**: derived gallery telemetry by default, or metrics from a Prometheus `/metrics` endpoint. Prometheus metrics use the `emk_gallery_*` namespace.
- **Backup timeline**: create local JSON recovery points, retain a configurable number, inspect the timeline, and restore a selected catalog snapshot.

Backups are stored in `catalog_backups.json` beside the app. For production use, replace the local JSON files with durable storage.

## Control room

The gallery is publicly browseable, while catalog changes and operational actions require curator access. Local credentials are configured in `.streamlit/secrets.toml`:

```toml
[control_room]
username = "admin"
password = "emk-gallery"
```

Copy `.streamlit/secrets.toml.example` and replace the password before deploying. The control room protects artwork additions, catalog import/export, link checks, Prometheus refreshes, backup creation, and catalog restore.
