import streamlit as st


st.set_page_config(layout='wide')

home = st.Page(page='views/home.py', title='Home', icon=':material/home:', default=True)
user = st.Page(page='views/user.py', title='Utente', icon=':material/person:')

router = st.navigation([home, user], position='hidden')

with st.sidebar:
    st.title('HealthTracker')
    st.divider()

    st.page_link(home)
    st.page_link(user)

router.run()
