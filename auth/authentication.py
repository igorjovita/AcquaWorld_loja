import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth


class Authentication:
    def __init__(self):
        self.authenticator = None

    def authenticate(self):
        with open('auth/config.yaml') as file:
            config = yaml.load(file, Loader=SafeLoader)

        self.authenticator = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days'],
            config['preauthorized']
        )

        self.authenticator.login(location='sidebar')

    def sidebar(self):

        if st.session_state["authentication_status"]:
            with st.sidebar:
                st.image('auth/logo.png', use_column_width=True)
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader(f'*{st.session_state["name"]}*')
                with col2:
                    self.authenticator.logout()
