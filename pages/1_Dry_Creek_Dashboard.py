import matplotlib.dates as mdates
import matplotlib
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Image, SimpleDocTemplate, Spacer, Paragraph, Table,TableStyle
from reportlab.lib import colors
import seaborn as sns
import folium
from streamlit_folium import st_folium
import time
from reportlab.lib.styles import getSampleStyleSheet
import plotly.express as px
import smtplib
from email.message import EmailMessage
from profanity_check import predict,predict_prob

qpcr=pd.read_csv("QPCR.csv")
st.markdown(
    """
<style>
/* Adjust the big number value size */
[data-testid="stMetricValue"] {
    font-size: 20px;
}
/* Adjust the label text size above the number */
[data-testid="stMetricLabel"] {
    font-size: 14px; /*  */
}
/* Adjust the delta text size below the number */
[data-testid="stMetricDelta"] {
    font-size:10px;
}
</style>
""",
    unsafe_allow_html=True,
)
#if "active_tab" not in st.session_state:
    #st.session_state.active_tab=0
# --- Data Processing ---
# Adjust filepath if necessary

    
def send_alerts(data):
    alert=None
    latest=data.iloc[-1]
    if latest['DO']<7 or latest['SPC']>500 or latest["Turbidity"]>10 or latest["Water Temp"]>25 or latest['PH']<6.5 or latest['PH']>8.5:
        alert=True
def censor(message):
    is_profane=predict([message])[0]
    prob = predict_prob([message])[0]
    if is_profane==1 or prob>0.8:
        return -1
    return message



# --- Helper Function for Plotly Interactive Shaded Threshold Zones ---
def pdf_download(prompt,miners_ravine,dry_creek):
    params=["DO","SPC","Turbidity","PH","Water Temp"]
    sites=["Miners Ravine","Dry Creek"]
    parameter=""
    site=""
    for i in params:
        if i.lower() in prompt.lower():
            parameter=i
            break
    for x in sites:
        if x.lower() in prompt.lower():
            site=x
            break
    param=parameter
    if param==""or site=="":
        st.warning("Command not recognized")
    else:

        text=[]

        finaldf=miners_ravine.copy()if site == "Miners Ravine" else dry_creek.copy()
        finaldf=finaldf.sort_values("Date")
        pdf=io.BytesIO()
        doc = SimpleDocTemplate(pdf,pagesize=letter,rightMargin=40,leftMargin=10)
        table_data=[["Date", f"{param} Value","Evaluation"]]
        for _,row in finaldf.iterrows():
            date_str = row['Date']
            val=row[parameter]
            if parameter=="DO":
                status="healthy" if val>7 else "unhealthy"
            elif parameter=="SPC":
                status="healthy" if val<200 else "unhealthy"
            elif parameter=="PH":
                status="healthy" if val>6.5 and val<8.5 else "unhealthy"
            elif parameter=="Turbidity":
                status="healthy" if val<10 else "unhealthy"
            else:
                status="healthy" if val>10 and val<20 else "unhealthy"
            table_data.append([date_str,val,status])
        avgval = finaldf[parameter].mean()
        minvl = finaldf[parameter].min()
        maxvL = finaldf[parameter].max()
        table_data.append(["average",round(avgval,2),""])
        table_data.append(["minimum",round(minvl,2),""])
        table_data.append(["maximum",round(maxvL,2),""])
        water_data = Table(table_data,colWidths=[120,80,100])
        water_data.setStyle(TableStyle([
    # Header Styling
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A365D")), # Dark navy header
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
    
    # Alternating row colors for the data rows (Rows 1 to length of data)
    ('BACKGROUND', (0, 1), (-1, -4), colors.HexColor("#F7FAFC")), 
    ('GRID', (0, 0), (-1, -4), 0.5, colors.lightgrey),
    
    # Summary Metrics Row Styling (Bottom 3 rows)
    ('LINEABOVE', (0, -3), (-1, -3), 1.5, colors.HexColor("#1A365D")), # Solid top boundary
    ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
    ('BACKGROUND', (0, -3), (-1, -1), colors.HexColor("#EDF2F7")), # Light grey summary fill
    ('BOTTOMPADDING', (0, -3), (-1, -1), 6),
    ]))


        
            

        fig3,ax3=plt.subplots()
        sns.lineplot(data=finaldf,x="Date",y=parameter,marker="o")
        ax3.tick_params(axis='x',labelsize=6)
        ax3.set_title(f"Data report for {parameter} over a {len(finaldf[parameter])} month period for the {site} site")
        img_buffer=io.BytesIO()
        fig3.savefig(img_buffer,format="png",bbox_inches="tight")
        img_buffer.seek(0)
        if parameter=="DO":
            thresholdstr="""Thresholds:

        Healthy: > 7.0 mg/L (Supports thriving aquatic life and salmonid requirements)

        Moderate Stress: 5.0 to 7.0 mg/L

        Critical / Hypoxia: < 5.0 mg/L (Causes severe stress or fish kills)"""
        elif parameter=="PH":
            thresholdstr="""Thresholds:

Healthy Basin Standard: 6.5 to 8.5 (Central Valley Regional Water Quality Control Board standard for inland surface waters)

Acidic Warning: < 6.5

Alkaline Warning: > 8.5"""
        elif parameter=="SPC":
            thresholdstr="""Natural Baseline: 100 to 300 µS/cm (Typical for Sierra foothill-fed valley streams)

Elevated Urban Impact: 300 to 500 µS/cm

Significant Runoff Pollution: > 500 µS/cm"""
        else:
            if parameter=="Turbidity":
                thresholdstr="""Clear / Base Flow: < 10 NTU

Moderate Runoff / Storm Impact: 10 to 50 NTU

Heavy Erosion / Storm Event: > 50 NTU"""
            else:
                thresholdstr="""Optimal Coldwater Habitat: < 18.0°C (64.4°F)

Elevated Stress Zone: 18.0°C – 21.0°C

High Thermal Stress: > 21.0°C (Significantly reduces oxygen-holding capacity)"""
            


        text.append(Image(img_buffer))
        y=len(finaldf)
        text.append(Paragraph(f"<b>Summary of Values over a {y} Month Period</b>"))
        text.append(Spacer(1,10))
        text.append(water_data)
        text.append(
            Paragraph(f"""Thresholds for {param}:<br/>
 {thresholdstr}""")
        )


        doc.build(text)
        pdf.seek(0)
        b=False
        st.download_button(label="Download report",data=pdf,file_name="Report.pdf")
        if st.button(label="View Preview"):
            b=not b
        if(b):
            st.pyplot(fig3)
        # fig3.savefig(img_buffer,format="png")



    
    
data=pd.read_csv("Waterquality.csv")
reqcols=["DO","SPC","Turbidity","Water Temp","PH","Site"]
# --- Main Layout ---
st.title("Dry Creek Water Quality Monitoring and Salmon Suitability Project")
# upload=(st.file_uploader(label="Enter your data here",type="csv"))
# time.sleep(5)
# is_valid=None
# missing=[]
# if upload != None:
#     data=pd.read_csv(upload)
#     data=data.dropna()
#     cols=data.columns.str.strip()
#     for c in reqcols:
#         if c not in cols:
#             missing.append(c)
#     if len(missing)>0:
#         is_valid=False
#         st.error(f"The following columns are missing from the data: {missing}, try adding them or renaming them. THere are the required columns: {reqcols}")
#     else:
#         errors=[]
#         do_prob = ((data["DO"] <4) | (data["DO"]>20))
#         cond_prob = ((data["SPC"] <10) | (data["SPC"]>1000)) 
#         ph_prob = ((data['PH']<4) | (data['PH'] > 11))
#         turbprob = ((data["Turbidity"]>500)| (data["Turbidity"]<0))
#         tempprob = ((data['Water Temp']>40) | (data['Water Temp']<0))
#         if do_prob.any():
#             errors.append("DO is out of the Required range\n")
#         if cond_prob.any():
#             errors.append("Some of your conductivity values are off \n")
#         if ph_prob.any():
#             errors.append("Some of your PH values are off\n")
#         if turbprob.any():
#             errors.append("Your turbidity values are off \n")
#         if tempprob.any():
#             errors.append("Your temperature values are off")
#         if len(errors)>0:
#             st.error(f"{errors}")
#         else:
#             is_valid=True
miners_ravine = data[data["Site"] == "JBDC01"]
dry_creek = data[data["Site"] == "JBDC02"]

tab_names=["Overview","Parameter deep dive", "Comparative analysis","Correlation analysis","PDF download","eDNA results","Feedback"]
selected_tab=st.sidebar.radio("Select Tab",tab_names)
#st.session_state.active_tab=tab_names.index(selected_tab)

    
# if not data.empty 
#and is_valid==True:


miners_ravine["Date"] = pd.to_datetime(miners_ravine["Date"], format="%m/%d/%Y")
dry_creek["Date"] = pd.to_datetime(dry_creek["Date"], format="%m/%d/%Y")

def on_tab_change():
    tab=selection
    st.session_state.active_tab=tab_names.index(tab)
if selected_tab=="Overview":
    st.header(f"Water Quality Dashboard and salmon sustainability monitor for The Dry Creek Watershed")
    st.space(size="small")
    st.markdown("""This project is a monthly Water Quality monitoring project of the Dry Creek watershed. We are monitoring 5 different physiochemical parameters and 2 eDNA parameters. " \
    **Our physiochemical parameters are**: Dissolved Oxygen(DO), Conductivity(SPC), Turbidity, Water temperature, and PH.""")
    st.markdown("Our eDNA parameters we sample for are Benthic macroinvertebrates and New Zealand Mudsnails ")

    
    st.subheader("Miners Ravine")
    if not miners_ravine.empty:
        latest_row = miners_ravine.iloc[-1]
        latest_do = latest_row["DO"]
        latest_cond = latest_row["SPC"]
        latest_ph = latest_row["PH"]
        latest_turbidity=latest_row["Turbidity"]
        latest_temp=latest_row['Water Temp']

        col1, col2, col3, col4,col5 = st.columns(5)
        with col1:
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
            ph_healthy = (
                "Normal: 6.5-8.5"
                if latest_ph >= 6.5 and latest_ph<=8.5
                else (
                    "Alkali" if latest_ph >= 8.5  else "Acidic"
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
            t_healthy = (
                "Clear <10NTU"
                if latest_turbidity <=10
                else (
                    "Cloudy" if latest_turbidity <= 50  else "Opaque"
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
    st.space(size="medium")
    st.subheader("Saugstad Park")
    colors=[]
    if not dry_creek.empty:
        latest_row = dry_creek.iloc[-1]
        latest_do = latest_row["DO"]
        latest_cond = latest_row["SPC"]
        latest_ph = latest_row["PH"]
        latest_turbidity=latest_row["Turbidity"]
        latest_temp=latest_row['Water Temp']

        col1, col2, col3, col4,col5 = st.columns(5)
        with col1:
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
            ph_healthy = (
                "Normal: 6.5-8.5"
                if latest_ph >= 6.5 and latest_ph<=8.5
                else (
                    "Alkali" if latest_ph >= 8.5  else "Acidic"
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
            t_healthy = (
                "Clear <10NTU"
                if latest_turbidity <=10
                else (
                    "Cloudy" if latest_turbidity <= 50  else "Opaque"
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
    miners_lat=miners_ravine.iloc[-1]
    miners_ravine_health = miners_lat['DO']>7 and miners_lat['PH'] > 6.5 and miners_lat['PH']<8.5 and miners_lat['Turbidity']<10 and miners_lat['Water Temp']<20 and miners_lat["SPC"]<200
    dry_lat=dry_creek.iloc[-1]
    dry_creek_health = dry_lat['DO']>7 and dry_lat['PH'] > 6.5 and dry_lat['PH']<8.5 and dry_lat['Turbidity']<10 and dry_lat['Water Temp']<20 and dry_lat["SPC"]<200
    if miners_ravine_health:
        miners_status = "Healthy"
    else:
        miners_status = "Stressed"
    if dry_creek_health:
        dry_status="Healthy"
    else:
        dry_status="Stressed"
    # st.title("Dry creek water quality monitoring Site map")
    st.header("This is a map of our two sampling sites on the Dry Creek.")
    mapdata=pd.DataFrame(
        {
            
            "latitude": [38.752945,38.742738,38.759216],
            "longitude":[-121.241526,-121.284156,-121.256444],
             "label": ["Miners Ravine", "Saugstad park","Confluence"],
             "fill":["green" if miners_status=="Healthy" else "red","green" if dry_status=="Healthy" else "red","green"],
             "health_status":[miners_status,dry_status,""],
             "Tab":[1,2,2]
         }
    )
    map=folium.Map(location=[38.74,-121.24],zoom_start=11)
    for idx,row in mapdata.iterrows():
        folium.CircleMarker(location=[row["latitude"],row["longitude"]],popup=f"For the {row['label']} site",fill=True,fill_color=row['fill'],tooltip=f"{row['label']} status: {row['health_status']}").add_to(map)
    map_out=st_folium(map,height=400,width=400)
    if map_out.get("last_object_clicked"):
        clicked_lat=map_out.get("last_object_clicked")['lat']
        clicked_lon=map_out.get("last_object_clicked")['lng']
        match=mapdata[abs(mapdata['latitude']-clicked_lat)<0.001].dropna()
        if not match.empty:
            st.session_state.active_tab=match.iloc[0]['Tab']
            st.rerun()
    st.caption("This map shows the three monitoring sites of this project in the form of blue circles.")




        

    
    
    # st.map(mapdata,latitude="latitude",longitude="longitude")
    # st.pydeck_chart(
    #     pydeck.Deck(
    #         initial_view_state=pydeck.ViewState(
    #             latitude=38.752,
    #             longitude=-121.24,
    #             zoom=15
    #         ),
    #         layers=[
    #             pydeck.Layer(
    #                 type="ScatterplotLayer",
    #                 data=mapdata,
    #                 get_position="[longitude,latitude]",
    #                 get_radius=50,
    #                 get_fill_color="fill",
    #                 pickable=True
                    
                    



    #             ),
    #             pydeck.Layer(
    #                 type="GeoJSON"
    #             )s
    #         ],
    #         tooltip={"html": """<b>Site:</b> {label}<br/><b>Health:</b> {healthy}
    #          <br/><b>Dissolved Oxygen:</b> {DO} mg/L<br/>
    #          <b>PH value</b> {PH}""",
    #          }
            
            

    #     )
    # )


elif selected_tab=="Parameter deep dive":
    if st.selectbox(label="Select a site",options=["Dry Creek at Saugstad","Miners Ravine at Orivetto Drive"])=="Dry Creek at Saugstad":
        dry_creek.sort_values('Date')
        
        fig4=px.line(
            dry_creek,
            x=dry_creek['Date'],
            y=dry_creek['DO'],
            markers=True,
            labels={"Date":"Date","DO":"DO"}
        )
        fig4.update_traces(
        line=dict(color="brown"),marker=dict(color="brown",size=8,symbol="circle")

        )
        fig4.update_layout(
        yaxis_range=[4,10],
        xaxis=dict(tickformat="%m/%d/%Y"),
        shapes=[
            dict(xref="paper",yref="y",x0=0,x1=1,y0=4,y1=5,fillcolor="red",opacity=0.5,layer="below",line_width=0),
            dict(xref="paper",yref="y",x0=0,x1=1,y0=5,y1=7,fillcolor="yellow",opacity=0.5,layer="below",line_width=0),
            dict(xref="paper",yref="y",x0=0,x1=1,y0=7,y1=10,fillcolor="green",opacity=0.5,layer="below",line_width=0)

        ]
        )
        chart=st.plotly_chart(fig4,use_container_width=True,selection_mode="points",key="Dry Creek DO",on_select='rerun')

        if chart and chart.get('selection',{}).get('points'):
            point=chart['selection']['points'][0]
            if point.get('y')<7:
                do_healthy="stressed"
            else:
                do_healthy="healthy"
            st.info(f"Date: {point.get('x')}, Dissolved Oxygen level: {point.get('y')}, {do_healthy}")
        st.markdown("""**Dissolved Oxygen**

What it measures: The amount of gaseous oxygen dissolved in the water, essential for fish and aquatic organisms to breathe.

Why it matters: As water temperature rises, its capacity to hold oxygen drops. Low DO indicates organic pollution, excessive algae decomposition, or stagnant water.

Dry Creek Thresholds:

Healthy: > 7.0 mg/L (Supports thriving aquatic life and salmonid requirements)

Moderate Stress: 5.0 to 7.0 mg/L

Critical / Hypoxia: < 5.0 mg/L (Causes severe stress or fish kills)





""")
        st.space("small")
        


        fig5=px.line(
            dry_creek,
            x=dry_creek['Date'],
            y=dry_creek['SPC'],
            markers=True,
            labels={"Date":"Date","SPC":"SPC"}
        )
        fig5.update_traces(
        line=dict(color="brown"),marker=dict(color="green",size=8,symbol="circle")

        )
        fig5.update_layout(
        yaxis_range=[0,500],
        xaxis=dict(tickformat="%m/%d/%Y"),
        shapes=[
            dict(xref="paper",yref="y",x0=0,x1=1,y0=0,y1=200,fillcolor="green",opacity=0.5,layer="below",line_width=0),
            dict(xref="paper",yref="y",x0=0,x1=1,y0=200,y1=300,fillcolor="yellow",opacity=0.5,layer="below",line_width=0),
            dict(xref="paper",yref="y",x0=0,x1=1,y0=300,y1=500,fillcolor="red",opacity=0.5,layer="below",line_width=0)

        ]
        )
        chart=st.plotly_chart(fig5,use_container_width=True,selection_mode="points",key="Dry Creek SPC",on_select="rerun")

        if chart and chart.get('selection',{}).get('points'):
            point=chart['selection']['points'][0]
            if point.get('y')>300:
                spc_healthy="High"
            else:
                spc_healthy="Healthy"
            st.info(f"Date: {point.get('x')}, Conductivity level: {point.get('y')}, {spc_healthy}")
        st.markdown("""**Electrical Conductivity or Specific Conductance**
    
What it measures: The ability of water to pass an electrical current, directly proportional to the concentration of dissolved ions (salts, minerals, and urban runoff pollutants).

Why it matters: High conductivity spikes during dry weather can indicate illicit discharges, failing septic systems, or excessive road salt/fertilizer wash.

Dry Creek Thresholds:

Natural Baseline: 100 to 300 µS/cm (Typical for Sierra foothill-fed valley streams)

Elevated Urban Impact: 300 to 500 µS/cm

Significant Runoff Pollution: > 500 µS/cm





""",unsafe_allow_html=False)
        st.space("small")
        

        st.space("small")
        fig6=px.line(
        dry_creek,
        x=dry_creek['Date'],
        y=dry_creek['PH'],
        markers=True,
        labels={"Date":"Date","PH":"PH"}
        )
        fig6.update_traces(
        line=dict(color="brown"),marker=dict(color="brown",size=8,symbol="circle")

        )
        fig6.update_layout(
        yaxis_range=[4,10],
        xaxis=dict(tickformat="%m/%d/%Y"),
        shapes=[
            dict(xref="paper",yref="y",x0=0,x1=1,y0=4,y1=6.5,fillcolor="red",opacity=0.5,layer="below",line_width=0),
            dict(xref="paper",yref="y",x0=0,x1=1,y0=6.5,y1=8.5,fillcolor="green",opacity=0.5,layer="below",line_width=0),
            dict(xref="paper",yref="y",x0=0,x1=1,y0=8.5,y1=10,fillcolor="red",opacity=0.5,layer="below",line_width=0)

        ]
        )
        chart=st.plotly_chart(fig6,use_container_width=True,selection_mode="points",key="Dry Creek PH",on_select="rerun")

        if chart and chart.get('selection',{}).get('points'):
            point=chart['selection']['points'][0]
            if point.get('y')<6.5:
                ph_healthy="acidic"
        
            elif point.get('y')>8.5:
                ph_healthy="Alkali"
            else:
                ph_healthy="healthy"
            st.info(f"Date: {point.get('x')} PH: {point.get('y')}, {ph_healthy}")
        st.markdown("""**PH: **

What it measures: The logarithmic measure of hydrogen ion concentration, indicating how acidic or basic the water is on a scale of 0 to 14.

Why it matters: Extreme pH levels (too acidic or too basic) can release toxic heavy metals from sediments into the water column and damage fish gills.

Dry Creek Thresholds:

Healthy Basin Standard: 6.5 to 8.5 (Central Valley Regional Water Quality Control Board standard for inland surface waters)

Acidic Warning: < 6.5

Alkaline Warning: > 8.5







""",unsafe_allow_html=False)
        st.space("small")
        
        fig7=px.line(
        dry_creek,
        x=dry_creek['Date'],
        y=dry_creek['Turbidity'],
        markers=True,
        labels={"Date":"Date","Turbidity":"Turbidity"}
        )
        fig7.update_traces(
        line=dict(color="brown"),marker=dict(color="brown",size=8,symbol="circle")

        )
        fig7.update_layout(
        yaxis_range=[0,100],
        xaxis=dict(tickformat="%m/%d/%Y"),
            shapes=[
                dict(xref="paper",yref="y",x0=0,x1=1,y0=0,y1=10,fillcolor="green",opacity=0.5,layer="below",line_width=0),
                dict(xref="paper",yref="y",x0=0,x1=1,y0=10,y1=50,fillcolor="yellow",opacity=0.5,layer="below",line_width=0),
                dict(xref="paper",yref="y",x0=0,x1=1,y0=50,y1=100,fillcolor="red",opacity=0.5,layer="below",line_width=0)

            ]
        )
        chart=st.plotly_chart(fig7,use_container_width=True,selection_mode="points",key="Dry Creek Turbidity",on_select="rerun")

        if chart and chart.get('selection',{}).get('points'):
            point=chart['selection']['points'][0]
            if point.get('y')>50:
                turb_healthy="Turbid"
        
            elif point.get('y')>10:
                turb_healthy="medium"
            else:
                turb_healthy="healthy"
            st.info(f"Date: {point.get('x')} Turbidity: {point.get('y')}, {turb_healthy}")
        st.markdown("""**Turbidity**

*What it measures:* Water clarity and the amount of suspended sediments (soil, silt, organic matter, and microscopic organisms) scattering light.

Why it matters: High turbidity blocks sunlight needed by aquatic plants and can clog fish gills or smother benthic macroinvertebrate habitats.

Dry Creek Thresholds:

Clear / Base Flow: < 10 NTU

Moderate Runoff / Storm Impact: 10 to 50 NTU

Heavy Erosion / Storm Event: > 50 NTU






""",unsafe_allow_html=False)
        st.space("small")
        
        fig=px.line(
        dry_creek,
        x=dry_creek['Date'],
        y=dry_creek['Water Temp'],
        markers=True,
        labels={"Date":"Date","Water Temp":"Water Temp"}
        )
        fig.update_traces(
        line=dict(color="brown"),marker=dict(color="brown",size=8,symbol="circle")

        )
        fig.update_layout(
            yaxis_range=[10,30],
            xaxis=dict(tickformat="%m/%d/%Y"),
            shapes=[
                dict(xref="paper",yref="y",x0=0,x1=1,y0=10,y1=20,fillcolor="green",opacity=0.5,layer="below",line_width=0),
                dict(xref="paper",yref="y",x0=0,x1=1,y0=20,y1=25,fillcolor="yellow",opacity=0.5,layer="below",line_width=0),
                dict(xref="paper",yref="y",x0=0,x1=1,y0=25,y1=30,fillcolor="red",opacity=0.5,layer="below",line_width=0)

            ]
        )
        chart=st.plotly_chart(fig,use_container_width=True,selection_mode="points",key="Dry Creek Water Temperature",on_select="rerun")

        if chart and chart.get('selection',{}).get('points'):
            point=chart['selection']['points'][0]
            if point.get('y')>25:
                temp_healthy="Too warm for cold water species"
        
            elif point.get('y')>20:
                temp_healthy="Warmer than normal"
            else:
                temp_healthy="Healthy"
            st.info(f"Date: {point.get('x')} Water Temperature: {point.get('y')}, {temp_healthy}")
        st.markdown("""**Water Temperature**

What it measures: The thermal condition of the water body.

Why it matters: Temperature controls metabolic rates in aquatic life and directly dictates Dissolved Oxygen saturation levels. Elevated temperatures often result from lack of riparian tree canopy or warm urban stormwater runoff.

Dry Creek Thresholds:

Optimal Coldwater Habitat: < 18.0°C (64.4°F)

Elevated Stress Zone: 18.0°C – 21.0°C

High Thermal Stress: > 21.0°C (Significantly reduces oxygen-holding capacity)







""",unsafe_allow_html=False)
        st.space("small")
        
    else:
        miners_ravine.sort_values('Date')
        st.markdown("")
        fig4=px.line(
            miners_ravine,
            x=miners_ravine['Date'],
            y=miners_ravine['DO'],
            markers=True,
            labels={"Date":"Date","DO":"DO"}
        )
        fig4.update_traces(
        line=dict(color="brown"),marker=dict(color="brown",size=8,symbol="circle")

        )
        fig4.update_layout(
        yaxis_range=[0,10],
        xaxis=dict(tickformat="%m/%d/%Y"),
        shapes=[
            dict(xref="paper",yref="y",x0=0,x1=1,y0=0,y1=5,fillcolor="red",opacity=0.5,layer="below",line_width=0),
            dict(xref="paper",yref="y",x0=0,x1=1,y0=5,y1=7,fillcolor="yellow",opacity=0.5,layer="below",line_width=0),
            dict(xref="paper",yref="y",x0=0,x1=1,y0=7,y1=10,fillcolor="green",opacity=0.5,layer="below",line_width=0)

        ]
        )
        chart=st.plotly_chart(fig4,use_container_width=True,selection_mode="points",key="Miners Ravine DO",on_select="rerun")

        if chart and chart.get('selection',{}).get('points'):
            point=chart['selection']['points'][0]
            if point.get('y')<7:
                do_healthy="stressed"
            else:
                do_healthy="healthy"
            st.info(f"Date: {point.get('x')} Dissolved Oxygen level: {point.get('y')}, {do_healthy}")
        st.markdown("""**DO**

What it measures: The amount of gaseous oxygen dissolved in the water, essential for fish and aquatic organisms to breathe.

Why it matters: As water temperature rises, its capacity to hold oxygen drops. Low DO indicates organic pollution, excessive algae decomposition, or stagnant water.

Miners Ravine Thresholds:

Healthy: > 7.0 mg/L (Supports thriving aquatic life and salmonid requirements)

Moderate Stress: 5.0 to 7.0 mg/L

Critical / Hypoxia: < 5.0 mg/L (Causes severe stress or fish kills)



""",unsafe_allow_html=False)

        st.space("small")
        fig5=px.line(
            miners_ravine,
            x=miners_ravine['Date'],
            y=miners_ravine['SPC'],
            markers=True,
            labels={"Date":"Date","SPC":"SPC"}
        )
        fig5.update_traces(
        line=dict(color="brown"),marker=dict(color="green",size=8,symbol="circle")

        )
        fig5.update_layout(
        yaxis_range=[0,500],
        xaxis=dict(tickformat="%m/%d/%Y"),
        shapes=[
            dict(xref="paper",yref="y",x0=0,x1=1,y0=0,y1=200,fillcolor="green",opacity=0.5,layer="below",line_width=0),
            dict(xref="paper",yref="y",x0=0,x1=1,y0=200,y1=300,fillcolor="yellow",opacity=0.5,layer="below",line_width=0),
            dict(xref="paper",yref="y",x0=0,x1=1,y0=300,y1=500,fillcolor="red",opacity=0.5,layer="below",line_width=0)

        ]
        )
        chart=st.plotly_chart(fig5,use_container_width=True,selection_mode="points",key="Miners Ravine SPC",on_select="rerun")

        if chart and chart.get('selection',{}).get('points'):
            point=chart['selection']['points'][0]
            if point.get('y')>300:
                spc_healthy="High"
            else:
                spc_healthy="Healthy"
            st.info(f"Date: {point.get('x')} Conductivity level: {point.get('y')}, {spc_healthy}")
        st.markdown("""**Conductivity**

What it measures: The ability of water to pass an electrical current, directly proportional to the concentration of dissolved ions (salts, minerals, and urban runoff pollutants).

Why it matters: High conductivity spikes during dry weather can indicate illicit discharges, failing septic systems, or excessive road salt/fertilizer wash.

Miners Ravine Thresholds:

Natural Baseline: 100 to 300 µS/cm (Typical for Sierra foothill-fed valley streams)

Elevated Urban Impact: 300 to 500 µS/cm

Significant Runoff Pollution: > 500 µS/cm




""",unsafe_allow_html=False)
        
        st.space("small")
        fig6=px.line(
        miners_ravine,
        x=miners_ravine['Date'],
        y=miners_ravine['PH'],
        markers=True,
        labels={"Date":"Date","PH":"PH"}
        )
        fig6.update_traces(
        line=dict(color="brown"),marker=dict(color="brown",size=8,symbol="circle")

        )
        fig6.update_layout(
        yaxis_range=[4,10],
        xaxis=dict(tickformat="%m/%d/%Y"),
        shapes=[
            dict(xref="paper",yref="y",x0=0,x1=1,y0=4,y1=6.5,fillcolor="red",opacity=0.5,layer="below",line_width=0),
            dict(xref="paper",yref="y",x0=0,x1=1,y0=6.5,y1=8.5,fillcolor="green",opacity=0.5,layer="below",line_width=0),
            dict(xref="paper",yref="y",x0=0,x1=1,y0=8.5,y1=10,fillcolor="red",opacity=0.5,layer="below",line_width=0)

        ]
        )
        chart=st.plotly_chart(fig6,use_container_width=True,selection_mode="points",key="Miners Ravine PH",on_select="rerun")

        if chart and chart.get('selection',{}).get('points'):
            point=chart['selection']['points'][0]
            if point.get('y')<6.5:
                ph_healthy="acidic"
        
            elif point.get('y')>8.5:
                ph_healthy="Alkali"
            else:
                ph_healthy="healthy"
            st.info(f"Date: {point.get('x')} PH: {point.get('y')}, {ph_healthy}")
        st.markdown("""**PH**

What it measures: The logarithmic measure of hydrogen ion concentration, indicating how acidic or basic the water is on a scale of 0 to 14.

Why it matters: Extreme pH levels (too acidic or too basic) can release toxic heavy metals from sediments into the water column and damage fish gills.

Miners Ravine Thresholds:

Healthy Basin Standard: 6.5 to 8.5 (Central Valley Regional Water Quality Control Board standard for inland surface waters)

Acidic Warning: < 6.5

Alkaline Warning: > 8.5




""",unsafe_allow_html=False)
        st.space("small")
        fig7=px.line(
        miners_ravine,
        x=miners_ravine['Date'],
        y=miners_ravine['Turbidity'],
        markers=True,
        labels={"Date":"Date","Turbidity":"Turbidity"}
        )
        fig7.update_traces(
        line=dict(color="brown"),marker=dict(color="brown",size=8,symbol="circle")

        )
        fig7.update_layout(
        yaxis_range=[0,100],
        xaxis=dict(tickformat="%m/%d/%Y"),
            shapes=[
                dict(xref="paper",yref="y",x0=0,x1=1,y0=0,y1=10,fillcolor="green",opacity=0.5,layer="below",line_width=0),
                dict(xref="paper",yref="y",x0=0,x1=1,y0=10,y1=50,fillcolor="yellow",opacity=0.5,layer="below",line_width=0),
                dict(xref="paper",yref="y",x0=0,x1=1,y0=50,y1=100,fillcolor="red",opacity=0.5,layer="below",line_width=0)

            ]
        )
        chart=st.plotly_chart(fig7,use_container_width=True,selection_mode="points",key="Miners Ravine Turbidity",on_select="rerun")

        if chart and chart.get('selection',{}).get('points'):
            point=chart['selection']['points'][0]
            if point.get('y')>50:
                turb_healthy="Turbid"
        
            elif point.get('y')>10:
                turb_healthy="medium"
            else:
                turb_healthy="healthy"
            st.info(f"Date: {point.get('x')} Turbidity: {point.get('y')}, {turb_healthy}")
        st.markdown("""**Turbidity**

What it measures:* Water clarity and the amount of suspended sediments (soil, silt, organic matter, and microscopic organisms) scattering light.

Why it matters: High turbidity blocks sunlight needed by aquatic plants and can clog fish gills or smother benthic macroinvertebrate habitats.

Miners Ravine Thresholds:

Clear / Base Flow: < 10 NTU

Moderate Runoff / Storm Impact: 10 to 50 NTU

Heavy Erosion / Storm Event: > 50 NTU



""",unsafe_allow_html=False)
        st.space("small")
        fig=px.line(
        miners_ravine,
        x=miners_ravine['Date'],
        y=miners_ravine['Water Temp'],
        markers=True,
        labels={"Date":"Date","Water Temp":"Water Temp"}
        )
        fig.update_traces(
        line=dict(color="brown"),marker=dict(color="brown",size=8,symbol="circle")

        )
        fig.update_layout(
            yaxis_range=[10,30],
            xaxis=dict(tickformat="%m/%d/%Y"),
            shapes=[
                dict(xref="paper",yref="y",x0=0,x1=1,y0=10,y1=20,fillcolor="green",opacity=0.5,layer="below",line_width=0),
                dict(xref="paper",yref="y",x0=0,x1=1,y0=20,y1=25,fillcolor="yellow",opacity=0.5,layer="below",line_width=0),
                dict(xref="paper",yref="y",x0=0,x1=1,y0=25,y1=30,fillcolor="red",opacity=0.5,layer="below",line_width=0)

            ]
        )
        chart=st.plotly_chart(fig,use_container_width=True,selection_mode="points",key="Dry Creek Water Temperature",on_select="rerun")

        if chart and chart.get('selection',{}).get('points'):
            point=chart['selection']['points'][0]
            if point.get('y')>25:
                temp_healthy="Too warm for cold water species"
        
            elif point.get('y')>20:
                temp_healthy="Warmer than normal"
            else:
                temp_healthy="Healthy"
            st.info(f"Date: {point.get('x')} Water Temperature: {point.get('y')}, {temp_healthy}")
        st.markdown("""**Water Temperature**

What it measures: The thermal condition of the water body.

Why it matters: Temperature controls metabolic rates in aquatic life and directly dictates Dissolved Oxygen saturation levels. Elevated temperatures often result from lack of riparian tree canopy or warm urban stormwater runoff.

Miners Ravine Thresholds:

Optimal Coldwater Habitat: < 18.0°C (64.4°F)

Elevated Stress Zone: 18.0°C – 21.0°C

High Thermal Stress: > 21.0°C (Significantly reduces oxygen-holding capacity)




""",unsafe_allow_html=False)
        st.space("small")

    

elif selected_tab=="Comparative analysis":
    st.subheader("Comparative Parameter analysis")
    param=st.selectbox(
        label="Select a parameter",
        options={
            "DO":"DO",
            "SPC":"SPC",
            "PH":"PH",
            "Turbidity":"Turbidity",
            "Water Temp":"Water Temp"
        },
        index=0

    )
    matplotlib.use('Agg')
    fig,ax=plt.subplots()
    
    ax1=ax.twinx()
    y1=miners_ravine[["Date",param]]
    y1=y1.sort_values(['Date'])
    y2=dry_creek[["Date",param]]
    y2=y2.sort_values(['Date'])

    sns.lineplot(data=y1,x='Date',y=param,marker="o",color="blue",ax=ax)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    if len(param)==2:
        if param=="DO":
            ax.set_ylim(5,10)
            ax1.set_ylim(5,10)
            ax.axhspan(5,6,color="red")
            ax.axhspan(6,7,color="yellow")
            ax.axhspan(7,10,color="green")
        else:
            ax.set_ylim(3,9)
            ax1.set_ylim(3,9)
            ax.axhspan(3,6.5,color="red")
            ax.axhspan(6.5,8.5,color="green")
            ax.axhspan(8.5,9,color="red")
    elif len(param)==3:
        ax.set_ylim(100,300)
        ax1.set_ylim(100,300)
        ax.axhspan(0,200,color="green")
        ax.axhspan(200,300,color="yellow")
    elif param=="Turbidity":
        ax.set_ylim(0,50)
        ax1.set_ylim(0,50)
        ax.axhspan(0,10,color="green")
        ax.axhspan(10,50,color="yellow")
        
    elif param=="Water Temp":
        ax.set_ylim(10,30)
        ax1.set_ylim(10,30)
        ax.axhspan(10,20,color="green")
        ax.axhspan(20,30,color="red")
    
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))


    
    sns.lineplot(data=y2,x="Date",y=param,marker="o",color="gray",ax=ax1)
    st.pyplot(fig)
    if len(param)==2:
        if param=="DO":
            st.markdown("""**DO**

        What it measures: The amount of gaseous oxygen dissolved in the water, essential for fish and aquatic organisms to breathe.

        Why it matters: As water temperature rises, its capacity to hold oxygen drops. Low DO indicates organic pollution, excessive algae decomposition, or stagnant water.

        Thresholds:

        Healthy: > 7.0 mg/L (Supports thriving aquatic life and salmonid requirements)

        Moderate Stress: 5.0 to 7.0 mg/L

        Critical / Hypoxia: < 5.0 mg/L (Causes severe stress or fish kills)

        """)
        else:
            st.markdown("""**PH: **

What it measures: The logarithmic measure of hydrogen ion concentration, indicating how acidic or basic the water is on a scale of 0 to 14.

Why it matters: Extreme pH levels (too acidic or too basic) can release toxic heavy metals from sediments into the water column and damage fish gills.

Dry Creek Thresholds:

Healthy Basin Standard: 6.5 to 8.5 (Central Valley Regional Water Quality Control Board standard for inland surface waters)

Acidic Warning: < 6.5

Alkaline Warning: > 8.5""")

    elif len(param)==3:
        st.markdown("""**Electrical Conductivity or Specific Conductance**
            
        What it measures: The ability of water to pass an electrical current, directly proportional to the concentration of dissolved ions (salts, minerals, and urban runoff pollutants).
        
        Why it matters: High conductivity spikes during dry weather can indicate illicit discharges, failing septic systems, or excessive road salt/fertilizer wash.
        
        Dry Creek Thresholds:
        
        Natural Baseline: 100 to 300 µS/cm (Typical for Sierra foothill-fed valley streams)
        
        Elevated Urban Impact: 300 to 500 µS/cm
        
        Significant Runoff Pollution: > 500 µS/cm""")


    elif param=="Turbidity":
        st.markdown("""**Turbidity**
        
        *What it measures:* Water clarity and the amount of suspended sediments (soil, silt, organic matter, and microscopic organisms) scattering light.
        
        Why it matters: High turbidity blocks sunlight needed by aquatic plants and can clog fish gills or smother benthic macroinvertebrate habitats.
        
        Dry Creek Thresholds:
        
        Clear / Base Flow: < 10 NTU
        
        Moderate Runoff / Storm Impact: 10 to 50 NTU
        
        Heavy Erosion / Storm Event: > 50 NTU""")
        
    elif param=="Water Temp":
        st.markdown("""**Water Temperature**
       
       What it measures: The thermal condition of the water body.
       
       Why it matters: Temperature controls metabolic rates in aquatic life and directly dictates Dissolved Oxygen saturation levels. Elevated temperatures often result from lack of riparian tree canopy or warm urban stormwater runoff.
       
       Dry Creek Thresholds:
       
       Optimal Coldwater Habitat: < 18.0°C (64.4°F)
       
       Elevated Stress Zone: 18.0°C – 21.0°C
       
       High Thermal Stress: > 21.0°C (Significantly reduces oxygen-holding capacity)""")
elif selected_tab=="Correlation analysis":
    st.title("Correlation analysis between parameters")
    x=st.multiselect(
        label="Select two parameters to compare",options={"DO":"DO",
                                                          "SPC":"SPC","Turbidity":"Turbidity","PH":"PH","Water Temp":"Water Temp",
                                                          },max_selections=2,default=["DO","Water Temp"]
    )
    if len(x)!=2:
        st.warning("Please select 2 parameters")
    if len(x)==2:
        p1,p2=x
        miners=miners_ravine.copy()
        miners['Site Name']="Miners Ravine"
        dry=dry_creek.copy()
        dry['Site Name']="Dry Creek"
        new=pd.concat([miners,dry])
        fig2,ax2=plt.subplots()
        sns.scatterplot(data=new,x=p1,y=p2,hue="Site Name",ax=ax2)
        st.pyplot(fig2)
        minerscorr=miners_ravine[p1].corr(miners_ravine[p2])
        dry_creekcorr=dry_creek[p1].corr(dry_creek[p2])
        
        if abs(minerscorr)>0.7:
            txt="Strong"
        elif abs(minerscorr)>0.4:
            txt="medium"
        else:
            txt="weak"
        if abs(dry_creekcorr)>0.7:
            txt2="Strong"
        elif abs(dry_creekcorr)>0.4:
            txt2="medium"
        else:
            txt2="weak"
        if minerscorr<0:
            sign="Negative"
        else:
            sign="Positive"
        if dry_creekcorr>0:
            sign2="Positive"
        else:
            sign2="Negative"
        col1,col2=st.columns(2)
        with col1:
            st.metric(value=minerscorr,label="Correlation for miners ravine site",delta=txt+","+sign,delta_color="normal" if minerscorr>0.5 else "inverse")
        with col2:
            st.metric(value=dry_creekcorr,label="Correlation for miners ravine site",delta=txt2+","+sign2,delta_color="normal" if txt2=="Strong" else "inverse")
elif selected_tab=="PDF download":
        userinput=st.text_input(label="Give a prompt for what parameter you want to download and which site you want to download.")
        if userinput.strip():
            pdf_download(userinput,miners_ravine,dry_creek)
elif selected_tab=="eDNA results":
    st.title("Environmental DNA (eDNA) Analysis")
    st.subheader("New Zealand Mudsnails")
    st.write("Sampling technique used: qPCR")
    st.markdown("**Significance:** The New Zealand Mudsnail is a tiny, highly invasive freshwater snail that reproduces rapidly by cloning, outcompeting native species and disrupting aquatic food webs.")
    col1,col2=st.columns(2)
    with col1:
        st.metric(
            label="New Zealand Mudsnail Samples, August 2026",
            value="0 Replications Detected",
            delta="First Sample",
            delta_color="normal"
        )
    with col2:
        st.metric(
            label="New Zealand Mudsnail Samples, September 2026",
            value="0 Replications Detected",
            delta="No change",
            delta_color="normal"
        )
    st.header("Benthic Macroinvertebrates (BMI)")
    st.write("Sampling technique used: Metabarcoding")
    st.markdown("**Significance** BMI are bottom-dwelling aquatic insects and organisms whose community diversity and pollution tolerance serve as key biological indicators of stream health.")
    st.metric(label="BMI Samples",value="In Process")
    st.space("large")
    st.dataframe(data={"eDNA type:":["NZMS","BMI"],"Lab Partner":["Jonah Ventures Laboratory"," UCSC CaleDNA Program"]})
elif selected_tab=="Feedback":
    st.header("Feedback Portal")
    st.write("Enter feedback as to how this dashboard can be improved!")
    with st.form(key="Form",clear_on_submit=True):
        message=st.text_area(label="Enter Your message!")
        submit=st.form_submit_button(label="Submit Feedback")
        if submit:
            if not message.strip():
                st.error("Enter is a message")
            else:
                if censor(message)==-1:
                    st.error("Message was flagged")
                else:
                    st.success("submitted!")
                    try:
                        st.write("starting")
                        msg = EmailMessage()
                        display="Anonymous community member"
                        msg.set_content(f"From {display}: \n\n {message}")
                        st.write("set content")
                        user_email = st.secrets['EMAIL_USER']
                        user_pass=st.secrets['USER_PASS']
                        adress=st.secrets['EMAIL']
                        st.write("retrieved email")
                        msg['From']=user_email
                        msg['To']=adress
                        print("set up path")
                        with smtplib.SMTP_SSL('smtp.gmail.com',465) as smtp:
                            smtp.login(user_email,user_pass)
                            st.write("sending")
                            smtp.send_message(msg)
                        st.success("Registered")
                    except Exception as e:
                        print(f"Encountered {e} while sending message")













        

    
        


    
