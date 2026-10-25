import streamlit as st
import pandas as pd
st.set_page_config(page_title="Smart Watershed Monitoring Assistant for creek data visualization",layout="wide")
st.title("A Water Quality monitoring Dasboard and Visualizing tool for Volunteers and organizations alike.")
st.write("Choose which page you want to explore using the sidebar")
if "dry creek" not in st.session_state or "miners ravine" not in st.session_state:
    try:
        data=pd.read_csv("Waterquality.csv")
        mr = data[data["Site"] == "JBDC01"]
        dc = data[data["Site"] == "JBDC02"]
        mr["Date"] = pd.to_datetime(mr["Date"], format="%m/%d/%Y",errors="coerce")
        dc["Date"] = pd.to_datetime(dc["Date"], format="%m/%d/%Y",errors="coerce")
        mr=mr.sort_values('Date')
        dc=dc.sort_values('Date')
        st.session_state['dry creek']=dc
        st.session_state['miners ravine']=mr
    except FileNotFoundError:
        st.info("Files are not on the computer.")
col1,col2=st.columns(2)
with col1:
    st.header("How to use the app:")
    st.write("You can view an example water quality dashboard of the Dry Creek, and then Visualize your own data files as well!")
with col2:
    st.write("To navigate, use the sidebar on the left and get exploring!")
