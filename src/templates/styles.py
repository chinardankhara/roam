# Common CSS styles used across the app
RESET_BUTTON_CSS = """
    <style>
    /* Remove default padding/margin */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
        padding-left: 5rem;
        padding-right: 5rem;
    }
    
    /* Title styling */
    .stTitle {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* Input container styling */
    .input-container {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 20px 0;
        padding: 0;
    }
    
    /* Chat input styling */
    .stChatInput {
        flex-grow: 1;
        margin: 0;
    }

    /* Option menu styling */
    .stSelectbox {
        margin-bottom: 0;
    }
    
    /* Center the voice chat button */
    .stButton>button {
        width: 100%;
        padding: 20px;
        font-size: 20px;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""" 