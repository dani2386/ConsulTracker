import streamlit as st
from src.config import VIEWS_DIR


st.set_page_config(layout='wide')

home = st.Page(page=VIEWS_DIR / 'home.py', title='Início', icon=':material/home:', default=True)
user = st.Page(page=VIEWS_DIR / 'user.py', title='Utente', icon=':material/person:')
painel = st.Page(page=VIEWS_DIR / 'global.py', title='Painel Geral', icon=':material/table_view:')

router = st.navigation([home, user, painel], position='hidden')

with st.sidebar:
    st.title('ConsulTracker')
    st.divider()

    st.page_link(home)
    st.page_link(user)
    st.page_link(painel)

router.run()
