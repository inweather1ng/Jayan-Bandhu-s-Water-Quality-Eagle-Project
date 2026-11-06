import streamlit as st
import pandas as pd
st.set_page_config(page_title="Do the Salmon like my creek?",layout="wide",page_icon="🐟")
st.image("pages/dcc_logo.png",width=100)
st.markdown("**Adopted by [Dry Creek Conservancy](https://www.drycreekconservancy.org/) as a community resource**")
st.title("Do the Salmon like my creek?")
st.header("A Water Quality and Environmental DNA (eDNA) Data Visualization and Analysis Tool.\n")
st.caption("If on mobile, click on the chevron (>>) on the top left to navigate")



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
        st.session_state['secret ravine']=sc
    except FileNotFoundError:
        st.info("Files are not on the computer.")
# st.html("""
# <style>
# .st-key-my_custom_container {
    
#     }
# """)
if "dry creek" in st.session_state and "miners ravine" in st.session_state and "secret ravine" in st.session_state:
    with st.container(border=True):
        st.subheader("Salmon Health Status: GOOD 🐟")
        st.write("All 3 sites (Secret Ravine, Saugstad Park, and Miners Ravine) currently meet healthy thresholds for salmon!")
        site = st.radio("Select site to check salmon factors:", ["Miners Ravine", "Saugstad Park", "Secret Ravine"], horizontal=True)
        latest = st.session_state["miners ravine"].iloc[-1] if site == "Miners Ravine" else (st.session_state["dry creek"].iloc[-1] if site == "Saugstad Park" else st.session_state["secret ravine"].iloc[-1])
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Dissolved Oxygen", f"{latest['DO']} mg/L", "Healthy > 7")
        c2.metric("Conductivity", f"{latest['SPC']} µS/cm", "Healthy < 300")
        c3.metric("PH", f"{latest['PH']}", "Normal 6.5-8.5")
        c4.metric("Turbidity", f"{latest['Turbidity']} NTU", "Clear < 10")
        c5.metric("Water Temp", f"{latest['Water Temp']} °C", "Healthy < 20")
        st.page_link("pages/1_Dry_Creek_Data_Visualization.py", label="Click here to view full charts & tabs →")
with st.container(border=True):
    st.write("Come to the Dry Creek Conservancy's Salmon homecoming event on :red[November 8] for a :red[live presentation of this Dashboard] and more!")
    st.write("Event will be held at Royer park")
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
st.markdown(f"""• I started collecting data monthly from July 2026 onwards. (Site 3 recently added October 2026) \n\n
• I developed a QAPP with guidance from the State Water Boards for Physicochemical and Biological data. \n\n
• Data has been submitted to the California Environmental Data Exchange network (CEDEN). \n\n
• I have received Clearance for the water quality monitoring project from the city of Roseville. """
)
st.space("large")
col1,col2=st.columns(2)
with col1:
    st.markdown("Special thanks to the **Sierra Streams Institute** for providing training for conducting water quality monitoring and equipment")
with col2:
    st.image("SS_Logo_Color.jpg",width=100)


