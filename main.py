import streamlit as st
import pandas as pd
import os
import base64
import plotly.express as px
from io import BytesIO
import time
import traceback

# Import custom helper modules
from helper.config import (
    LinkedInLoginError, 
    InstagramLoginError, 
    InvalidCredentialsError, 
    XLoginError
)
from helper.linkedinscraper import LinkedInScraper
from helper.instagramscraper import InstagramScraper
from helper.xscraper import XScraper

class VarturLeadGenerationApp:
    def __init__(self):
        # Configure page settings
        st.set_page_config(
            page_title="Social Media Lead Generation @ Vartur",
            page_icon="🎯",
            layout="wide"
        )
        
        # Initialize state management
        self._initialize_session_states()
        
        # Load and cache logos
        self.logos = self._load_logos()
        
        # Apply custom styling
        self._apply_custom_styling()
    
    def _initialize_session_states(self):
        """Initialize Streamlit session states"""
        session_states = {
            'debug_mode': False,
            'dataframe_result': None,
            'current_url': ""
        }
        for key, default_value in session_states.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def _load_logos(self):
        """Load and cache platform logos"""
        try:
            return {
                platform: self._image_to_base64(os.path.join('data', f'logo-{platform.lower()}.png'))
                for platform in ['LinkedIn', 'Instagram', 'X']
            }
        except Exception as e:
            st.error(f"Error loading images: {str(e)}")
            st.stop()
    
    @staticmethod
    @st.cache_data
    def _image_to_base64(image_path):
        """Convert image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    
    def _apply_custom_styling(self):
        """Apply custom CSS styling"""
        background = self._image_to_base64(os.path.join('data', 'background.png'))
        logo_base64 = self._image_to_base64(os.path.join('data', 'logo-vartur.png'))
        
        st.markdown(f"""
            <style>
                /* Existing styles remain the same */
            </style>
            """, unsafe_allow_html=True)
        
        # Create header
        st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 0;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 2em; margin-right: 10px;">🎯</span>
                    <h1 style="margin: 0;">Social Media Leads Generation</h1>
                </div>
                <img src="data:image/png;base64,{logo_base64}" style="width: 150px; height: 150px; margin-right: 50px;">
            </div>
        """, unsafe_allow_html=True)
        
        st.divider()
    
    def _render_sidebar(self):
        """Render sidebar with platform and login options"""
        with st.sidebar:
            st.title("Platform")
            
            # Platform selection
            lead_filter = st.radio("Choose a Platform", ["LinkedIn", "Instagram", "X"])
            
            # Debug mode toggle
            st.session_state.debug_mode = st.checkbox("Debug Mode", value=st.session_state.debug_mode)
            
            # Login section
            st.markdown(f"### {lead_filter} Login")
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Save Credentials")
                
                if submitted:
                    st.session_state['email'] = email
                    st.session_state['password'] = password
                    st.success("Credentials saved!")
            
            return lead_filter
    
    def _process_platform_leads(self, platform, url):
        """Generic method to process leads for different platforms"""
        scrapers = {
            "LinkedIn": LinkedInScraper,
            "Instagram": InstagramScraper,
            "X": XScraper
        }
        
        login_errors = {
            "LinkedIn": LinkedInLoginError,
            "Instagram": InstagramLoginError,
            "X": XLoginError
        }
        
        if not url:
            st.info(f"Please enter a {platform} post URL to begin.")
            return None
        
        if 'email' not in st.session_state or not st.session_state['email']:
            st.warning(f"Please enter your {platform} credentials in the sidebar first.")
            return None
        
        if st.button("Generate Leads", use_container_width=True):
            with st.spinner('Processing... This may take a few minutes.'):
                try:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text(f"Logging in to {platform}...")
                    progress_bar.progress(20)
                    
                    # Select appropriate scraper and create instance
                    ScraperClass = scrapers[platform]
                    scraper_kwargs = {
                        'url': url,
                        'email': st.session_state['email'],
                        'password': st.session_state['password'],
                        'is_headless': not st.session_state.debug_mode
                    }
                    
                    # Adjust kwargs based on platform-specific requirements
                    if platform == 'Instagram':
                        scraper_kwargs['headless'] = not st.session_state.debug_mode
                    
                    # Perform scraping
                    dataframe_result = ScraperClass(**scraper_kwargs).scrape()
                    
                    progress_bar.progress(100)
                    status_text.text("Processing complete!")
                    time.sleep(1)
                    status_text.empty()
                    progress_bar.empty()
                    
                    return dataframe_result
                
                except InvalidCredentialsError:
                    st.error(f"Invalid {platform} credentials. Please check your email and password.")
                except login_errors[platform] as e:
                    st.error(f"Login error: {str(e)}")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    if st.session_state.debug_mode:
                        with st.expander("Error Details"):
                            st.code(traceback.format_exc())
                
                return None
    
    def _render_data_analysis_tabs(self, df, platform):
        """Render data and analysis tabs with platform-specific logic"""
        if df is None or df.empty:
            st.warning("No results found for this URL.")
            return
        
        tab1, tab2 = st.tabs(["📊 Data", "📈 Analysis"])
        
        with tab1:
            self._render_data_tab(df, platform)
        
        with tab2:
            self._render_analysis_tab(df, platform)
    
    def _render_data_tab(self, df, platform):
        """Render data tab with filtering and download options"""
        st.markdown("### Data")
        
        # Determine filtering strategy based on platform
        filtered_df = df
        if platform in ["LinkedIn", "Instagram"] and 'Is Lead' in df.columns:
            lead_filter = st.selectbox(
                "Filter by lead status:",
                ["All", "Lead", "Not a Lead"]
            )
            if lead_filter != "All":
                filtered_df = df[df["Is Lead"] == lead_filter]
        
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        
        # Download options
        col1, col2 = st.columns(2)
        with col1:
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                "Download as CSV",
                csv,
                f"{platform.lower()}_leads.csv",
                "text/csv",
                use_container_width=True
            )
        with col2:
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                filtered_df.to_excel(writer, sheet_name='Data', index=False)
            excel_data = buffer.getvalue()
            st.download_button(
                "Download as Excel",
                excel_data,
                f"{platform.lower()}_leads.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    def _render_analysis_tab(self, df, platform):
        """Render analysis tab with platform-specific visualizations"""
        if platform in ["LinkedIn", "Instagram"]:
            self._render_lead_analysis(df)
        elif platform == "X":
            self._render_x_analysis(df)
    
    def _render_lead_analysis(self, df):
        """Render lead analysis for platforms with lead classification"""
        total_leads = len(df[df["Is Lead"] == "Lead"]) if "Is Lead" in df.columns else 0
        total_comments = len(df)
        lead_rate = (total_leads / total_comments * 100) if total_comments > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Comments", total_comments)
        with col2:
            st.metric("Total Leads", total_leads)
        with col3:
            st.metric("Lead Rate", f"{lead_rate:.1f}%")
        
        # Lead distribution pie chart
        fig = px.pie(
            df,
            names="Is Lead" if "Is Lead" in df.columns else None,
            title="Lead Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_x_analysis(self, df):
        """Render specific analysis for X platform"""
        # Implementation similar to your original code
        # ...
    
    def run(self):
        """Main application run method"""
        # Render platform selection and sidebar
        lead_filter = self._render_sidebar()
        
        # Render platform-specific logo and header
        st.markdown(f""" 
            <div style="display: flex; align-items: center;">
                <img src="data:image/png;base64,{self.logos[lead_filter]}" style="width: 30px; height: 30px;">
                <h2 style="margin-left: 10px;">{lead_filter} Leads Generation</h2>
            </div>
        """, unsafe_allow_html=True)
        
        # URL input
        url = st.text_input(f"Enter {lead_filter} Post URL:")
        
        # Process leads when URL changes
        if url != st.session_state.current_url:
            st.session_state.dataframe_result = None
            st.session_state.current_url = url
        
        # Process and display leads
        st.session_state.dataframe_result = self._process_platform_leads(lead_filter, url)
        self._render_data_analysis_tabs(st.session_state.dataframe_result, lead_filter)
        
        # Help section
        with st.expander("ℹ️ How to Use"):
            st.markdown(f"""
            1. Choose {lead_filter} platform from the sidebar
            2. Enter your login credentials in the sidebar
            3. Paste a {lead_filter} post URL in the input field
            4. Click Generate to analyze potential leads
            5. Download the results as CSV or Excel
            
            **Note:** The analysis may take a few minutes to complete.
            """)
        
        # Footer
        st.divider()
        st.markdown("""
            <div style='text-align: center; color: grey;'>
                Made with ❤️ by Vartur AI Team
            </div>
        """, unsafe_allow_html=True)

# Main execution
if __name__ == "__main__":
    app = VarturLeadGenerationApp()
    app.run()