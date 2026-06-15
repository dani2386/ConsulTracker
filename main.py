import streamlit as st


st.set_page_config(layout='wide')

home = st.Page(page='views/home.py', title='Home', icon=':material/home:')
user = st.Page(page='views/user.py', title='Utente', icon=':material/person:')
alertas = st.Page(page='views/alertas.py', title='Alertas', icon=':material/priority_high:')
inicio = st.Page(page='views/inicio.py', title='Início', icon=':material/favorite:', default=True)
painel = st.Page(page='views/painel.py', title='Painel Geral', icon=':material/table_view:')

router = st.navigation([home, user, alertas, inicio, painel], position='hidden')

with st.sidebar:
    st.title('HealthTracker')
    st.divider()

    st.page_link(home)
    st.page_link(user)
    st.page_link(alertas)
    st.page_link(inicio)
    st.page_link(painel)

router.run()
