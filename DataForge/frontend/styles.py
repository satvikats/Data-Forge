import streamlit as st

def inject_custom_styles():
    """
    Injects global CSS into Streamlit to create a premium, modern developer experience.
    Uses glassmorphism, refined dark-mode typography, gradient headings, and subtle animations.
    """
    st.set_page_config(
        page_title="DataForge | Intelligent Data Quality & Cleaning",
        page_icon="🛠️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS Injection
    st.markdown(
        """
        <style>
        /* Import Premium Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
        
        /* Apply font family to entire Streamlit app */
        html, body, [class*="css"], .stApp {
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
        }

        /* Main app background & container styling */
        .stApp {
            background: linear-gradient(135deg, #0f0c1b 0%, #15102a 50%, #0a0616 100%);
            color: #e2e8f0;
        }

        /* Custom Header Styling with Gradients */
        .main-title {
            background: linear-gradient(to right, #a78bfa, #818cf8, #60a5fa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3rem !important;
            font-weight: 800;
            margin-bottom: 0.5rem;
            letter-spacing: -0.05em;
        }
        
        .sub-title {
            color: #94a3b8;
            font-size: 1.15rem;
            margin-bottom: 2rem;
            font-weight: 300;
        }

        /* Glassmorphic Card Container */
        .glass-card {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            margin-bottom: 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease-in-out;
        }
        
        .glass-card:hover {
            border-color: rgba(139, 92, 246, 0.3);
            background: rgba(255, 255, 255, 0.04);
            transform: translateY(-2px);
        }

        /* Metrics Display */
        .metric-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 4px solid #8b5cf6;
            background: rgba(139, 92, 246, 0.05);
            padding: 12px 18px;
            border-radius: 4px 12px 12px 4px;
            margin-bottom: 15px;
        }
        
        .metric-label {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #94a3b8;
        }
        
        .metric-value {
            font-size: 1.75rem;
            font-weight: 700;
            color: #ffffff;
            font-family: 'Outfit', sans-serif;
        }

        /* Sidebar styling override */
        [data-testid="stSidebar"] {
            background-color: #0b0816 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        /* Standardizing Streamlit elements */
        div.stButton > button {
            background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 10px 24px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 14px 0 rgba(124, 58, 237, 0.3) !important;
            transition: all 0.2s ease !important;
        }
        
        div.stButton > button:hover {
            background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 20px 0 rgba(124, 58, 237, 0.4) !important;
        }
        
        div.stButton > button:active {
            transform: translateY(1px) !important;
        }

        /* Secondary actions button */
        .secondary-button button {
            background: rgba(255, 255, 255, 0.05) !important;
            color: #f1f5f9 !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            box-shadow: none !important;
        }
        
        .secondary-button button:hover {
            background: rgba(255, 255, 255, 0.08) !important;
            border-color: rgba(255, 255, 255, 0.2) !important;
        }

        /* Badges & Pills */
        .custom-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-right: 5px;
        }
        
        .badge-purple { background: rgba(139, 92, 246, 0.2); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.3); }
        .badge-blue { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
        .badge-green { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
        .badge-red { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
        .badge-orange { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }

        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(15, 12, 27, 0.5);
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(139, 92, 246, 0.3);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(139, 92, 246, 0.5);
        }
        </style>
        """,
        unsafe_allow_html=True
    )
