import streamlit as st
import numpy as np
import plotly.express as px
import pandas as pd
with st.container():
    st.caption("Coming soon!")
st.title("Watershed Water Quality monitoring tool for everyone to use!")
st.write("To get Started, Drop a csv file into the upload box below")
file=st.file_uploader(label="Enter in your organization's CSV file here!",type="csv")

if file is not None:
    file=pd.read_csv(file)
    cols=list(file.columns)
    watershed=st.text_input(label="Enter Your watershed name here")
    fish_category=st.selectbox(label="Which fish species does your watershed support?",options=["COld water fish(Salmonids)","Warm Water Fish","Other"] )
    col1,col2 = st.columns(2)
    with col1:
        

        date=st.selectbox(label="Date Column(Required)",options=cols,index=cols.index('Date') if 'Date' in cols else 0)
        site=st.selectbox(label="site column:",options=cols, index=cols.index('Site') if 'Site' in cols else 0)
        do=st.selectbox(label="DO column",options=['None']+cols,index=cols.index('DO')+1 if 'DO' in cols else 0)
        conductivity=st.selectbox(label="Couductivity Column:",options=['None']+cols,index=cols.index('Conductivity')+1 if 'Conductivity' in cols else 0)
    with col2:
        ph=st.selectbox(label="PH column",options=['None']+cols,index=cols.index('PH')+1 if 'PH' in cols else 0)
        turbidity=st.selectbox(label="Turbidity Column",options=['None']+cols,index=cols.index("Turbidity")+1 if 'Turbidity' in cols else 0)
        water_temp=st.selectbox(label="Temperature Column",options=['None']+cols,index=cols.index("Water Temperature")+1 if 'Water Temperature' in cols else 0)
    file[site]=file[site].astype(str).str.strip()
    results=[date,do,conductivity,ph,turbidity,water_temp,site]
    final=list(filter(lambda x: x != "None",results))
    final_df=file[final].copy()
    try:
        for c in list(final_df.columns):
            if c!=results[0] and c!=results[-1]:
                final_df[c]=pd.to_numeric(final_df[c],errors="coerce")
        final_df[date]=pd.to_datetime(final_df[date],errors="coerce")
        final_df=final_df.sort_values(date).dropna(subset=[date])
        if final_df.empty:
            st.error("empty data")
        if site!="None":
            unique_sites=file[site].unique()
            
            


            tab1,tab2,tab3,tab4=st.tabs(['Water Quality Dashboard','Parameter plots','Correlation analysis',"simulation"])
            with tab1:
                st.title(f"Water Quality Dashboard for the {watershed} watershed"
            )
            select=st.selectbox(label="Select the site you want to view Data for",options=unique_sites)
            specialdf=final_df[final_df[site]==select]
            st.write(f"🔍 DEBUG: Found {len(specialdf)} rows for site '{select}'")
            if not specialdf.empty:
                st.success("SUccessfuly proccesed Your Data")
                latest_row=specialdf.iloc[-1]
                colors=[]
            

                latest_do = latest_row[do] if do != "None" else "N/A"
                latest_cond = latest_row[conductivity] if conductivity != "None" else "N/A"
                latest_ph = latest_row[ph] if ph != "None" else "N/A"
                latest_turbidity=latest_row[turbidity] if turbidity != "None" else "N/A"
                latest_temp=latest_row[water_temp] if water_temp != "None"  else  "N/A"

                col1, col2, col3, col4,col5 = st.columns(5)
                with col1:
                    if do != "None":
                        do_healthy = (
                    "Healthy > 7 (mg/l)"
                        if latest_do >= 7
                        else (
                        "Tolerable" if latest_do >= 5 and latest_do < 7 else "Stressed"
                        ) 
                        )
                        color = (
                        "normal"
                        if latest_do >= 7
                        else ("off" if latest_do >= 5 and latest_do < 7 else "inverse")
                        )
                        st.metric(
                        label="Dissolved Oxygen",
                        value=f"{latest_do} mg/L",
                        delta=do_healthy,
                        delta_color=color,
                        )

                with col2:
                    if conductivity != "None":
                        cond_healthy = (
                    "Healthy <150 "
                        if latest_cond <= 150
                        else (
                    "Moderate(150-500)"
                            if latest_cond > 150 and latest_cond <= 500
                            else "Stressed(>500)"
                        )
                        )
                        color2 = (
                "normal"
                        if latest_cond <= 150
                        else (
                        "off"
                            if latest_cond > 150 and latest_cond <= 500
                            else "inverse"
                    )
                )
                        st.metric(
                        label="Conductivity",
                        value=f"{latest_cond} µS/cm",
                        delta=cond_healthy,
                        delta_color=color2,
                )
                with col3:
                    if ph !="None":
                        ph_healthy = (
                    "Normal: 6.5-8.5"
                        if latest_ph >= 6.5 and latest_ph<=8.5
                        else (
                        "alkali" if latest_ph >= 8.5  else "Acidic"
                        )
                    )
                        color = (
                    "normal"
                        if latest_ph >= 6.5 and latest_ph<=8.5
                        else "inverse"
                )
                        st.metric(
                        label="PH",
                        value=f"{latest_ph}",
                        delta=ph_healthy,
                        delta_color=color,
                )
                with col4:
                    if turbidity!="None":
                        t_healthy = (
                "Clear <10NTU"
                        if latest_turbidity <=10
                        else (
                     "Cloudy" if latest_do <= 50  else "Opaque"
                    )
                )
                        color = (
                "normal"
                        if latest_turbidity <= 10
                        else ("off" if latest_turbidity <= 50  else "inverse")
            )
                        st.metric(
                        label="Turbidity",
                        value=f"{latest_turbidity} NTU",
                        delta=t_healthy,
                        delta_color=color,
            )
                with col5:
                    if water_temp !="None":
                        temp_healthy=(
                    "Sustainable"
                        if latest_temp>=10 and latest_temp<=20
                        else("Hot" if latest_temp>20 else "cold")
            )
                        color=(
                "normal"if latest_temp>=10 and latest_temp<=21 else"inverse"
            )
                        st.metric(
                        label="Water temperature",
                        value=f"{latest_temp} degrees celsius",
                        delta=temp_healthy,
                        delta_color=color
            )
                st.header("Interactive point mapping")
    except Exception as e:
        st.error(f"Found {e}, retry column mapping")


    
    
    

