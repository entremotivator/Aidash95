import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import json

st.set_page_config(page_title="Call Analysis CRM - Universal Audio", layout="wide")
st.title("📞 Call CRM Dashboard")
st.caption("Live analytics from Google Sheets | Advanced filtering | Universal audio player for all major formats")

GSHEET_URL = "https://docs.google.com/spreadsheets/d/1LFfNwb9lRQpIosSEvV3O6zIwymUIWeG9L_k7cxw1jQs/edit?gid=0"

# --------------- COLUMN DEFINITIONS ---------------
EXPECTED_COLUMNS = [
    "call_id", "customer_name", "email", "phone number", "Booking Status", "voice_agent_name",
    "call_date", "call_start_time", "call_end_time", "call_duration_seconds", "call_duration_hms",
    "cost", "call_success", "appointment_scheduled", "intent_detected", "sentiment_score",
    "confidence_score", "keyword_tags", "summary_word_count", "transcript", "summary",
    "action_items", "call_recording_url", "customer_satisfaction", "resolution_time_seconds",
    "escalation_required", "language_detected", "emotion_detected", "speech_rate_wpm",
    "silence_percentage", "interruption_count", "ai_accuracy_score", "follow_up_required",
    "customer_tier", "call_complexity", "agent_performance_score", "call_outcome",
    "revenue_impact", "lead_quality_score", "conversion_probability", "next_best_action",
    "customer_lifetime_value", "call_category", "Upload_Timestamp"
]

SUPPORTED_AUDIO_EXTS = [
    "mp3", "wav", "ogg", "flac", "aac", "m4a", "webm", "oga",
]
AUDIO_FORMAT_ICONS = {
    "mp3": "🎵", "wav": "🔊", "ogg": "🦉", "flac": "💠", "aac": "🎼", "m4a": "🎶", "webm": "🌐", "oga": "📀"
}

# --------- SIDEBAR: AUTH & FILTERS ----------
with st.sidebar:
    st.header("🔑 Authentication Status")
    
    if st.session_state.get("global_gsheets_creds"):
        st.success("✅ Using Global Credentials")
        client_email = st.session_state.global_gsheets_creds.get('client_email', 'Unknown')
        st.info(f"📧 Service Account: {client_email[:30]}...")
        
        if st.button("🧪 Test Connection"):
            try:
                json_dict = st.session_state.global_gsheets_creds
                scope = [
                    "https://spreadsheets.google.com/feeds",
                    "https://www.googleapis.com/auth/drive"
                ]
                creds = ServiceAccountCredentials.from_json_keyfile_dict(json_dict, scope)
                client = gspread.authorize(creds)
                sheet = client.open_by_url(GSHEET_URL).sheet1
                st.success("✅ Connection successful!")
            except Exception as e:
                st.error(f"❌ Connection failed: {e}")
    else:
        st.error("❌ No global credentials found")
        st.info("Please upload service account JSON in the main sidebar")
    st.divider()
    st.header("🔍 Call Filters")
    customer_name = st.text_input("Customer Name")
    agent_name = st.text_input("Voice Agent Name")
    call_success = st.selectbox("Call Success", ["", "Yes", "No"])
    sentiment_range = st.slider("Sentiment Score", -1.0, 1.0, (-1.0, 1.0))
    st.info("Apply multiple filters together for precision search.\nAudio tab supports MP3, WAV, OGG, FLAC, AAC, M4A, WEBM & more*")

# --------- DATA LOADING ----------
@st.cache_data(show_spinner=True)
def load_data():
    global_creds = st.session_state.get("global_gsheets_creds")
    if global_creds is None:
        st.info("Please ensure Google Service Account credentials are uploaded in the sidebar.")
        return pd.DataFrame(columns=EXPECTED_COLUMNS)
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(global_creds, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(GSHEET_URL).sheet1
        df = get_as_dataframe(sheet, evaluate_formulas=True).dropna(how="all")
        df.columns = [col.strip() for col in df.columns]
        return df
    except Exception as e:
        st.warning(f"⚠️ Could not load live data. Using placeholder columns. Error: {e}")
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

df = load_data()

for col in EXPECTED_COLUMNS:
    if col not in df.columns:
        df[col] = ""
df = df[EXPECTED_COLUMNS]

# -------- FILTER LOGIC ----------
filtered_df = df.copy()
if customer_name:
    filtered_df = filtered_df[filtered_df["customer_name"].str.contains(customer_name, case=False, na=False)]
if agent_name:
    filtered_df = filtered_df[filtered_df["voice_agent_name"].str.contains(agent_name, case=False, na=False)]
if call_success:
    filtered_df = filtered_df[filtered_df["call_success"].astype(str).str.lower() == call_success.lower()]
filtered_df = filtered_df[
    (filtered_df["sentiment_score"].astype(str).replace("None", "0").astype(float) >= sentiment_range[0]) &
    (filtered_df["sentiment_score"].astype(str).replace("None", "0").astype(float) <= sentiment_range[1])
]

# --------- ANALYTICS FUNCTIONS -------
def readable_sec(seconds):
    """Turn seconds into h:mm:ss."""
    try:
        seconds = int(float(seconds))
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
    except Exception:
        return str(seconds)

# ------- MAIN TABS ----------
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Call Log", "📊 Analytics", "🧠 AI Summary", "🔊 Audio/Recordings"
])

with tab1:
    st.subheader("📋 Full Call Log Table")
    st.dataframe(filtered_df, use_container_width=True)
    st.caption(f"Showing {len(filtered_df)} calls out of {len(df)} total records.")

with tab2:
    st.subheader("📊 Analytics & Insights")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Calls", len(df))
    with col2:
        st.metric("Unique Customers", df["customer_name"].nunique())
    with col3:
        st.metric("Programs/Agents", df["voice_agent_name"].nunique())
    with col4:
        st.metric("Success Rate (%)", f"{100*df['call_success'].str.lower().eq('yes').mean():.1f}" if len(df) else "-")
    with col5:
        durs = pd.to_numeric(df["call_duration_seconds"], errors='coerce').dropna()
        st.metric("Avg Duration (min)", f"{(durs.mean()/60):.2f}" if not durs.empty else "-")

    st.markdown("#### 📈 Calls by Agent")
    st.bar_chart(df["voice_agent_name"].value_counts())
    st.markdown("#### 🎯 Conversion Probabilities")
    st.line_chart(pd.to_numeric(df["conversion_probability"], errors="coerce"))
    st.markdown("#### 📅 Calls per Day")
    calls_by_date = df.groupby("call_date")["call_id"].count()
    if not calls_by_date.empty:
        st.area_chart(calls_by_date)
    else:
        st.info("No date data to plot.")

with tab3:
    st.subheader("🧠 AI Insights: Summaries & Next Actions")
    if filtered_df.empty:
        st.info("No results for these filters.")
    else:
        for idx, row in filtered_df.iterrows():
            with st.expander(f"📞 {row['call_id']} - {row['customer_name']} ({row['call_date']})"):
                st.write(f"**Agent:** {row['voice_agent_name']}")
                st.write(f"**Outcome:** {row['call_outcome']} | **Success:** {row['call_success']}")
                st.markdown(f"**Summary:** {row['summary']}")
                st.markdown(f"**Action Items:** {row['action_items']}")
                if row["transcript"]:
                    st.markdown("**Transcript Preview:**")
                    st.text(row["transcript"][:1500] + " ...")
                else:
                    st.info("No transcript found for this call.")

with tab4:
    st.subheader("🔊 Audio Recordings: Universal Format Support")
    st.caption(
        "Playable call recordings for all popular audio formats: MP3, WAV, OGG, FLAC, AAC, M4A, WEBM, OGA, etc. "
        "Browser support depends on file type. For best experience, use direct URLs."
    )

    audiocount = 0
    for idx, row in filtered_df.iterrows():
        url = str(row["call_recording_url"]).strip()
        if url:
            audiocount += 1
            filename = url.split("/")[-1] if "/" in url else url
            ext = filename.split(".")[-1].lower() if "." in filename else None
            icon = AUDIO_FORMAT_ICONS.get(ext, "🎧")
            st.markdown(f"---\n**{icon} {row['call_id']} — {row['customer_name']}**")
            st.write(f"**Audio file:** `{filename}` | **Format:** `{ext or 'Unknown'}`")

            # Attempt st.audio play, fallback to clickable link
            if ext in SUPPORTED_AUDIO_EXTS or ext is None:  # Try anyway; browsers may support more
                try:
                    st.audio(url)
                except Exception as e:
                    st.warning(f"Could not play audio in-app: {e}")
                    st.markdown(f"[Play/download manually]({url})")
            else:
                st.warning(f"Audio file appears to be an unsupported format: `{ext}`. [Manual link]({url})")

            # Transcript preview if available
            if row["transcript"]:
                with st.expander("📝 Transcript Preview"):
                    st.text(row["transcript"][:1000] + ("..." if len(row["transcript"])>1000 else ""))
            st.caption("Supported: mp3, wav, ogg, flac, aac, m4a, webm, oga & more by browser. "
                       "If playback fails, try manual download.")
    if audiocount == 0:
        st.info("No recordings found in filtered results.")

st.success("✅ Dashboard loaded. Explore all calls, deep analytics, summaries, and play recordings of any major audio format!")

# ------- USER HELP AND TIPS -------
st.markdown(
    """
    <hr>
    <h6>ℹ️ Audio Player Notes</h6>
    <ul>
      <li>Audio playback works for all common audio streaming formats directly supported by browsers (mp3, wav, ogg, flac, aac, m4a, webm, oga, etc).</li>
      <li>
        If the audio won't play inline, you can always click the download/play link shown.
        <br>Note: Some Google Drive links may require "Anyone with link" sharing for playback.
      </li>
      <li>
        If your call recordings use rare or proprietary file types, consider converting to <b>mp3</b> or <b>wav</b> for universal accessibility.
      </li>
      <li>
        You can combine multiple sidebar filters for deep dive (by agent, positive/negative sentiment, or customer name).
      </li>
    </ul>
    <b>Contact dev for support for even more advanced audio analytics, waveform, uploads, or instant call scoring!</b>
    """,
    unsafe_allow_html=True
)
