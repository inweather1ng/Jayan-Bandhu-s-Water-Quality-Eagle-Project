import base64
from datetime import datetime
import io
import json
import os
import urllib.request
import folium
import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="Creek Trash Watch", layout="wide", page_icon="📸")
st.markdown('<style>[data-testid="stToolbarActions"], [data-testid="stMainMenu"] { display: none !important; }</style>', unsafe_allow_html=True)
st.title("Creek Trash Watch")

# ==============================================================================
# COMING SOON BANNER (Live code preserved below)
# ==============================================================================
st.info(
    "🚧 **COMING SOON — Creek Trash Watch (Community Photo & Habitat Reporting Portal)**\n\n"
    "Two-step GPS map-tagging and photo upload portal covering all creeks and tributaries "
    "across the 101-sq-mi **Dry Creek Watershed**."
)

# Hold off on executing the live interactive Photo Upload code below while keeping all code intact:
st.stop()

st.write("Step 1: Choose any creek across the entire Dry Creek Watershed (or view the full watershed) and click the exact spot on the map. Step 2: Upload or take a photo.")

GITHUB_REPO = "inweather1ng/Jayan-Bandhu-s-Water-Quality-Eagle-Project"
LOG_FILE = "photo_logs.csv"

# Entire 101 sq mi Dry Creek Watershed (Loomis / Rocklin / Granite Bay -> Roseville -> Rio Linda)
CREEK_SITES = {
    "Entire Dry Creek Watershed (Full Basin View)": (38.7580, -121.2850, 12),
    "Dry Creek — Saugstad Park (Roseville)": (38.7428, -121.2845, 17),
    "Dry Creek — Royer Park (Downtown Roseville)": (38.7468, -121.2832, 17),
    "Dry Creek — Riverside Ave / Darling Way (Roseville)": (38.7325, -121.3038, 16),
    "Dry Creek — Cook Riolo Rd (West Roseville / Placer-Sac Line)": (38.7192, -121.3595, 16),
    "Dry Creek Parkway — Rio Linda / Cherry Island (Sacramento Co.)": (38.6915, -121.4480, 15),
    "Secret Ravine — Sierra College Blvd (Roseville / Rocklin)": (38.7593, -121.2563, 17),
    "Secret Ravine — Rocklin Rd & Loomis Basin (Upper Reach)": (38.8035, -121.2015, 15),
    "Miners Ravine — Sculpture Park (Roseville)": (38.7603, -121.2494, 17),
    "Miners Ravine — Folsom Rd & Granite Bay (Upper Reach)": (38.7632, -121.1845, 15),
    "Antelope Creek — Multi-Use Trail (Roseville / Rocklin)": (38.7626, -121.2605, 16),
    "Clover Valley Creek (Rocklin)": (38.8085, -121.2360, 15),
    "Linda Creek — Champion Oaks (Roseville / Granite Bay)": (38.7315, -121.2380, 16),
    "Cirby Creek (Roseville)": (38.7285, -121.2750, 16),
    "Strap Ravine & Sucker Ravine (Roseville / Granite Bay)": (38.7420, -121.2190, 15),
}


def _get_github_token():
    try:
        return str(st.secrets.get("GITHUB_TOKEN", os.environ.get("GITHUB_TOKEN", ""))).strip()
    except Exception:
        return str(os.environ.get("GITHUB_TOKEN", "")).strip()


def load_photo_logs():
    frames = []
    # 1. Load live cloud photo_logs.csv from GitHub repo so code updates/reboots never lose photos
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{LOG_FILE}"
        headers = {"User-Agent": "DryCreekTrashWatch/1.0", "Accept": "application/vnd.github.v3.raw"}
        token = _get_github_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as resp:
            cloud_df = pd.read_csv(io.BytesIO(resp.read()))
            if not cloud_df.empty:
                frames.append(cloud_df)
    except Exception:
        pass

    # 2. Merge with local container photo_logs.csv if present
    if os.path.exists(LOG_FILE):
        try:
            local_df = pd.read_csv(LOG_FILE)
            if not local_df.empty:
                frames.append(local_df)
        except Exception:
            pass

    if not frames:
        return []
    merged = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["Time", "Lat", "Lon", "Issue"], keep="last")
    merged.to_csv(LOG_FILE, index=False)
    return merged.to_dict("records")


def autosave_photo_logs(records):
    df = pd.DataFrame(records)
    if df.empty:
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
    else:
        df.to_csv(LOG_FILE, index=False)

    token = _get_github_token()
    if not token:
        return False

    try:
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{LOG_FILE}"
        headers = {
            "User-Agent": "DryCreekTrashWatch/1.0",
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        }
        sha = None
        remote_frames = []
        try:
            get_req = urllib.request.Request(api_url, headers=headers)
            with urllib.request.urlopen(get_req, timeout=6) as resp:
                meta = json.loads(resp.read().decode("utf-8"))
                sha = meta.get("sha")
                if meta.get("content") and not df.empty:
                    raw_csv = base64.b64decode(meta["content"])
                    remote_df = pd.read_csv(io.BytesIO(raw_csv))
                    if not remote_df.empty:
                        remote_frames.append(remote_df)
        except Exception:
            pass

        if not df.empty and remote_frames:
            df = pd.concat(remote_frames + [df], ignore_index=True).drop_duplicates(
                subset=["Time", "Lat", "Lon", "Issue"], keep="last"
            )
            df.to_csv(LOG_FILE, index=False)

        csv_bytes = df.to_csv(index=False).encode("utf-8") if not df.empty else b"Time,Issue,Location,Lat,Lon,Note,ThumbB64\n"
        payload = {
            "message": f"Auto-save citizen Creek Trash Watch photo log ({len(df)} records)",
            "content": base64.b64encode(csv_bytes).decode("utf-8"),
        }
        if sha:
            payload["sha"] = sha

        put_req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="PUT",
        )
        with urllib.request.urlopen(put_req, timeout=8) as _:
            return True
    except Exception:
        return False


if "photo_logs" not in st.session_state:
    st.session_state.photo_logs = load_photo_logs()

if "tagged_spot" not in st.session_state:
    st.session_state.tagged_spot = None

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Tag Location & Upload Photo")
    selected_site = st.selectbox(
        "Zoom map to any creek in the Dry Creek Watershed (or view Entire Watershed):",
        list(CREEK_SITES.keys()),
        on_change=lambda: st.session_state.update(tagged_spot=None),
    )

    not_tagged = st.session_state.tagged_spot is None
    if not_tagged:
        st.warning("⚠️ **Action Required:** Please click on the map on the right to tag where the photo was taken before uploading a photo.")
    else:
        st.success(f"📌 **Map Spot Tagged:** `{st.session_state.tagged_spot[0]}, {st.session_state.tagged_spot[1]}` — You can now upload or take your photo!")
        if st.button("Reset Map Tag"):
            st.session_state.tagged_spot = None
            st.rerun()

    mode = st.radio("Photo Source:", ["Upload Photo", "Take Photo with Phone Camera"], horizontal=True, disabled=not_tagged)
    uploaded_file = (
        st.file_uploader("Upload Creek Photo (JPG/PNG)", type=["jpg", "jpeg", "png"], disabled=not_tagged)
        if mode == "Upload Photo"
        else st.camera_input("Take Photo with Phone Camera", disabled=not_tagged)
    )
    note = st.text_input("Optional note about the photo:", disabled=not_tagged)

    if uploaded_file is not None:
        if not_tagged:
            st.error("⚠️ Please click on the map to tag the location first before uploading a photo!")
        else:
            img = Image.open(uploaded_file)
            st.image(img, width=250)

            lat, lon = st.session_state.tagged_spot
            loc_source = f"{selected_site} (Map Tag)"

            # Simple issue parser from image pixels + note
            arr = np.array(img.convert("RGB").resize((100, 100)))
            bright_pct = float(((arr[:, :, 0] > 210) & (arr[:, :, 1] > 210) & (arr[:, :, 2] > 210)).mean() * 100)
            text = note.lower()
            if any(w in text for w in ["salmon", "fish", "wildlife"]):
                auto_issue = "Salmon / Wildlife Sighting"
            elif any(w in text for w in ["erosion", "bank", "log", "block"]):
                auto_issue = "Bank Erosion / Channel Blockage"
            elif any(w in text for w in ["foam", "murky", "turbid", "runoff"]):
                auto_issue = "Turbid Water / Runoff"
            elif bright_pct > 6.0 or any(w in text for w in ["trash", "litter", "plastic", "bottle", "can", "bag"]):
                auto_issue = "Trash / Litter Along Creek"
            else:
                auto_issue = "Trash / Litter Along Creek"

            issue = st.selectbox(
                "Parsed Issue:",
                ["Trash / Litter Along Creek", "Turbid Water / Runoff", "Bank Erosion / Channel Blockage", "Salmon / Wildlife Sighting"],
                index=["Trash / Litter Along Creek", "Turbid Water / Runoff", "Bank Erosion / Channel Blockage", "Salmon / Wildlife Sighting"].index(auto_issue),
            )
            st.write(f"**Tagged Location:** `{lat}, {lon}` ({loc_source})")

            if st.button("Log Photo to Map", type="primary"):
                thumb = img.convert("RGB").copy()
                thumb.thumbnail((220, 220))
                buf = io.BytesIO()
                thumb.save(buf, format="JPEG", quality=72)
                b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")

                st.session_state.photo_logs.append(
                    {
                        "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Issue": issue,
                        "Location": loc_source,
                        "Lat": lat,
                        "Lon": lon,
                        "Note": note,
                        "ThumbB64": b64_img,
                    }
                )
                autosave_photo_logs(st.session_state.photo_logs)
                st.session_state.tagged_spot = None
                st.success("Photo logged and auto-saved!")
                st.rerun()

with col2:
    st.subheader("2. Dry Creek Watershed Map (Click Spot First to Unlock Photo Upload)")
    site_lat, site_lon, site_zoom = CREEK_SITES[selected_site]
    center = list(st.session_state.tagged_spot) if st.session_state.tagged_spot else [site_lat, site_lon]
    zoom_lvl = 17 if st.session_state.tagged_spot else site_zoom
    m = folium.Map(location=center, zoom_start=zoom_lvl)

    # Show blue preview pin where the user clicked on the map prior to uploading
    if st.session_state.tagged_spot is not None:
        folium.Marker(
            location=list(st.session_state.tagged_spot),
            tooltip=f"📌 Tagged Spot ({st.session_state.tagged_spot[0]}, {st.session_state.tagged_spot[1]})",
            icon=folium.Icon(color="cadetblue", icon="thumb-tack", prefix="fa"),
        ).add_to(m)

    # Show all logged photo bubbles
    for item in st.session_state.photo_logs:
        popup_html = (
            f"<b>{item['Issue']}</b><br>"
            f"<img src='data:image/jpeg;base64,{item['ThumbB64']}' width='180' style='border-radius:6px;margin:4px 0;'><br>"
            f"Location: {item['Location']} ({item['Lat']}, {item['Lon']})<br>"
            f"Note: {item['Note']}"
        )
        folium.Marker(
            location=[item["Lat"], item["Lon"]],
            tooltip=item["Issue"],
            popup=folium.Popup(popup_html, max_width=210),
            icon=folium.Icon(color="red" if "Trash" in str(item["Issue"]) else "green", icon="camera", prefix="fa"),
        ).add_to(m)

    map_click = st_folium(m, width=600, height=450, key=f"creek_photo_map_{selected_site}")
    if map_click and map_click.get("last_clicked"):
        clicked = (round(map_click["last_clicked"]["lat"], 5), round(map_click["last_clicked"]["lng"], 5))
        if st.session_state.tagged_spot != clicked:
            st.session_state.tagged_spot = clicked
            st.rerun()

if st.session_state.photo_logs:
    st.subheader("Logged Creek Photos")
    full_df = pd.DataFrame(st.session_state.photo_logs)
    df_logs = full_df.drop(columns=["ThumbB64"], errors="ignore")
    st.dataframe(df_logs, use_container_width=True)
    b1, b2 = st.columns(2)
    with b1:
        st.download_button(
            "📥 Download Photo Logs Backup (CSV)",
            data=full_df.to_csv(index=False).encode("utf-8"),
            file_name="photo_logs.csv",
            mime="text/csv",
        )
    with b2:
        if st.button("Clear All Logged Photos"):
            st.session_state.photo_logs = []
            autosave_photo_logs([])
            st.rerun()
