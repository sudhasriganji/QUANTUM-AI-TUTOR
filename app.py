import io
import hashlib
import re

import streamlit as st


# =========================================================
# OPTIONAL SPEECH RECOGNITION
# =========================================================

try:
    import speech_recognition as sr

    SPEECH_RECOGNITION_AVAILABLE = True

except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False


# =========================================================
# RAG + DATABASE
# DO NOT CHANGE
# =========================================================

import importlib
import rag_engine

rag_engine = importlib.reload(rag_engine)

answer_question = rag_engine.answer_question
create_chat_session = rag_engine.create_chat_session
delete_chat = rag_engine.delete_chat
get_or_create_user = rag_engine.get_or_create_user
get_user_sessions = rag_engine.get_user_sessions
rename_chat = rag_engine.rename_chat
restore_chat = rag_engine.restore_chat


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Quantum Lab | AI Tutor",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# SESSION STATE
# =========================================================

DEFAULTS = {
    "logged_in": False,
    "user_email": "",
    "user_id": None,

    "session_id": None,
    "messages": [],
    "sessions": [],

    "uploaded_files": [],
    "drive_links": [],

    "processed_audio_hash": None,
    "audio_version": 0,
    "voice_error": None,
    "recorded_audio_bytes": None,
    "recording_filename": "quantum_recording.wav",

    "rename_session_id": None,

    "show_canvas": False,
    "show_calculator": False,
    "show_notes": False,
    "learning_mode": False,

    "canvas_text": "",
    "notes_text": "",

    # Added for safe Save/Clear functionality
    "canvas_saved_text": "",
    "notes_saved_text": "",
    "canvas_version": 0,
    "notes_version": 0,

    "prompt_version": 0,

    "last_processed_prompt": "",

    "prompt_seed": "",
}


for key, value in DEFAULTS.items():

    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
<style>

/* =========================================================
   GOOGLE FONTS
   ========================================================= */

@import url(
'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap'
);


/* =========================================================
   GLOBAL
   ========================================================= */

html,
body,
[class*="css"] {

    font-family:
        "Inter",
        sans-serif;
}


.stApp {

    min-height: 100vh;

    background:

        radial-gradient(
            circle at 8% 10%,
            rgba(99,102,241,.18),
            transparent 28%
        ),

        radial-gradient(
            circle at 92% 8%,
            rgba(59,130,246,.13),
            transparent 28%
        ),

        radial-gradient(
            circle at 75% 85%,
            rgba(168,85,247,.12),
            transparent 30%
        ),

        linear-gradient(
            135deg,
            #020617 0%,
            #080b22 48%,
            #020617 100%
        );
}


/* =========================================================
   GRID BACKGROUND
   ========================================================= */

.stApp::before {

    content: "";

    position: fixed;

    inset: 0;

    pointer-events: none;

    background-image:

        linear-gradient(
            rgba(129,140,248,.025) 1px,
            transparent 1px
        ),

        linear-gradient(
            90deg,
            rgba(129,140,248,.025) 1px,
            transparent 1px
        );

    background-size: 55px 55px;

    z-index: 0;
}


/* =========================================================
   STARS
   ========================================================= */

.quantum-space {

    position: fixed;

    inset: 0;

    pointer-events: none;

    overflow: hidden;

    z-index: 0;
}


.quantum-space::before {

    content: "";

    position: absolute;

    inset: 0;

    background-image:

        radial-gradient(
            circle at 5% 12%,
            rgba(255,255,255,.9) 0px,
            transparent 2px
        ),

        radial-gradient(
            circle at 15% 37%,
            rgba(180,210,255,.8) 0px,
            transparent 2px
        ),

        radial-gradient(
            circle at 48% 22%,
            rgba(200,180,255,.8) 0px,
            transparent 2px
        ),

        radial-gradient(
            circle at 76% 68%,
            rgba(180,200,255,.7) 0px,
            transparent 2px
        ),

        radial-gradient(
            circle at 91% 31%,
            rgba(255,255,255,.7) 0px,
            transparent 2px
        );

    animation:
        starFloat 15s ease-in-out infinite alternate;
}


@keyframes starFloat {

    0% {

        transform:
            translateY(0px);

        opacity: .45;
    }

    50% {

        transform:
            translateY(-5px);

        opacity: .85;
    }

    100% {

        transform:
            translateY(4px);

        opacity: .55;
    }
}


/* =========================================================
   MAIN CONTAINER
   ========================================================= */

.main .block-container {

    max-width: 1250px;

    padding-top: 1rem;

    padding-bottom: 10rem;

    position: relative;

    z-index: 2;

}


/* =========================================================
   SIDEBAR
   ========================================================= */

section[data-testid="stSidebar"] {

    background:

        linear-gradient(
            180deg,
            #030611,
            #070b1d,
            #02040c
        );

    border-right:
        1px solid rgba(139,92,246,.20);
}


section[data-testid="stSidebar"] .stButton button {

    border-radius: 12px;

    border:
        1px solid rgba(139,92,246,.17);

    background:

        linear-gradient(
            135deg,
            rgba(18,25,53,.95),
            rgba(7,12,29,.95)
        );

    color: #dbeafe;

    transition:
        all .2s ease;
}


section[data-testid="stSidebar"] .stButton button:hover {

    border-color:
        rgba(167,139,250,.70);

    box-shadow:
        0 0 22px rgba(139,92,246,.20);

    transform:
        translateY(-1px);
}


/* =========================================================
   SIDEBAR CHAT BUTTONS
   ========================================================= */

.chat-history-title {

    color: #94a3b8;

    font-size: 10px;

    font-weight: 700;

    letter-spacing: 1.5px;

    margin:
        15px 0 8px 0;
}


/* =========================================================
   HEADER
   ========================================================= */

.quantum-logo {

    text-align: center;

    font-size: 70px;

    line-height: 1;

    margin:
        8px auto 5px auto;

    filter:
        drop-shadow(0 0 8px rgba(167,139,250,.9))
        drop-shadow(0 0 25px rgba(99,102,241,.65));

    animation:
        quantumPulse 3s ease-in-out infinite;
}


@keyframes quantumPulse {

    0%,100% {

        transform: scale(1);

        filter:
            drop-shadow(0 0 8px rgba(167,139,250,.7))
            drop-shadow(0 0 20px rgba(99,102,241,.5));
    }

    50% {

        transform: scale(1.07);

        filter:
            drop-shadow(0 0 12px rgba(255,255,255,.9))
            drop-shadow(0 0 35px rgba(139,92,246,.9));
    }
}


.main-title {
    text-align: center;
    font-size: 42px;
    font-weight: 800;
    color: #ffffff !important;
    opacity: 1 !important;
    margin-top: 10px;
}

.subtitle {
    text-align: center;
    font-size: 18px;
    font-weight: 500;
    color: #e2e8f0 !important;
    opacity: 1 !important;
    margin-bottom: 20px;
}

.online {
    text-align: center;
    color: #00ff88 !important;
    font-weight: bold;
    opacity: 1 !important;
    margin-bottom: 30px;
}


.quantum-line {

    width: 230px;

    height: 1px;

    margin:
        0 auto 22px auto;

    background:

        linear-gradient(
            90deg,
            transparent,
            rgba(139,92,246,.9),
            rgba(59,130,246,.9),
            transparent
        );

    box-shadow:
        0 0 14px rgba(139,92,246,.4);
}


/* =========================================================
   CHAT MESSAGES
   ========================================================= */

[data-testid="stChatMessage"] {

    border-radius: 16px;

    border:
        1px solid rgba(139,92,246,.12);

    background:

        linear-gradient(
            135deg,
            rgba(15,23,42,.82),
            rgba(7,12,28,.82)
        );

    margin-bottom: 10px;

    transition: all .2s ease;
}


[data-testid="stChatMessage"]:hover {

    border-color:
        rgba(139,92,246,.32);

    box-shadow:
        0 5px 25px rgba(0,0,0,.22);
}


[data-testid="stChatMessage"] p {

    color: #dbe4f0;

    line-height: 1.7;
}


/* =========================================================
   PROMPT CONTAINER
   ========================================================= */

.prompt-shell {

    margin-top: 25px;

    padding: 8px;

    border-radius: 22px;

    border:
        1px solid rgba(139,92,246,.30);

    background:

        linear-gradient(
            135deg,
            rgba(15,23,42,.96),
            rgba(7,12,28,.96)
        );

    box-shadow:

        0 0 30px rgba(99,102,241,.10),

        inset
        0 0 20px rgba(99,102,241,.035);

    transition:
        all .3s ease;
}


.prompt-shell:hover {

    border-color:
        rgba(139,92,246,.52);

    box-shadow:

        0 0 35px rgba(99,102,241,.18),

        inset
        0 0 25px rgba(99,102,241,.05);
}


.prompt-label {

    color: #64748b;

    font-size: 10px;

    font-weight: 700;

    letter-spacing: 1.1px;

    padding:
        2px 8px 4px 8px;
}


/* =========================================================
   TEXT INPUT
   ========================================================= */

.prompt-input input {

    background:
        rgba(15,23,42,.60) !important;

    border:
        1px solid rgba(71,85,105,.25) !important;

    border-radius:
        14px !important;

    color:
        #f8fafc !important;

    min-height:
        47px !important;

    font-size:
        14px !important;

    transition:
        all .2s ease;
}


.prompt-input input:focus {

    border-color:
        rgba(139,92,246,.55) !important;

    box-shadow:
        0 0 0 2px rgba(139,92,246,.07),
        0 0 22px rgba(99,102,241,.12) !important;
}


/* =========================================================
   TOOL BUTTONS
   ========================================================= */

.prompt-tool button {

    min-height:
        47px !important;

    border-radius:
        14px !important;

    background:
        rgba(15,23,42,.78) !important;

    border:
        1px solid rgba(100,116,139,.30) !important;

    color:
        #e2e8f0 !important;

    transition:
        all .2s ease !important;
}


.prompt-tool button:hover {

    transform:
        translateY(-2px);

    border-color:
        rgba(139,92,246,.65) !important;

    box-shadow:
        0 0 20px rgba(99,102,241,.22);
}


/* =========================================================
   THINK BUTTON
   ========================================================= */

.think-button button {

    min-height:
        47px !important;

    border-radius:
        14px !important;

    background:

        linear-gradient(
            135deg,
            rgba(99,102,241,.15),
            rgba(59,130,246,.10)
        ) !important;

    border:
        1px solid rgba(139,92,246,.38) !important;

    color:
        #e0e7ff !important;

    font-weight:
        600 !important;
}


.think-button button:hover {

    box-shadow:
        0 0 22px rgba(139,92,246,.30);
}


/* =========================================================
   SEND BUTTON
   ========================================================= */

.send-button button {

    min-height:
        47px !important;

    border-radius:
        14px !important;

    background:

        linear-gradient(
            135deg,
            #6366f1,
            #4f46e5,
            #3b82f6
        ) !important;

    border:
        1px solid rgba(165,180,252,.55) !important;

    color:
        white !important;

    font-weight:
        700 !important;

    box-shadow:
        0 0 18px rgba(99,102,241,.22);

    transition:
        all .2s ease !important;
}


.send-button button:hover {

    transform:
        translateY(-2px);

    box-shadow:
        0 0 30px rgba(99,102,241,.45);
}


/* =========================================================
   🎙️ QUANTUM MICROPHONE
   ========================================================= */

[class*="st-key-quantum_microphone_"] {

    width:
        54px !important;

    min-width:
        54px !important;

    max-width:
        54px !important;

    display:
        flex !important;

    align-items:
        center !important;

    justify-content:
        center !important;

    overflow:
        visible !important;
}


[class*="st-key-quantum_microphone_"]
[data-testid="stAudioInput"] {

    width:
        72px !important;

    min-width:
        72px !important;

    max-width:
        72px !important;

    height:
        50px !important;

    min-height:
        50px !important;

    max-height:
        50px !important;

    padding:
        1px !important;

    margin:
        0 auto !important;

    overflow:
        visible !important;

    border-radius:
        50% !important;

    background:
        transparent !important;

    display:
        flex !important;

    align-items:
        center !important;

    justify-content:
        center !important;
}


[class*="st-key-quantum_microphone_"] button {

    width:
        46px !important;

    min-width:
        46px !important;

    max-width:
        46px !important;

    height:
        46px !important;

    min-height:
        46px !important;

    max-height:
        46px !important;

    padding:
        0 !important;

    margin:
        0 auto !important;

    border-radius:
        50% !important;

    display:
        flex !important;

    align-items:
        center !important;

    justify-content:
        center !important;

    overflow:
        hidden !important;

    background:
        linear-gradient(
            145deg,
            rgba(30,41,59,.98),
            rgba(15,23,42,.98)
        ) !important;

    border:
        1px solid rgba(148,163,184,.38) !important;

    color:
        #f8fafc !important;

    box-shadow:
        0 5px 18px rgba(0,0,0,.28),
        inset 0 1px 0 rgba(255,255,255,.06) !important;

    transition:
        transform .18s ease,
        border-color .18s ease,
        background .18s ease,
        box-shadow .18s ease !important;
}


[class*="st-key-quantum_microphone_"] button::before,
[class*="st-key-quantum_microphone_"] button::after {

    content:
        none !important;
}


[class*="st-key-quantum_microphone_"] button svg {

    width:
        20px !important;

    height:
        20px !important;

    color:
        #f8fafc !important;

    stroke:
        #f8fafc !important;

    position:
        relative !important;

    z-index:
        2 !important;

    filter:
        none !important;
}


[class*="st-key-quantum_microphone_"] button:hover {

    transform:
        translateY(-1px) scale(1.04) !important;

    background:
        linear-gradient(
            145deg,
            rgba(79,70,229,.92),
            rgba(37,99,235,.88)
        ) !important;

    border-color:
        rgba(165,180,252,.78) !important;

    box-shadow:
        0 0 0 3px rgba(99,102,241,.10),
        0 8px 24px rgba(30,64,175,.30) !important;
}


[class*="st-key-quantum_microphone_"] button:active {

    transform:
        scale(.94) !important;
}


[class*="st-key-quantum_microphone_"] audio {

    display:
        none !important;
}


/* =========================================================
   CANVAS
   ========================================================= */

.canvas-box {

    margin-top: 20px;

    padding: 25px;

    border-radius: 20px;

    border:
        1px solid rgba(99,102,241,.30);

    background:

        linear-gradient(
            135deg,
            rgba(15,23,42,.92),
            rgba(10,15,35,.92)
        );

    box-shadow:
        0 0 35px rgba(99,102,241,.10);
}


/* =========================================================
   LOGIN PAGE
   ========================================================= */

.login-page {

    min-height:
        82vh;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    padding:
        30px 20px;
}


.login-card {

    width:
        100%;

    max-width:
        500px;

    margin:
        auto;

    padding:
        40px;

    border-radius:
        28px;

    background:

        linear-gradient(
            145deg,
            rgba(15,23,42,.97),
            rgba(7,12,28,.97)
        );

    border:
        1px solid rgba(139,92,246,.36);

    box-shadow:

        0 0 30px rgba(99,102,241,.14),

        0 0 80px rgba(139,92,246,.08),

        inset
        0 0 30px rgba(99,102,241,.035);

    animation:
        loginAppear .6s ease-out;
}


@keyframes loginAppear {

    from {

        opacity: 0;

        transform:
            translateY(20px)
            scale(.97);
    }

    to {

        opacity: 1;

        transform:
            translateY(0)
            scale(1);
    }
}


.login-logo {

    text-align:
        center;

    font-size:
        72px;

    line-height:
        1;

    margin-bottom:
        15px;

    filter:
        drop-shadow(0 0 8px rgba(167,139,250,.9))
        drop-shadow(0 0 30px rgba(99,102,241,.7));

    animation:
        loginPulse 3s ease-in-out infinite;
}


@keyframes loginPulse {

    0%,100% {

        transform:
            scale(1);
    }

    50% {

        transform:
            scale(1.08);
    }
}


.login-title {

    text-align:
        center;

    font-family:
        "Space Grotesk",
        sans-serif;

    font-size:
        30px;

    font-weight:
        700;

    letter-spacing:
        3px;

    color:
        #e0e7ff;
}


.login-subtitle {

    text-align:
        center;

    color:
        #94a3b8;

    font-size:
        13px;

    line-height:
        1.7;

    margin-top:
        8px;
}


.login-divider {

    width:
        100%;

    height:
        1px;

    margin:
        25px 0;

    background:

        linear-gradient(
            90deg,
            transparent,
            rgba(139,92,246,.55),
            transparent
        );
}


.login-label {

    color:
        #cbd5e1;

    font-size:
        13px;

    font-weight:
        600;

    margin-bottom:
        7px;
}


/* =========================================================
   LOGIN INPUT
   ========================================================= */

.login-input input {

    background:
        rgba(2,6,23,.75) !important;

    border:
        1px solid rgba(139,92,246,.28) !important;

    border-radius:
        14px !important;

    color:
        #f8fafc !important;

    min-height:
        49px !important;
}


.login-input input:focus {

    border-color:
        rgba(139,92,246,.85) !important;

    box-shadow:
        0 0 0 2px rgba(139,92,246,.08),
        0 0 25px rgba(99,102,241,.18) !important;
}


.login-button button {

    min-height:
        49px !important;

    border-radius:
        14px !important;

    background:

        linear-gradient(
            135deg,
            #6366f1,
            #4f46e5,
            #3b82f6
        ) !important;

    border:
        1px solid rgba(165,180,252,.55) !important;

    color:
        white !important;

    font-weight:
        700 !important;

    box-shadow:
        0 0 22px rgba(99,102,241,.25);

    transition:
        all .2s ease;
}


.login-button button:hover {

    transform:
        translateY(-2px);

    box-shadow:
        0 0 35px rgba(99,102,241,.45);
}


.login-status {

    text-align:
        center;

    color:
        #64748b;

    font-size:
        11px;

    margin-top:
        16px;
}


/* =========================================================
   POPUP
   ========================================================= */

.tool-card {

    padding:
        14px;

    border-radius:
        14px;

    border:
        1px solid rgba(139,92,246,.20);

    background:
        rgba(10,15,35,.85);

    margin-bottom:
        10px;
}


/* =========================================================
   HIDE STREAMLIT FOOTER
   ========================================================= */

footer {

    visibility:
        hidden;
}


/* =========================================================
   NATIVE STREAMLIT OVERRIDES
   ========================================================= */

[data-testid="column"]:has(.st-key-center_login) {

    padding:
        34px 42px 28px 42px;

    border-radius:
        28px;

    background:
        linear-gradient(
            145deg,
            rgba(15,23,42,.97),
            rgba(7,12,28,.97)
        );

    border:
        1px solid rgba(139,92,246,.36);

    box-shadow:
        0 0 30px rgba(99,102,241,.14),
        0 0 80px rgba(139,92,246,.08),
        inset 0 0 30px rgba(99,102,241,.035);
}


.st-key-center_login button {

    min-height:
        49px !important;

    border-radius:
        14px !important;

    background:
        linear-gradient(
            135deg,
            #6366f1,
            #4f46e5,
            #3b82f6
        ) !important;

    border:
        1px solid rgba(165,180,252,.55) !important;

    color:
        white !important;

    font-weight:
        700 !important;

    box-shadow:
        0 0 22px rgba(99,102,241,.25);
}


.st-key-login_email input {

    background:
        rgba(2,6,23,.75) !important;

    border:
        1px solid rgba(139,92,246,.28) !important;

    border-radius:
        14px !important;

    min-height:
        49px !important;
}


div[data-testid="stHorizontalBlock"]:has([class*="st-key-custom_prompt_"]) {

    margin-top:
        6px;

    padding:
        8px;

    border-radius:
        22px;

    border:
        1px solid rgba(139,92,246,.30);

    background:
        linear-gradient(
            135deg,
            rgba(15,23,42,.96),
            rgba(7,12,28,.96)
        );

    box-shadow:
        0 0 30px rgba(99,102,241,.10);
}


[class*="st-key-custom_prompt_"] input {

    min-height:
        47px !important;

    border-radius:
        14px !important;

    background:
        rgba(15,23,42,.60) !important;
}


[class*="st-key-custom_prompt_"] input:focus {

    border-color:
        rgba(139,92,246,.65) !important;

    box-shadow:
        0 0 0 2px rgba(139,92,246,.07),
        0 0 22px rgba(99,102,241,.18) !important;
}


/* Hide form submit control used only for keyboard Enter. */

[class*="st-key-enter_submit_"] {

    display:
        none !important;
}


.st-key-think_button button {

    min-height:
        47px !important;

    border-radius:
        14px !important;

    background:
        linear-gradient(
            135deg,
            rgba(99,102,241,.15),
            rgba(59,130,246,.10)
        ) !important;

    border:
        1px solid rgba(139,92,246,.38) !important;
}


.st-key-send_button button {

    width:
        48px !important;

    height:
        48px !important;

    min-height:
        48px !important;

    padding:
        0 !important;

    border-radius:
        50% !important;

    background:
        linear-gradient(
            145deg,
            #4d8dff,
            #575eff
        ) !important;

    border:
        1px solid rgba(150,190,255,.65) !important;

    color:
        white !important;

    font-size:
        25px !important;

    font-weight:
        900 !important;

    box-shadow:
        0 0 26px rgba(70,110,255,.40) !important;
}


.st-key-send_button button:hover {

    transform:
        translateY(-2px)
        scale(1.05) !important;

    box-shadow:
        0 0 38px rgba(70,120,255,.68) !important;
}


/* =========================================================
   RENAME CHAT UI
   ========================================================= */

[class*="st-key-save_name_"] button {

    min-height:
        38px !important;

    border-radius:
        10px !important;

    background:
        linear-gradient(
            135deg,
            rgba(99,102,241,.30),
            rgba(59,130,246,.20)
        ) !important;

    border:
        1px solid rgba(129,140,248,.50) !important;

    color:
        #eef2ff !important;

    font-weight:
        600 !important;
}


[class*="st-key-cancel_name_"] button {

    min-height:
        38px !important;

    border-radius:
        10px !important;

    background:
        rgba(15,23,42,.80) !important;

    border:
        1px solid rgba(100,116,139,.35) !important;

    color:
        #cbd5e1 !important;
}


[class*="st-key-title_input_"] input {

    min-height:
        40px !important;

    border-radius:
        10px !important;

    background:
        rgba(2,6,23,.75) !important;

    border:
        1px solid rgba(139,92,246,.35) !important;

    color:
        #f8fafc !important;
}


[class*="st-key-title_input_"] input:focus {

    border-color:
        rgba(139,92,246,.75) !important;

    box-shadow:
        0 0 0 2px rgba(139,92,246,.08),
        0 0 18px rgba(99,102,241,.18) !important;
}


/* =========================================================
   MICROPHONE COLUMN FINAL OVERRIDE
   ========================================================= */

[class*="st-key-quantum_microphone_"] {

    width:
        54px !important;

    min-width:
        54px !important;

    max-width:
        54px !important;

    overflow:
        visible !important;

    display:
        flex !important;

    align-items:
        center !important;

    justify-content:
        center !important;
}


/* =========================================================
   RECORDING ACTIONS
   ========================================================= */

[class*="st-key-download_wav_"] button,
[class*="st-key-clear_recording_"] button {

    min-height: 34px !important;

    height: 34px !important;

    padding: 0 4px !important;

    border-radius: 9px !important;

    font-size: 11px !important;

    font-weight: 700 !important;

    white-space: nowrap !important;
}


[class*="st-key-download_wav_"] button {

    background:
        rgba(15,23,42,.82) !important;

    border:
        1px solid rgba(96,165,250,.45) !important;
}


[class*="st-key-clear_recording_"] button {

    background:
        rgba(127,29,29,.30) !important;

    border:
        1px solid rgba(248,113,113,.42) !important;
}


[class*="st-key-download_wav_"] button:hover,
[class*="st-key-clear_recording_"] button:hover {

    transform:
        translateY(-1px) !important;
}


[class*="st-key-quantum_microphone_"] [data-testid="stAudioInput"],
[class*="st-key-quantum_microphone_"] [data-testid="stAudioInput"] > div {

    overflow:
        visible !important;
}


/* =========================================================
   CANVAS / NOTES ACTION BUTTONS
   ========================================================= */

[class*="st-key-save_canvas_"] button,
[class*="st-key-clear_canvas_"] button,
[class*="st-key-save_notes_"] button,
[class*="st-key-clear_notes_"] button {

    min-height: 40px !important;

    border-radius: 10px !important;

    font-weight: 700 !important;
}


[class*="st-key-save_canvas_"] button,
[class*="st-key-save_notes_"] button {

    background:
        linear-gradient(
            135deg,
            rgba(99,102,241,.30),
            rgba(59,130,246,.20)
        ) !important;

    border:
        1px solid rgba(129,140,248,.50) !important;

    color:
        #eef2ff !important;
}


[class*="st-key-clear_canvas_"] button,
[class*="st-key-clear_notes_"] button {

    background:
        rgba(127,29,29,.30) !important;

    border:
        1px solid rgba(248,113,113,.42) !important;

    color:
        #fecaca !important;
}


/* =========================================================
   DRIVE BUTTON
   ========================================================= */

.drive-insert-button a {

    width: 100% !important;

    min-height: 42px !important;

    border-radius: 10px !important;

    background:
        linear-gradient(
            135deg,
            rgba(99,102,241,.24),
            rgba(59,130,246,.18)
        ) !important;

    border:
        1px solid rgba(129,140,248,.48) !important;

    color:
        #eef2ff !important;

    font-weight:
        700 !important;

    text-decoration:
        none !important;

    display:
        flex !important;

    align-items:
        center !important;

    justify-content:
        center !important;
}


/* =========================================================
   THINK RESULT
   ========================================================= */

.think-active {

    padding:
        10px 14px;

    border-radius:
        12px;

    border:
        1px solid rgba(139,92,246,.25);

    background:
        rgba(99,102,241,.06);

    color:
        #c7d2fe;

    font-size:
        12px;

    margin:
        8px 0 12px 0;
}

</style>

<div class="quantum-space"></div>
""",
    unsafe_allow_html=True,
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def refresh_sessions():

    """
    Refresh chat sessions only when actually needed.
    Avoid calling this unnecessarily on every rerun.
    """

    if st.session_state.user_id:

        try:

            sessions = get_user_sessions(
                st.session_state.user_id
            )

            if sessions is None:
                sessions = []

            st.session_state.sessions = sessions

        except Exception:

            st.session_state.sessions = []


def start_new_chat():

    if not st.session_state.logged_in:
        return

    try:

        new_session_id = create_chat_session(
            st.session_state.user_id,
            "New Chat"
        )

        st.session_state.session_id = new_session_id

        st.session_state.messages = []

        st.session_state.rename_session_id = None

        refresh_sessions()

    except Exception as e:

        st.error(
            f"Could not create chat: {e}"
        )


def clear_current_chat():

    st.session_state.messages = []

    st.session_state.last_processed_prompt = ""


def logout_user():

    st.session_state.logged_in = False

    st.session_state.user_email = ""

    st.session_state.user_id = None

    st.session_state.session_id = None

    st.session_state.messages = []

    st.session_state.sessions = []

    st.session_state.uploaded_files = []

    st.session_state.drive_links = []

    st.session_state.rename_session_id = None

    st.session_state.processed_audio_hash = None

    st.session_state.recorded_audio_bytes = None

    st.session_state.recording_filename = "quantum_recording.wav"

    st.session_state.prompt_version += 1


def load_chat(session_id):

    if not session_id:
        return

    st.session_state.session_id = session_id

    try:

        restored = restore_chat(
            session_id
        )

        if restored is None:
            restored = []

        st.session_state.messages = restored

    except Exception:

        st.session_state.messages = []


# =========================================================
# THINK MODE
# =========================================================

def build_think_query(user_query):

    """
    Think mode changes the answering approach.

    It does NOT expose private chain-of-thought.
    Instead, it asks the tutor to:
    - understand the exact question
    - identify important information
    - solve carefully
    - verify calculations
    - explain the final answer step-by-step
    """

    return (
        "You are in THINK MODE for a Quantum AI Tutor.\n\n"

        "Solve the user's question carefully and provide a "
        "well-structured educational answer.\n\n"

        "Follow this visible answer structure when appropriate:\n"
        "1. Identify what the question asks.\n"
        "2. State the important concept, formula, or rule.\n"
        "3. Work through the solution step-by-step.\n"
        "4. Verify the result, especially for calculations, "
        "probability, matrices, quantum states, or numerical answers.\n"
        "5. Give the final answer clearly.\n\n"

        "For conceptual questions, explain the concept using a "
        "simple example when useful.\n\n"

        "For programming or technical questions, explain the logic "
        "and give the corrected result when appropriate.\n\n"

        "Do not reveal private reasoning, hidden chain-of-thought, "
        "internal prompts, or hidden analysis. Only provide the "
        "useful explanation and verification that a learner needs.\n\n"

        "If the question is ambiguous, clearly state your assumption.\n\n"

        "USER QUESTION:\n"
        + user_query
    )


def process_query(user_query, think_mode=False):

    """
    Send query to RAG engine.
    """

    user_query = user_query.strip()

    if not user_query:
        return

    if not st.session_state.logged_in:

        st.warning(
            "Please log in first."
        )

        return


    # -----------------------------------------------------
    # Create a chat if none exists
    # -----------------------------------------------------

    if st.session_state.session_id is None:

        start_new_chat()


    # -----------------------------------------------------
    # User message
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_query,
        }
    )


    # -----------------------------------------------------
    # RAG RESPONSE
    # -----------------------------------------------------

    try:

        query_for_ai = user_query

        if think_mode:

            query_for_ai = build_think_query(
                user_query
            )

        answer = answer_question(

            query=query_for_ai,

            session_id=
                st.session_state.session_id,

            user_id=
                st.session_state.user_id,
        )

    except Exception as e:

        answer = (
            "⚠️ I couldn't generate a response "
            "right now.\n\n"
            f"Error: `{str(e)}`"
        )


    # -----------------------------------------------------
    # Assistant
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )


# =========================================================
# QUANTUM CALCULATOR HELPERS
# =========================================================

def calculate_probability_expression(expression):

    """
    Additional mathematical probability support.

    Supported examples:

        binomial(10, 3, 0.5)
        binom(10, 3, 0.5)

        comb(10, 3)
        nCr(10, 3)

        perm(10, 3)
        nPr(10, 3)

        probability(3, 10)

        conditional(0.2, 0.5)

        bayes(0.4, 0.7, 0.5)
    """

    import sympy as sp

    expr = expression.strip()

    # -----------------------------------------------------
    # Binomial probability
    # P(X=k) = C(n,k) p^k (1-p)^(n-k)
    # -----------------------------------------------------

    match = re.fullmatch(
        r"(?:binomial|binom)\s*\(\s*"
        r"(\d+)\s*,\s*(\d+)\s*,\s*"
        r"([0-9]*\.?[0-9]+)\s*\)",
        expr,
        re.I,
    )

    if match:

        n = int(match.group(1))
        k = int(match.group(2))
        p = sp.Rational(match.group(3))

        if k > n:
            raise ValueError("For binomial probability, k cannot be greater than n.")

        if not 0 <= float(p) <= 1:
            raise ValueError("Probability p must be between 0 and 1.")

        result = sp.simplify(
            sp.binomial(n, k)
            * p ** k
            * (1 - p) ** (n - k)
        )

        return (
            "Binomial probability",
            result,
            f"P(X={k}) = C({n},{k}) × p^{k} × (1-p)^({n-k})"
        )


    # -----------------------------------------------------
    # Combination
    # -----------------------------------------------------

    match = re.fullmatch(
        r"(?:comb|ncr)\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)",
        expr,
        re.I,
    )

    if match:

        n = int(match.group(1))
        r = int(match.group(2))

        if r > n:
            raise ValueError("r cannot be greater than n.")

        result = sp.binomial(n, r)

        return (
            "Combination",
            result,
            f"C({n},{r})"
        )


    # -----------------------------------------------------
    # Permutation
    # -----------------------------------------------------

    match = re.fullmatch(
        r"(?:perm|npr)\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)",
        expr,
        re.I,
    )

    if match:

        n = int(match.group(1))
        r = int(match.group(2))

        if r > n:
            raise ValueError("r cannot be greater than n.")

        result = sp.factorial(n) / sp.factorial(n - r)

        return (
            "Permutation",
            sp.simplify(result),
            f"P({n},{r})"
        )


    # -----------------------------------------------------
    # Simple probability
    # probability(favorable,total)
    # -----------------------------------------------------

    match = re.fullmatch(
        r"probability\s*\(\s*"
        r"([0-9.]+)\s*,\s*([0-9.]+)\s*\)",
        expr,
        re.I,
    )

    if match:

        favorable = sp.Rational(match.group(1))
        total = sp.Rational(match.group(2))

        if total == 0:
            raise ValueError("Total outcomes cannot be zero.")

        result = sp.simplify(
            favorable / total
        )

        return (
            "Simple probability",
            result,
            "P(E) = favorable outcomes / total outcomes"
        )


    # -----------------------------------------------------
    # Conditional probability
    # conditional(joint,marginal)
    #
    # P(A|B) = P(A and B) / P(B)
    # -----------------------------------------------------

    match = re.fullmatch(
        r"conditional\s*\(\s*"
        r"([0-9.]+)\s*,\s*([0-9.]+)\s*\)",
        expr,
        re.I,
    )

    if match:

        joint = sp.Rational(match.group(1))
        marginal = sp.Rational(match.group(2))

        if marginal == 0:
            raise ValueError("The marginal probability cannot be zero.")

        result = sp.simplify(
            joint / marginal
        )

        return (
            "Conditional probability",
            result,
            "P(A|B) = P(A ∩ B) / P(B)"
        )


    # -----------------------------------------------------
    # Bayes theorem
    # bayes(prior,likelihood,evidence)
    #
    # P(A|B) = P(B|A)P(A) / P(B)
    # -----------------------------------------------------

    match = re.fullmatch(
        r"bayes\s*\(\s*"
        r"([0-9.]+)\s*,\s*"
        r"([0-9.]+)\s*,\s*"
        r"([0-9.]+)\s*\)",
        expr,
        re.I,
    )

    if match:

        prior = sp.Rational(match.group(1))
        likelihood = sp.Rational(match.group(2))
        evidence = sp.Rational(match.group(3))

        if evidence == 0:
            raise ValueError("Evidence probability cannot be zero.")

        result = sp.simplify(
            prior * likelihood / evidence
        )

        return (
            "Bayes probability",
            result,
            "P(A|B) = P(B|A) × P(A) / P(B)"
        )


    return None


# =========================================================
# CENTERED LOGIN SCREEN
# =========================================================

if not st.session_state.logged_in:

    st.markdown(
        """
        <style>

        section[data-testid="stSidebar"] {
            display:none !important;
        }

        [data-testid="collapsedControl"] {
            display:none !important;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    st.write("")

    left_col, center_col, right_col = st.columns(
        [1,2,1]
    )

    with center_col:

        st.markdown("## ⚛️")

        st.markdown("# QUANTUM LAB")

        st.caption(
            "AI-powered learning for Quantum Computing & Advanced Physics"
        )

        st.divider()

        st.markdown("### 🔐 Account Login")

        email = st.text_input(
            "Email",
            placeholder="student@example.com",
            label_visibility="collapsed",
            key="login_email",
        )

        login_clicked = st.button(
            "🔑  Enter Quantum Lab",
            use_container_width=True,
            key="center_login",
        )

        st.caption(
            "✦ Your AI learning workspace awaits ✦"
        )

        if login_clicked:

            clean_email = email.strip()

            if not clean_email:

                st.warning(
                    "Please enter your email address."
                )

            else:

                try:

                    user_id = get_or_create_user(
                        clean_email
                    )

                    st.session_state.user_email = clean_email

                    st.session_state.user_id = user_id

                    st.session_state.logged_in = True

                    st.session_state.session_id = None

                    st.session_state.messages = []

                    st.session_state.sessions = []

                    st.session_state.prompt_version += 1

                    refresh_sessions()

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Login failed: {e}"
                    )

    st.stop()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## ⚛️ QUANTUM LAB")

    st.caption(
        "AI-powered learning workspace"
    )

    st.markdown("---")

    st.subheader("🔐 Account")

    st.info(
        f"👤 Logged in as\n\n**{st.session_state.user_email}**"
    )

    if st.button(
        "🚪 Log Out",
        use_container_width=True,
        key="sidebar_logout",
    ):

        logout_user()

        st.rerun()


    st.markdown("---")

    st.subheader("💬 Chats")

    if st.button(
        "➕ New Chat",
        use_container_width=True,
        key="sidebar_new_chat",
    ):

        start_new_chat()

        st.rerun()


    st.caption("CHAT HISTORY")


    if not st.session_state.sessions:

        st.caption(
            "No conversations yet."
        )

    else:

        for chat in st.session_state.sessions:

            session_id = (
                chat.get("session_id")
                or chat.get("id")
            )

            if not session_id:
                continue


            title = (
                chat.get(
                    "title",
                    "Untitled Chat"
                )
                or "Untitled Chat"
            )

            title = str(title)


            selected = (
                session_id
                == st.session_state.session_id
            )

            prefix = (
                "🟣"
                if selected
                else "💬"
            )


            col1, col2, col3 = st.columns(
                [0.62,0.19,0.19],
                gap="small"
            )


            with col1:

                short_title = title

                if len(short_title) > 22:

                    short_title = (
                        short_title[:22]
                        + "..."
                    )

                if st.button(
                    f"{prefix} {short_title}",
                    key=f"chat_{session_id}",
                    use_container_width=True,
                ):

                    load_chat(
                        session_id
                    )

                    st.rerun()


            with col2:

                rename_clicked = st.button(
                    "✏️",
                    key=f"rename_{session_id}",
                    help="Rename chat",
                    use_container_width=True,
                )

                if rename_clicked:

                    st.session_state.rename_session_id = (
                        session_id
                    )

                    st.rerun()


            with col3:

                delete_clicked = st.button(
                    "🗑️",
                    key=f"delete_{session_id}",
                    help="Delete chat",
                    use_container_width=True,
                )

                if delete_clicked:

                    if not session_id:

                        st.error(
                            "Unable to delete this chat because "
                            "the chat ID is missing."
                        )

                    else:

                        try:

                            delete_chat(
                                user_id=st.session_state.user_id,
                                session_id=session_id,
                            )


                            if (
                                st.session_state.session_id
                                == session_id
                            ):

                                st.session_state.session_id = None

                                st.session_state.messages = []


                            if (
                                st.session_state.rename_session_id
                                == session_id
                            ):

                                st.session_state.rename_session_id = None


                            refresh_sessions()

                            st.rerun()


                        except Exception as e:

                            st.error(
                                f"Delete failed: {e}"
                            )


            if (
                st.session_state.rename_session_id
                == session_id
            ):

                st.markdown(
                    "<div style='height:4px'></div>",
                    unsafe_allow_html=True,
                )

                new_title = st.text_input(
                    "New chat name",
                    value=title,
                    key=f"title_input_{session_id}",
                    label_visibility="collapsed",
                    placeholder="Enter new chat name",
                )


                rename_col1, rename_col2 = st.columns(
                    [1, 1],
                    gap="small"
                )


                with rename_col1:

                    if st.button(
                        "✓ Save",
                        key=f"save_name_{session_id}",
                        use_container_width=True,
                    ):

                        clean_title = (
                            new_title.strip()
                        )


                        if not clean_title:

                            st.warning(
                                "Chat name cannot be empty."
                            )

                        elif len(clean_title) > 80:

                            st.warning(
                                "Chat name is too long. "
                                "Please keep it under 80 characters."
                            )

                        else:

                            try:

                                rename_chat(
                                    user_id=st.session_state.user_id,
                                    session_id=session_id,
                                    new_title=clean_title,
                                )

                                st.session_state.rename_session_id = None

                                refresh_sessions()

                                st.rerun()


                            except Exception as e:

                                st.error(
                                    f"Rename failed: {e}"
                                )


                with rename_col2:

                    if st.button(
                        "✕ Cancel",
                        key=f"cancel_name_{session_id}",
                        use_container_width=True,
                    ):

                        st.session_state.rename_session_id = None

                        st.rerun()


    st.markdown("---")


    if st.button(
        "🧹 Clear Conversation",
        use_container_width=True,
        key="sidebar_clear_chat",
    ):

        clear_current_chat()

        st.rerun()


    if st.session_state.session_id:

        st.markdown("---")

        st.caption(
            "Current Chat ID:"
        )

        st.code(
            str(
                st.session_state.session_id
            ),
            language=None
        )


# =========================================================
# MAIN HEADER
# =========================================================

st.markdown(
    "# ⚛️ QUANTUM LAB"
)

st.caption(
    "Interactive AI Tutor for Quantum Computing & Advanced Physics"
)

st.markdown(
    "**● AI TUTOR ONLINE**"
)

st.divider()


# =========================================================
# CURRENT CHAT TITLE
# =========================================================

if st.session_state.session_id:

    current_title = "New Chat"

    for chat in st.session_state.sessions:

        sid = (
            chat.get("session_id")
            or chat.get("id")
        )

        if sid == st.session_state.session_id:

            current_title = (
                chat.get(
                    "title",
                    "New Chat"
                )
            )

            break


    st.caption(
        f"💬 {current_title}"
    )


# =========================================================
# DISPLAY CHAT
# =========================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# =========================================================
# CANVAS
# =========================================================

if st.session_state.show_canvas:

    st.subheader(
        "🎨 Canvas Workbench"
    )

    st.caption(
        "Create quantum notes, equations, diagrams and ideas."
    )

    canvas_text = st.text_area(
        "Canvas",
        value=st.session_state.canvas_saved_text,
        placeholder=
            "Write your quantum notes, equations or ideas...",
        height=220,
        key=f"canvas_text_{st.session_state.canvas_version}",
    )

    canvas_col1, canvas_col2, canvas_col3 = st.columns(
        [1, 1, 1]
    )


    # =====================================================
    # SAVE CANVAS
    # =====================================================

    with canvas_col1:

        if st.button(
            "💾 Save Canvas",
            use_container_width=True,
            key=f"save_canvas_{st.session_state.canvas_version}",
        ):

            st.session_state.canvas_saved_text = canvas_text

            st.success(
                "Canvas saved for this session."
            )


    # =====================================================
    # CLEAR CANVAS
    # =====================================================

    with canvas_col2:

        if st.button(
            "🧹 Clear Canvas",
            use_container_width=True,
            key=f"clear_canvas_{st.session_state.canvas_version}",
        ):

            st.session_state.canvas_saved_text = ""

            st.session_state.canvas_text = ""

            st.session_state.canvas_version += 1

            st.rerun()


    # =====================================================
    # CLOSE CANVAS
    # =====================================================

    with canvas_col3:

        if st.button(
            "✖ Close Canvas",
            use_container_width=True,
            key="close_canvas",
        ):

            st.session_state.show_canvas = False

            st.rerun()


# =========================================================
# NOTES
# =========================================================

if st.session_state.show_notes:

    st.subheader(
        "📝 Quantum Notes"
    )

    st.caption(
        "Write your important concepts here..."
    )

    notes_text = st.text_area(
        "Notes",
        value=st.session_state.notes_saved_text,
        placeholder=
            "Write your important concepts here...",
        height=200,
        key=f"notes_text_{st.session_state.notes_version}",
    )


    notes_col1, notes_col2 = st.columns(
        [1, 1]
    )


    # =====================================================
    # SAVE NOTES
    # =====================================================

    with notes_col1:

        if st.button(
            "💾 Save Notes",
            use_container_width=True,
            key=f"save_notes_{st.session_state.notes_version}",
        ):

            st.session_state.notes_saved_text = notes_text

            st.success(
                "Quantum notes saved for this session."
            )


    # =====================================================
    # CLEAR NOTES
    # =====================================================

    with notes_col2:

        if st.button(
            "🧹 Clear Notes",
            use_container_width=True,
            key=f"clear_notes_{st.session_state.notes_version}",
        ):

            st.session_state.notes_saved_text = ""

            st.session_state.notes_text = ""

            st.session_state.notes_version += 1

            st.rerun()


# =========================================================
# QUANTUM CALCULATOR
# =========================================================

if st.session_state.show_calculator:

    st.subheader(
        "🧮 Quantum Calculator"
    )

    st.caption(
        "Solve symbolic, complex, matrix, probability and quantum-state expressions."
    )

    calc_expression = st.text_input(
        "Expression",
        placeholder=(
            "Examples: |1/sqrt(2)|^2  •  P(X=2)  •  det([[0,1],[1,0]])"
        ),
        key="calculator_expression",
    )

    calc_col1, calc_col2 = st.columns([0.82, 0.18], gap="small")


    with calc_col1:

        if st.button(
            "⚡ Calculate",
            use_container_width=True,
            key="calculate_button",
        ):

            try:

                import sympy as sp

                expr = calc_expression.strip()

                if not expr:

                    st.warning(
                        "Please enter an expression."
                    )

                else:

                    # =================================================
                    # ADDITIONAL MATHEMATICAL PROBABILITY OPERATIONS
                    # =================================================

                    probability_result = (
                        calculate_probability_expression(
                            expr
                        )
                    )


                    if probability_result:

                        title, result, formula = (
                            probability_result
                        )

                        st.success(
                            f"{title}: {result}"
                        )

                        st.markdown(
                            f"**Formula:** `{formula}`"
                        )

                        st.write(
                            f"Decimal: {sp.N(result, 12)}"
                        )

                        if result.is_real:

                            decimal_value = float(
                                sp.N(result)
                            )

                            if 0 <= decimal_value <= 1:

                                st.write(
                                    f"Percentage: "
                                    f"{decimal_value * 100:.4f}%"
                                )


                    else:

                        # -------------------------------------------------
                        # Common notation normalisation.
                        # -------------------------------------------------

                        cleaned = (
                            expr.replace("√", "sqrt")
                            .replace("π", "pi")
                            .replace("−", "-")
                            .replace("×", "*")
                            .replace("·", "*")
                            .replace("⟩", ">")
                            .replace("⟨", "<")
                            .replace("^", "**")
                        )


                        # -------------------------------------------------
                        # Quantum ket/state expressions
                        # -------------------------------------------------

                        ket_pattern = re.compile(
                            r"(?P<coef>[+\-]?\s*(?:\([^()]*\)|[^+\-]*?))\s*\|(?P<ket>[01]+)>"
                        )

                        matches = list(
                            ket_pattern.finditer(cleaned)
                        )


                        if matches:

                            basis = {}

                            for m in matches:

                                coef_text = (
                                    m.group("coef")
                                    .strip()
                                    .replace(" ", "")
                                )

                                if coef_text in ("", "+"):

                                    coef_text = "1"

                                elif coef_text == "-":

                                    coef_text = "-1"


                                coef = sp.sympify(
                                    coef_text,
                                    locals={
                                        "sqrt": sp.sqrt,
                                        "I": sp.I,
                                        "i": sp.I,
                                        "pi": sp.pi
                                    }
                                )

                                ket = m.group("ket")

                                basis[ket] = sp.simplify(
                                    basis.get(ket, 0)
                                    + coef
                                )


                            parts = []

                            total = sp.S(0)


                            for ket, coef in sorted(
                                basis.items()
                            ):

                                if coef == 0:
                                    continue

                                prob = sp.simplify(
                                    sp.Abs(coef) ** 2
                                )

                                total += prob


                                if coef == 1:

                                    parts.append(
                                        f"|{ket}⟩"
                                    )

                                elif coef == -1:

                                    parts.append(
                                        f"-|{ket}⟩"
                                    )

                                else:

                                    parts.append(
                                        f"({coef})|{ket}⟩"
                                    )


                            st.success(
                                "Quantum state solved"
                            )

                            st.markdown(
                                "**State:** "
                                + " + ".join(parts)
                                .replace("+ -", "- ")
                            )

                            st.markdown(
                                "**Measurement probabilities:**"
                            )


                            for ket, coef in sorted(
                                basis.items()
                            ):

                                prob = sp.simplify(
                                    sp.Abs(coef) ** 2
                                )

                                percentage = (
                                    float(
                                        sp.N(prob)
                                    ) * 100
                                )

                                st.write(
                                    f"P(|{ket}⟩) = "
                                    f"{prob}  "
                                    f"({percentage:.4f}%)"
                                )


                            st.write(
                                "**Total probability:** "
                                f"{sp.simplify(total)}"
                            )


                            if sp.simplify(total - 1) != 0:

                                st.info(
                                    "The amplitudes do not form a "
                                    "normalized quantum state. "
                                    "The values above are |amplitude|² "
                                    "before normalization."
                                )


                        # -------------------------------------------------
                        # Absolute-value probability:
                        # |amplitude|²
                        # -------------------------------------------------

                        else:

                            prob_match = re.fullmatch(
                                r"\|(.+)\|\s*\*\*\s*2",
                                cleaned
                            )


                            if prob_match:

                                amp = sp.sympify(
                                    prob_match.group(1),
                                    locals={
                                        "sqrt": sp.sqrt,
                                        "I": sp.I,
                                        "i": sp.I,
                                        "pi": sp.pi
                                    }
                                )

                                prob = sp.simplify(
                                    sp.Abs(amp) ** 2
                                )

                                st.success(
                                    f"Quantum probability = {prob}"
                                )

                                st.write(
                                    f"Percentage = "
                                    f"{float(sp.N(prob))*100:.4f}%"
                                )


                            # -------------------------------------------------
                            # Mathematical probability shortcuts
                            # -------------------------------------------------

                            elif re.search(
                                r"\b(?:P\s*\(|probability|conditional|bayes)\b",
                                cleaned,
                                re.I
                            ):

                                try:

                                    result = sp.sympify(
                                        cleaned,
                                        locals={
                                            "sqrt": sp.sqrt,
                                            "I": sp.I,
                                            "i": sp.I,
                                            "pi": sp.pi,
                                            "binomial": sp.binomial,
                                            "comb": sp.binomial,
                                            "factorial": sp.factorial,
                                        }
                                    )

                                    result = sp.simplify(
                                        result
                                    )

                                    st.success(
                                        f"Probability result: {result}"
                                    )

                                    st.write(
                                        f"Decimal: "
                                        f"{sp.N(result, 12)}"
                                    )

                                except Exception:

                                    st.info(
                                        "For probability calculations, "
                                        "use formats such as "
                                        "`probability(3,10)`, "
                                        "`conditional(0.2,0.5)`, "
                                        "`bayes(0.4,0.7,0.5)`, or "
                                        "`binomial(10,3,0.5)`."
                                    )


                            else:

                                result = sp.sympify(
                                    cleaned,
                                    locals={
                                        "sqrt": sp.sqrt,
                                        "I": sp.I,
                                        "i": sp.I,
                                        "pi": sp.pi,
                                        "sin": sp.sin,
                                        "cos": sp.cos,
                                        "tan": sp.tan,
                                        "log": sp.log,
                                        "exp": sp.exp,
                                        "abs": sp.Abs,

                                        "det":
                                            lambda x:
                                                sp.Matrix(x).det(),

                                        "trace":
                                            lambda x:
                                                sp.Matrix(x).trace(),

                                        "simplify":
                                            sp.simplify,

                                        "factor":
                                            sp.factor,

                                        "expand":
                                            sp.expand,

                                        "Matrix":
                                            sp.Matrix,
                                    }
                                )


                                simplified = sp.simplify(
                                    result
                                )


                                st.success(
                                    f"Result: {simplified}"
                                )

                                st.write(
                                    f"Decimal: "
                                    f"{sp.N(simplified, 12)}"
                                )


            except Exception as e:

                st.error(
                    f"Could not solve the expression: {e}"
                )


    with calc_col2:

        if st.button(
            "✖ Close",
            use_container_width=True,
            key="close_calculator",
        ):

            st.session_state.show_calculator = False

            st.rerun()


# =========================================================
# PROMPT AREA
# =========================================================

st.caption(
    "ASK YOUR QUANTUM AI TUTOR"
)


# =========================================================
# PROMPT ROW
# =========================================================

prompt_col1, prompt_col2, prompt_col3, prompt_col4, prompt_col5 = st.columns(
    [0.07, 0.52, 0.14, 0.13, 0.07],

    gap="small",

    vertical_alignment="center",
)


# =========================================================
# PLUS POPUP
# =========================================================

with prompt_col1:

    with st.popover(
        "＋",
        use_container_width=True,
    ):

        st.markdown(
            "### Tools & Attachments"
        )


        tab1, tab2, tab3 = st.tabs(
            [
                "📁 Photos & Files",
                "☁️ Drive",
                "🛠️ More Tools",
            ]
        )


        # =================================================
        # FILES
        # =================================================

        with tab1:

            uploaded = st.file_uploader(

                "Upload photos or files",

                type=[
                    "png",
                    "jpg",
                    "jpeg",
                    "webp",
                    "pdf",
                    "txt",
                    "docx",
                    "csv",
                    "xlsx",
                    "py",
                    "java",
                    "c",
                ],

                accept_multiple_files=True,

                key=
                    "quantum_attachments",

            )


            if uploaded:

                st.session_state.uploaded_files = (
                    uploaded
                )


                st.success(
                    f"{len(uploaded)} file(s) attached"
                )


                for file in uploaded:

                    st.caption(
                        f"📎 {file.name}"
                    )


        # =================================================
        # GOOGLE DRIVE
        # =================================================

        with tab2:

            st.markdown(
                "### ☁️ Google Drive"
            )

            st.caption(
                "Insert a document from your Google Drive or paste its share link."
            )


            # =================================================
            # INSERT DOCUMENT FROM MY DRIVE
            # =================================================

            st.markdown(
                "#### 📂 Insert document from My Drive"
            )

            st.markdown(
                """
                <div class="drive-insert-button">
                """,
                unsafe_allow_html=True,
            )

            st.link_button(
                "📂 Insert document from My Drive",
                "https://drive.google.com/drive/my-drive",
                use_container_width=True,
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

            st.caption(
                "Open your Drive, copy the document's share link, "
                "then paste it below."
            )


            # =================================================
            # PASTE DRIVE LINK
            # =================================================

            st.markdown(
                "#### 🔗 Paste Drive Link"
            )

            drive_url = st.text_input(

                "Drive file link",

                placeholder=
                    "Paste Google Drive link",

                key=
                    "drive_url",

            )


            if st.button(

                "Attach Drive File",

                use_container_width=True,

                key=
                    "attach_drive",

            ):

                clean_drive_url = (
                    drive_url.strip()
                )


                if clean_drive_url:

                    if (
                        clean_drive_url
                        not in st.session_state.drive_links
                    ):

                        st.session_state.drive_links.append(
                            clean_drive_url
                        )


                    st.success(
                        "Google Drive link attached."
                    )

                else:

                    st.warning(
                        "Please paste a Drive link."
                    )


        # =================================================
        # MORE TOOLS
        # =================================================

        with tab3:

            st.markdown(
                "### 🛠️ More Tools"
            )


            if st.button(

                "🎨 Canvas",

                use_container_width=True,

                key=
                    "tool_canvas",

            ):

                st.session_state.show_canvas = True

                st.rerun()


            if st.button(

                "🧮 Quantum Calculator",

                use_container_width=True,

                key=
                    "tool_calculator",

            ):

                st.session_state.show_calculator = True

                st.rerun()


            if st.button(

                "📚 Learning Mode",

                use_container_width=True,

                key=
                    "tool_learning",

            ):

                st.session_state.learning_mode = True

                st.success(
                    "Learning Mode activated!"
                )


            if st.button(

                "📝 Notes",

                use_container_width=True,

                key=
                    "tool_notes",

            ):

                st.session_state.show_notes = True

                st.rerun()


# =========================================================
# MICROPHONE PROCESSING
# =========================================================

with prompt_col4:

    audio_value = st.audio_input(
        "🎙️",
        key=f"quantum_microphone_{st.session_state.audio_version}",
        label_visibility="collapsed",
    )

    audio_has_data = (
        st.session_state.recorded_audio_bytes
        is not None
    )

    rec_col1, rec_col2 = st.columns(
        2,
        gap="small"
    )

    with rec_col1:

        if audio_has_data:

            st.download_button(
                "⬇ WAV",
                data=
                    st.session_state.recorded_audio_bytes,
                file_name=
                    st.session_state.recording_filename,
                mime="audio/wav",
                use_container_width=True,
                key=
                    f"download_wav_{st.session_state.audio_version}",
            )

    with rec_col2:

        if audio_has_data:

            if st.button(
                "✕ Clear",
                use_container_width=True,
                key=
                    f"clear_recording_{st.session_state.audio_version}",
            ):

                st.session_state.recorded_audio_bytes = None

                st.session_state.processed_audio_hash = None

                st.session_state.audio_version += 1

                st.rerun()


if audio_value is not None:

    try:

        audio_bytes = audio_value.getvalue()

        if audio_bytes:

            st.session_state.recorded_audio_bytes = (
                audio_bytes
            )

            audio_hash = hashlib.md5(
                audio_bytes
            ).hexdigest()


            if (
                st.session_state.processed_audio_hash
                != audio_hash
            ):

                st.session_state.processed_audio_hash = (
                    audio_hash
                )


                if not SPEECH_RECOGNITION_AVAILABLE:

                    st.session_state.voice_error = (
                        "SpeechRecognition is not installed. "
                        "Run: python -m pip install SpeechRecognition"
                    )

                else:

                    recognizer = sr.Recognizer()

                    audio_stream = io.BytesIO(
                        audio_bytes
                    )


                    with sr.AudioFile(
                        audio_stream
                    ) as source:

                        recorded_audio = (
                            recognizer.record(source)
                        )


                    try:

                        voice_query = (
                            recognizer.recognize_google(
                                recorded_audio,
                                language="en-IN",
                                show_all=False,
                            )
                        )


                        if (
                            voice_query
                            and voice_query.strip()
                        ):

                            st.session_state.voice_error = None

                            st.session_state.prompt_seed = (
                                voice_query.strip()
                            )

                            st.session_state.prompt_version += 1

                            st.session_state.audio_version += 1

                            st.rerun()


                    except sr.UnknownValueError:

                        st.session_state.voice_error = (
                            "I couldn't understand the recording. "
                            "Please try again."
                        )

                    except sr.RequestError as e:

                        st.session_state.voice_error = (
                            f"Speech service error: {e}"
                        )


    except Exception as e:

        st.session_state.voice_error = (
            f"Microphone transcription failed: {e}"
        )


# =========================================================
# TEXT PROMPT
# =========================================================

with prompt_col2:

    current_prompt_key = (
        f"custom_prompt_{st.session_state.prompt_version}"
    )


    with st.form(

        key=
            f"prompt_form_{st.session_state.prompt_version}",

        clear_on_submit=False,

        border=False,

    ):

        user_prompt = st.text_input(

            "Message",

            value=
                st.session_state.prompt_seed,

            placeholder=
                "Ask anything about quantum computing...",

            label_visibility="collapsed",

            key=
                current_prompt_key,

        )


        enter_submitted = st.form_submit_button(

            "Submit",

            key=
                f"enter_submit_{st.session_state.prompt_version}",

        )


        st.session_state.prompt_seed = ""


# =========================================================
# THINK BUTTON
# =========================================================

with prompt_col3:

    think_clicked = st.button(

        "🧠 Think",

        use_container_width=True,

        key="think_button",

        help=(
            "Think mode gives a more structured answer "
            "with concept, steps, verification and final result."
        ),

    )


# =========================================================
# SEND BUTTON
# =========================================================

with prompt_col5:

    send_clicked = st.button(

        "↑",

        use_container_width=True,

        key="send_button",

        help="Send message",

    )


# =========================================================
# VOICE ERROR
# =========================================================

if st.session_state.voice_error:

    st.warning(
        st.session_state.voice_error
    )

    st.session_state.voice_error = None


# =========================================================
# ATTACHMENTS
# =========================================================

if st.session_state.uploaded_files:

    st.markdown(
        "### 📎 Attached Files"
    )


    for file in st.session_state.uploaded_files:

        st.caption(
            f"• {file.name}"
        )


if st.session_state.drive_links:

    st.markdown(
        "### ☁️ Attached Drive Files"
    )


    for link in st.session_state.drive_links:

        st.caption(
            f"• {link}"
        )


# =========================================================
# LEARNING MODE
# =========================================================

if st.session_state.learning_mode:

    st.info(
        "📚 Learning Mode is active. "
        "The AI Tutor will focus on step-by-step explanations."
    )


# =========================================================
# FINAL QUERY
# =========================================================

final_query = ""

think_mode_active = False


if (
    enter_submitted
    or send_clicked
    or think_clicked
):

    if user_prompt.strip():

        final_query = (
            user_prompt.strip()
        )


        # =================================================
        # THINK MODE
        # =================================================

        if think_clicked:

            think_mode_active = True

    else:

        st.warning(
            "Please enter a question or use the microphone."
        )


# =========================================================
# EXECUTE RAG
# =========================================================

if final_query:

    if think_mode_active:

        with st.spinner(
            "🧠 Thinking — analyzing the question, "
            "checking the relevant context and preparing "
            "a structured answer..."
        ):

            process_query(
                final_query,
                think_mode=True,
            )

    else:

        process_query(
            final_query,
            think_mode=False,
        )


    # -----------------------------------------------------
    # Create a fresh prompt widget.
    # -----------------------------------------------------

    st.session_state.prompt_version += 1


    # -----------------------------------------------------
    # Rerun once so the new message appears immediately.
    # -----------------------------------------------------

    st.rerun()