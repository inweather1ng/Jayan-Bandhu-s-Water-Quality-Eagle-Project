import streamlit as st
import pandas as pd
st.set_page_config(page_title="Do the Salmon like my creek?",layout="wide",page_icon="🐟")
st.title("Do the Salmon like my creek?")
st.header("A Water Quality and Environmental DNA(eDNA) Data Visualization and Analysis Tool.\n")




if "dry creek" not in st.session_state or "miners ravine" not in st.session_state:
    try:
        data=pd.read_csv("Waterquality.csv")
        mr = data[data["Site"] == "JBDC01"]
        dc = data[data["Site"] == "JBDC02"]
        sc = data[data["Site"]=="JBDC03"]
        mr["Date"] = pd.to_datetime(mr["Date"], format="%m/%d/%Y",errors="coerce")
        dc["Date"] = pd.to_datetime(dc["Date"], format="%m/%d/%Y",errors="coerce")
        sc["Date"] = pd.to_datetime(sc["Date"], format="%m/%d/%Y",errors="coerce")
        mr=mr.sort_values('Date')
        dc=dc.sort_values('Date')
        sc=sc.sort_values('Date')
        st.session_state['dry creek']=dc
        st.session_state['miners ravine']=mr
    except FileNotFoundError:
        st.info("Files are not on the computer.")
# st.html("""
# <style>
# .st-key-my_custom_container {
    
#     }
# """)
with st.container(border=True):
    st.write("Come to the Dry Creek Conservancy's Salmon homecoming event on :red[November 8] for a :red[live presentation of this Dashboard] and more!")
    st.write("Event wil be held at Royer park")
    st.link_button(url="https://www.drycreekconservancy.org/events/",label="More info here",type="primary")


st.header("About the Dry Creek Watershed")
col1,col2=st.columns(2)


    



    
with col1:
    st.image("dccwatershed.png",caption="Map of the Dry Creek watershed, image courtesy of Dry creek Conservancy",use_container_width=True)

    
    
    
with col2:
    st.write("The Dry Creek watershed stretches across 101 square miles through Placer and Sacramento counties. Native Fall-run Chinook Salmon and threatened Central Valley Steelhead Trout return to Dry Creek to spawn. ")

st.link_button(url="https://drycreekconservancy.org",label="Learn more about the Dry Creek Conservancy")

with st.container(border=True):
    st.subheader(f"For 2025, the Dry Creek Conservancy counted 254 Salmon, The highest since 2014!!")
    

st.header("\n\n\nData collection info")
st.markdown(f"""Data being collected monthly from July 2026 onward. (Site 3 recently added October 2026) \n\n
• All physiochemical and biological data is being collected under an official QAPP approved the State Water Boards. \n\n
• Data uploaded to California Environmental Data Exchange network(CEDEN). \n\n
• Clearance to proceed with project from city of Roseville. """
)


