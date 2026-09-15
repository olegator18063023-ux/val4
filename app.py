import streamlit as st

st.set_page_config(
    page_title="ПобедИИтели",
    page_icon="⚙️",
    layout="wide",
)

st.title("ПобедИИтели")
st.subheader("Прогнозирование ресурса промышленного оборудования")

st.success("Приложение успешно запущено в Streamlit!")

st.info(
    "Это проверочная страница, а не полный симулятор. "
    "Предыдущую Flask-версию нужно заменить версией для Streamlit."
)
