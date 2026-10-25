import streamlit as st
import pandas as pd
st.set_page_config(page_title="How is my Creek Doing?",layout="wide",page_icon="🐟")
st.title("How is My Creek Doing?")
st.header("A Water Quality/Salmon Habitat Suitability Data Visualization and Analysis Tool\n")



st.write("You can view a water quality dashboard of the Dry Creek, and then Visualize your own data files as well (coming soon)!")
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
st.header("About the Dry Creek Watershed")
col1,col2=st.columns(2)
with col1:
    st.image("dccwatershed.png",caption="Map of the dry creek watershed, image courtesy of Dry creek Conservancy",use_container_width=True)

    
    
    
with col2:
    st.write("The Dry creek stretches across 101 square miles through Placer and Sacramento counties. Native Fall-run Chinook Salmon and threatened Central Valley Steelhead Trout return to spawn. ")

st.link_button(url="drycreekconservancy.org",label="Learn more about the Dry Creek Conservancy)")



st.header("\n\n\nData collection info")
st.markdown("All physiochemical and biological data is being collected under an official QAPP with guidance from the California Water Boards. Physichemical data collected using state-grade equipment from the Sierra Streams Institute. ")


