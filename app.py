import html

import streamlit as st

from src.memory.conversation_memory import ConversationMemory
from src.pipeline import generate_answer_from_saved_knowledge_base


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="KnowFlow AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# DESIGN SYSTEM
# ============================================================

BG = "#FCFDFE"
WHITE = "#FFFFFF"
SOFT = "#F6F8FA"
BLUE = "#6EA8FE"
BLUE_SOFT = "#EEF5FF"
TEXT = "#18212B"
SECONDARY = "#71808F"
MUTED = "#9AA6B2"
BORDER = "#E7ECF1"


# ============================================================
# GLOBAL CSS
# ============================================================

st.markdown(
    f"""
    <style>

    /* ======================================================
       GLOBAL
       ====================================================== */

    .stApp {{
        background: {BG};
        color: {TEXT};
    }}

    .main .block-container {{
        max-width: 1380px;
        padding-top: 1.8rem;
        padding-bottom: 6rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }}

    * {{
        font-family:
            Inter,
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            sans-serif;
    }}

    /* ======================================================
       SIDEBAR
       ====================================================== */

    section[data-testid="stSidebar"] {{
        background: {WHITE};
        border-right: 1px solid {BORDER};
    }}

    section[data-testid="stSidebar"] > div {{
        padding: 1.5rem 1.15rem;
    }}

    .brand {{
        display: flex;
        align-items: center;
        gap: 11px;
        margin-bottom: 2rem;
    }}

    .brand-icon {{
        width: 38px;
        height: 38px;
        border-radius: 12px;
        background: {BLUE_SOFT};
        border: 1px solid #DCEBFF;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #4F91ED;
        font-size: 20px;
        font-weight: 700;
    }}

    .brand-name {{
        font-size: 17px;
        font-weight: 700;
        color: {TEXT};
        line-height: 1.1;
    }}

    .brand-subtitle {{
        font-size: 11px;
        color: {MUTED};
        margin-top: 3px;
    }}

    .side-section {{
        margin-top: 1.8rem;
        margin-bottom: .65rem;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.1px;
        color: {MUTED};
        text-transform: uppercase;
    }}

    .status-card {{
        background: {SOFT};
        border: 1px solid {BORDER};
        border-radius: 13px;
        padding: 13px;
        margin-bottom: 10px;
    }}

    .status-row {{
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        font-weight: 650;
        color: {TEXT};
    }}

    .status-dot {{
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #68B984;
    }}

    .status-description {{
        color: {SECONDARY};
        font-size: 10px;
        line-height: 1.5;
        margin-top: 6px;
    }}

    .source-card {{
        background: {WHITE};
        border: 1px solid {BORDER};
        border-radius: 13px;
        padding: 12px 13px;
        margin-bottom: 8px;
    }}

    .source-title {{
        font-size: 12px;
        font-weight: 650;
        color: {TEXT};
    }}

    .source-description {{
        font-size: 10px;
        color: {SECONDARY};
        margin-top: 4px;
    }}

    .session-card {{
        background: {SOFT};
        border: 1px solid {BORDER};
        border-radius: 13px;
        padding: 13px;
        margin-bottom: 9px;
    }}

    .session-number {{
        font-size: 19px;
        font-weight: 700;
        color: {TEXT};
    }}

    .session-label {{
        font-size: 10px;
        color: {SECONDARY};
        margin-top: 2px;
    }}

    .stButton > button {{
        width: 100%;
        border-radius: 11px;
        border: 1px solid {BORDER};
        background: {WHITE};
        color: {TEXT};
        font-weight: 600;
        font-size: 12px;
        min-height: 40px;
    }}

    .stButton > button:hover {{
        border-color: #C9DDF8;
        background: {BLUE_SOFT};
        color: #4F91ED;
    }}

    /* ======================================================
       HERO
       ====================================================== */

    .topbar {{
        display: flex;
        justify-content: flex-end;
        margin-bottom: 2.3rem;
    }}

    .eyebrow {{
        color: #6099DF;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        margin-bottom: 9px;
    }}

    .hero-title {{
        font-size: clamp(32px, 4vw, 48px);
        line-height: 1.05;
        letter-spacing: -1.8px;
        font-weight: 750;
        color: {TEXT};
        margin: 0;
    }}

    .hero-title span {{
        color: #639CE6;
    }}

    .hero-description {{
        max-width: 670px;
        margin-top: 13px;
        margin-bottom: 2rem;
        font-size: 14px;
        line-height: 1.65;
        color: {SECONDARY};
    }}

    .ready-pill {{
        display: inline-flex;
        align-items: center;
        gap: 7px;
        padding: 8px 12px;
        border: 1px solid {BORDER};
        background: {WHITE};
        border-radius: 999px;
        font-size: 11px;
        font-weight: 650;
        color: {TEXT};
    }}

    .ready-dot {{
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #68B984;
    }}

    /* ======================================================
       METRICS
       ====================================================== */

    .metric-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-bottom: 2.3rem;
    }}

    .metric {{
        background: {WHITE};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 15px 17px;
    }}

    .metric-label {{
        color: {MUTED};
        font-size: 10px;
        font-weight: 650;
        text-transform: uppercase;
        letter-spacing: .8px;
    }}

    .metric-value {{
        color: {TEXT};
        font-size: 15px;
        font-weight: 700;
        margin-top: 5px;
    }}

    /* ======================================================
       CHAT
       ====================================================== */

    .chat-heading {{
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: {MUTED};
        margin-bottom: 12px;
    }}

    .user-message {{
        background: {BLUE_SOFT};
        border: 1px solid #DDEBFC;
        border-radius: 15px;
        padding: 14px 17px;
        margin-bottom: 13px;
        color: {TEXT};
        font-size: 13px;
        line-height: 1.6;
    }}

    .assistant-message {{
        background: {WHITE};
        border: 1px solid {BORDER};
        border-radius: 15px;
        padding: 18px 20px;
        margin-bottom: 15px;
        color: {TEXT};
        font-size: 13px;
        line-height: 1.7;
        box-shadow: 0 3px 16px rgba(24, 33, 43, .025);
    }}

    .message-label {{
        font-size: 10px;
        font-weight: 700;
        color: {MUTED};
        text-transform: uppercase;
        letter-spacing: .8px;
        margin-bottom: 8px;
    }}

    .assistant-icon {{
        color: #6099DF;
        margin-right: 5px;
    }}

    /* ======================================================
       SOURCE SECTION
       ====================================================== */

    .sources-label {{
        font-size: 10px;
        font-weight: 700;
        letter-spacing: .9px;
        text-transform: uppercase;
        color: {MUTED};
        margin-top: 17px;
        margin-bottom: 9px;
    }}

    .source-meta {{
        font-size: 11px;
        color: {SECONDARY};
        line-height: 1.5;
    }}

    .source-meta strong {{
        color: {TEXT};
        font-weight: 650;
    }}

    .source-preview {{
        background: {SOFT};
        border: 1px solid {BORDER};
        border-radius: 9px;
        padding: 10px 12px;
        margin-top: 8px;
        font-size: 11px;
        color: {SECONDARY};
        line-height: 1.6;
    }}

    div[data-testid="stExpander"] {{
        border: 1px solid {BORDER} !important;
        border-radius: 10px !important;
        background: {WHITE} !important;
        margin-bottom: 7px;
    }}

    div[data-testid="stExpander"] details summary {{
        font-size: 11px !important;
        color: {SECONDARY} !important;
    }}

    /* ======================================================
       INPUT
       ====================================================== */

    div[data-testid="stChatInput"] > div {{
        border: 1px solid #DCE3EA !important;
        border-radius: 15px !important;
        background: {WHITE} !important;
        box-shadow: 0 7px 28px rgba(24, 33, 43, .07) !important;
    }}

    div[data-testid="stChatInput"] textarea {{
        font-size: 13px !important;
        color: {TEXT} !important;
    }}

    /* ======================================================
       FOOTER
       ====================================================== */

    .footer {{
        text-align: center;
        color: {MUTED};
        font-size: 10px;
        margin-top: 3rem;
        padding-bottom: 1rem;
    }}

    /* ======================================================
       RESPONSIVE
       ====================================================== */

    @media (max-width: 800px) {{

        .main .block-container {{
            padding-left: 1rem;
            padding-right: 1rem;
        }}

        .metric-grid {{
            grid-template-columns: 1fr;
        }}

        .hero-title {{
            font-size: 34px;
        }}

        .ready-pill {{
            display: none;
        }}
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "memory" not in st.session_state:
    st.session_state.memory = ConversationMemory()

if "messages" not in st.session_state:
    st.session_state.messages = []


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="brand">
            <div class="brand-icon">✦</div>
            <div>
                <div class="brand-name">KnowFlow AI</div>
                <div class="brand-subtitle">Knowledge Assistant</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="side-section">System</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="status-card">
            <div class="status-row">
                <span class="status-dot"></span>
                Knowledge Base Ready
            </div>
            <div class="status-description">
                FAISS semantic index connected and ready.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="side-section">Sources</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="source-card">
            <div class="source-title">PDF Documents</div>
            <div class="source-description">
                Unstructured document knowledge.
            </div>
        </div>
        <div class="source-card">
            <div class="source-title">Google Sheets</div>
            <div class="source-description">
                Structured knowledge and tabular data.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="side-section">Session</div>',
        unsafe_allow_html=True,
    )

    # Each exchange contains one user message + one assistant message.
    message_count = len(st.session_state.memory)
    turn_count = message_count // 2

    st.markdown(
        f"""
        <div class="session-card">
            <div class="session-number">{turn_count}</div>
            <div class="session-label">
                conversation turns
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Clear Conversation"):
        st.session_state.memory.clear()
        st.session_state.messages = []
        st.rerun()


# ============================================================
# TOP BAR
# ============================================================

st.markdown(
    """
    <div class="topbar">
        <div class="ready-pill">
            <span class="ready-dot"></span>
            Knowledge Base Ready
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="eyebrow">AI Knowledge Assistant</div>

    <div class="hero-title">
        Ask your knowledge.<br>
        Get <span>grounded answers.</span>
    </div>
    <div class="hero-description">
        Search across documents and structured knowledge using semantic
        retrieval, grounded generation, and conversational memory.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# METRICS
# ============================================================

st.markdown(
    f"""
    <div class="metric-grid">
        <div class="metric">
            <div class="metric-label">Retrieval</div>
            <div class="metric-value">FAISS Semantic Search</div>
        </div>
        <div class="metric">
            <div class="metric-label">Generation</div>
            <div class="metric-value">Gemini LLM</div>
        </div>
        <div class="metric">
            <div class="metric-label">Memory</div>
            <div class="metric-value">{turn_count} Turns</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CONVERSATION
# ============================================================

if st.session_state.messages:

    st.markdown(
        '<div class="chat-heading">Conversation</div>',
        unsafe_allow_html=True,
    )

    for message in st.session_state.messages:

        role = message["role"]

        # ----------------------------------------------------
        # USER MESSAGE
        # ----------------------------------------------------

        if role == "user":

            safe_content = html.escape(
                message["content"]
            )

            st.markdown(
                f"""
                <div class="user-message">
                    <div class="message-label">You</div>
                    {safe_content}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ----------------------------------------------------
        # ASSISTANT MESSAGE
        # ----------------------------------------------------

        elif role == "assistant":

            st.markdown(
                """
                <div class="message-label">
                    <span class="assistant-icon">✦</span>
                    KnowFlow AI
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Render assistant Markdown normally.
            st.markdown(
                message["content"]
            )

            documents = message.get(
                "documents",
                [],
            )

            # ------------------------------------------------
            # RETRIEVED SOURCES
            # ------------------------------------------------

            if documents:

                st.markdown(
                    '<div class="sources-label">Retrieved Sources</div>',
                    unsafe_allow_html=True,
                )

                for index, document in enumerate(
                    documents,
                    start=1,
                ):

                    metadata = document.metadata

                    source = str(
                        metadata.get(
                            "source",
                            "Unknown",
                        )
                    )

                    page = metadata.get("page")
                    row = metadata.get("row")

                    # ----------------------------------------
                    # SOURCE TYPE
                    # ----------------------------------------

                    if page is not None:

                        source_name = "PDF Document"
                        location = f"Page {page}"

                    elif row is not None:

                        source_name = "Google Sheets"
                        location = f"Row {row}"

                    else:

                        source_name = "Knowledge Source"
                        location = "Source"

                    # ----------------------------------------
                    # SHORT TITLE
                    # ----------------------------------------

                    content = document.page_content.strip()

                    topic = ""

                    for line in content.splitlines():

                        if line.lower().startswith(
                            "topic:"
                        ):
                            topic = line.split(
                                ":",
                                1,
                            )[1].strip()
                            break

                    if not topic:

                        if page is not None:
                            topic = "World Bank Annual Report"

                        else:
                            topic = "Retrieved knowledge"

                    topic_safe = html.escape(topic)
                    source_safe = html.escape(source)

                    label = (
                        f"{index:02d}  "
                        f"{source_name} · {location}"
                    )

                    # ----------------------------------------
                    # COMPACT SOURCE CARD
                    # ----------------------------------------

                    with st.expander(label):

                        st.markdown(
                            f"""
                            <div class="source-meta">
                                <strong>Source</strong><br>
                                {source_safe}
                            </div>

                            <div class="source-meta"
                                 style="margin-top:8px;">
                                <strong>Topic</strong><br>
                                {topic_safe}
                            </div>

                            <div class="source-meta"
                                 style="margin-top:8px;">
                                <strong>Location</strong><br>
                                {location}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        st.markdown(
                            '<div class="source-preview">',
                            unsafe_allow_html=True,
                        )

                        st.markdown(
                            content
                        )

                        st.markdown(
                            '</div>',
                            unsafe_allow_html=True,
                        )


# ============================================================
# CHAT INPUT
# ============================================================

user_query = st.chat_input(
    "Ask KnowFlow AI about your knowledge..."
)


# ============================================================
# PROCESS QUERY
# ============================================================

if user_query:

    try:

        with st.spinner(
            "Searching your knowledge..."
        ):

            result = generate_answer_from_saved_knowledge_base(
                query=user_query,
                memory=st.session_state.memory,
            )

        # Save only after successful generation.
        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_query,
            }
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": result["answer"],
                "documents": result.get(
                    "documents",
                    [],
                ),
            }
        )

        st.rerun()

    except Exception as exc:

        error_text = str(exc)

        if (
            "429" in error_text
            or "RESOURCE_EXHAUSTED" in error_text
        ):

            st.error(
                "Gemini API quota has been reached. "
                "Please try again later or use another "
                "available API key."
            )

        else:

            st.error(
                "I couldn't process your request right now."
            )

            with st.expander("Technical details"):
                st.code(error_text)


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        KnowFlow AI · Retrieval-Augmented Generation · Conversational Memory
    </div>
    """,
    unsafe_allow_html=True,
)