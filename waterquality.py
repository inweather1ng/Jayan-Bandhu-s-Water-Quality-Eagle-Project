import matplotlib.dates as mdates
import matplotlib
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Image, SimpleDocTemplate, Spacer, Paragraph
import seaborn as sns
import folium
from streamlit_folium import st_folium
import time
from reportlab.lib.styles import getSampleStyleSheet

qpcr=pd.read_csv("Raw_data/QPCR.csv")
st.markdown(
    """
<style>
/* Adjust the big number value size */
[data-testid="stMetricValue"] {
    font-size: 20px;
}
/* Adjust the label text size above the number */
[data-testid="stMetricLabel"] {
    font-size: 14px; /* Fixed: 6px was microscopic */
}
/* Adjust the delta text size below the number */
[data-testid="stMetricDelta"] {
    font-size:10px;
}
</style>
""",
    unsafe_allow_html=True,
)
if "active_tab" not in st.session_state:
    st.session_state.active_tab=0
# --- Data Processing ---
# Adjust filepath if necessary

def send_alerts(data):
    alert=None
    latest=data.iloc[-1]
    if latest['DO']<7 or latest['SPC']>500 or latest["Turbidity"]>10 or latest["Water Temp"]>25 or latest['PH']<6.5 or latest['PH']>8.5:
        alert=True
    


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
        pdf=io.BytesIO()
        doc = SimpleDocTemplate(pdf,pagesize=letter,rightMargin=40,leftMargin=10)
        text=[]

        finaldf=miners_ravine.copy()if site == "Miners Ravine" else dry_creek.copy()
        finaldf=finaldf.sort_values("Date")
        fig3,ax3=plt.subplots()
        sns.lineplot(data=finaldf,x="Date",y=parameter,marker="o")
        ax3.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax3.set_title(f"Data report for {parameter} over a {len(finaldf[parameter])} month period for the {site} site")
        img_buffer=io.BytesIO()
        fig3.savefig(img_buffer,format="png",bbox_inches="tight")
        img_buffer.seek(0)
        if parameter=="DO":
            thresholdstr="""DO less than 5.0 mg/l: *Unhabitable*,
 DO between 5.0 mg/l to 7 mg/l: *stressful*,
 DO greater than 7.0: *Healthy*"""
        elif parameter=="PH":
            thresholdstr="""PH less than 6.5: Acidic.
 PH greater than 8.5: Alkali,
 PH 6.5-8.5: healthy"""
        elif parameter=="SPC":
            thresholdstr="""Conductivity less than 200: *healthy*,
Conductivity from 200-500: *tolerable*,
 Conductivity greater than 500: *Unhealthy*"""
        else:
            if parameter=="Turbidity":
                thresholdstr="""If turbidity is less than 10: *Healthy*,
 If turbidity is from 10-50: *Stressed*,
 Turbidity > 50 is *unhealthy*"""
            else:
                thresholdstr="If temperature from 10-20: Normal temperature, If temperature < 10, cold. If temperature > 20, warm"
            

        text.append(
            Paragraph(f"""Thresholds for {param}: {thresholdstr}""")
        )
        text.append(Image(img_buffer))

        doc.build(text)
        b=False
        st.download_button(label="Download report",data=pdf,file_name="Report.pdf")
        if st.button(label="View Preview"):
            b=not b
        if(b):
            st.pyplot(fig3)
        # fig3.savefig(img_buffer,format="png")



    
    

reqcols=["DO","SPC","Turbidity","Water Temp","PH","Site"]
# --- Main Layout ---
st.title("Dry Creek Water Quality Monitoring Project")
upload=(st.file_uploader(label="Enter your data here",type="csv"))
time.sleep(5)
is_valid=None
missing=[]
if upload != None:
    data=pd.read_csv(upload)
    data=data.dropna()
    cols=data.columns.str.strip()
    for c in reqcols:
        if c not in cols:
            missing.append(c)
    if len(missing)>0:
        is_valid=False
        st.error(f"The following columns are missing from the data: {missing}, try adding them or renaming them. THere are the required columns: {reqcols}")
    else:
        errors=[]
        do_prob = ((data["DO"] <4) | (data["DO"]>20))
        cond_prob = ((data["SPC"] <10) | (data["SPC"]>1000)) 
        ph_prob = ((data['PH']<4) | (data['PH'] > 11))
        turbprob = ((data["Turbidity"]>500)| (data["Turbidity"]<0))
        tempprob = ((data['Water Temp']>40) | (data['Water Temp']<0))
        if do_prob.any():
            errors.append("DO is out of the Required range\n")
        if cond_prob.any():
            errors.append("Some of your conductivity values are off \n")
        if ph_prob.any():
            errors.append("Some of your PH values are off\n")
        if turbprob.any():
            errors.append("Your turbidity values are off \n")
        if tempprob.any():
            errors.append("Your temperature values are off")
        if len(errors)>0:
            st.error(f"{errors}")
        else:
            is_valid=True
            miners_ravine = data[data["Site"] == "JBDC01"]
            dry_creek = data[data["Site"] == "JBDC02"]

tab_names=["Overview","Dry creek","Miners Ravine", "Comparative analysis","Correlation analysis","PDF fownload","eDNA results","Simulation"]
selected_tab=st.sidebar.radio("Select Tab",tab_names,index=st.session_state.active_tab)
st.session_state.active_tab=tab_names.index(selected_tab)

    
if not data.empty and is_valid==True:


    miners_ravine["Date"] = pd.to_datetime(miners_ravine["Date"], format="%m/%d/%Y")
    dry_creek["Date"] = pd.to_datetime(dry_creek["Date"], format="%m/%d/%Y")

    
if selected_tab=="Overview":
    st.header(f"Water Quality Dashboard for The Dry Creek Watershed")
    st.space(size="small")
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
    mapdata=pd.DataFrame(
        {
            
            "latitude": [38.752945,38.742738,38.759216],
            "longitude":[-121.241526,-121.284156,-121.256444],
             "label": ["Miners Ravine", "Saugstad park","Confluence"],
             "fill":["green" if miners_status=="Healthy" else "red","green" if dry_status=="Healthy" else "red","green"],
             "healthy":[miners_status,dry_status,""],
             "Tab":[1,2,2]
         }
    )
    map=folium.Map(location=[38.74,-121.24],zoom_start=11)
    # for idx,row in mapdata.iterrows():
    #     folium.CircleMarker(location=[row["latitude"],row["longitude"]],popup=f"Click to view Site {row['label']} Data",fill=True,fill_color=row['fill'],tooltip=).add_to(map)
    

    
    
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


if selected_tab=="Dry Creek":
    fig4,ax4=plt.subplots()
    sns.lineplot(data=dry_creek,x="Date",y="DO",ax=ax4,marker="o",color="black")
    ax4.set_title("DO trend for Dry Creek site")
    ax4.set_ylim(5,10)
    ax4.axhspan(5,6,color="red")
    ax4.axhspan(6,7,color="yellow")
    ax4.axhspan(7,10,color="green")
    ax4.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    st.pyplot(fig4)

    st.space("small")
    fig5,ax5=plt.subplots()
    sns.lineplot(data=dry_creek,x="Date",y="SPC",ax=ax5,marker="o",color="black")
    ax5.set_title("Conductivity trends for Dry Creek")
    ax5.set_ylim(0,500)
    ax5.axhspan(300,500,color="red")
    ax5.axhspan(200,300,color="yellow")
    ax5.axhspan(0,200,color="green")
    ax5.set_xlabel("Conductivity")
    ax5.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    st.pyplot(fig5)

    st.space("small")
    fig6,ax6=plt.subplots()
    sns.lineplot(data=dry_creek,x="Date",y="Turbidity",ax=ax6,marker="o",color="black")
    ax6.set_title("Turbidity trends for Dry Creek")

    ax6.set_ylim(0,100)
    ax6.axhspan(50,100,color="red")
    ax6.axhspan(10,50,color="yellow")
    ax6.axhspan(0,10,color="green")
    ax6.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    st.pyplot(fig6)

    st.space("small")
    figph,axph=plt.subplots()
    sns.lineplot(data=dry_creek,x="Date",y="PH",ax=axph,marker="o", color="black" )
    axph.set_title("PH trends for Dry Creek")
    axph.set_ylim(4,10)
    axph.axhspan(4,6.5,color="red")
    axph.axhspan(8.5,10,color="red")
    axph.axhspan(6.5,8.5,color="green")
    axph.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    st.pyplot(figph)
    st.space("small")
    temp,tempax=plt.subplots()
    sns.lineplot(data=dry_creek,x="Date",y="Water Temp",ax=tempax,marker="o",color="brown")
    tempax.set_title("Water temeprature for Dry Creek")
    tempax.set_ylim(0,30)
    tempax.axhspan(0,10,color="red")
    tempax.axhspan(10,20,color="green")
    tempax.axhspan(20,30,color="red")
    tempax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    st.pyplot(temp)
elif selected_tab=="Miners Ravine":
    fig4,ax4=plt.subplots()
    sns.lineplot(data=miners_ravine,x="Date",y="DO",ax=ax4,marker="o",color="black")
    ax4.set_title("DO trend for Miners Ravine site")
    ax4.set_ylim(5,10)
    ax4.axhspan(5,6,color="red")
    ax4.axhspan(6,7,color="yellow")
    ax4.axhspan(7,10,color="green")
    ax4.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    st.pyplot(fig4)

    st.space("small")
    fig5,ax5=plt.subplots()
    sns.lineplot(data=miners_ravine,x="Date",y="SPC",ax=ax5,marker="o",color="black")
    ax5.set_title("Conductivity trends for Miners Ravine site")
    ax5.set_ylim(0,500)
    ax5.axhspan(300,500,color="red")
    ax5.axhspan(200,300,color="yellow")
    ax5.axhspan(0,200,color="green")
    ax5.set_xlabel("Conductivity")
    ax5.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    st.pyplot(fig5)

    st.space("small")
    fig6,ax6=plt.subplots()
    sns.lineplot(data=miners_ravine,x="Date",y="Turbidity",ax=ax6,marker="o",color="black")
    ax6.set_title("Turbidity trends for Miners Ravine")

    ax6.set_ylim(0,100)
    ax6.axhspan(50,100,color="red")
    ax6.axhspan(10,50,color="yellow")
    ax6.axhspan(0,10,color="green")
    ax6.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    st.pyplot(fig6)

    st.space("small")
    figph,axph=plt.subplots()
    sns.lineplot(data=miners_ravine,x="Date",y="PH",ax=axph,marker="o", color="black" )
    axph.set_title("PH trends for Miners Ravine site")
    axph.set_ylim(4,10)
    axph.axhspan(4,6.5,color="red")
    axph.axhspan(8.5,10,color="red")
    axph.axhspan(6.5,8.5,color="green")
    axph.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    st.pyplot(figph)
    st.space("small")
    temp,tempax=plt.subplots()
    sns.lineplot(data=miners_ravine,x="Date",y="Water Temp",ax=tempax,marker="o",color="brown")
    tempax.set_title("Water temeprature for Miners Ravine site")
    tempax.set_ylim(0,30)
    tempax.axhspan(0,10,color="red")
    tempax.axhspan(10,20,color="green")
    tempax.axhspan(20,30,color="red")
    tempax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    st.pyplot(temp)    

    

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
            st.markdown("**What is DO?**")
            st.write("""Dissolved Oxygen Is a measurment of oxygen dissolved in the water. Dissolved oxygen levels are key for local salmonids as well as all other creek dwelling organisms. Dissolved oxygen levels determine on many factors, such as creek flow, bacteria, and Water temperature. Diournal variations on DO occur. In the afternoons, DO increases because photosynthesizing plants release oxygen during the day. DO decreases as these organisms don't photosynthesize and instead use up oxygen in cellular respiration. """)
            st.markdown("**Do Thresholds**")
            st.write("A DO level of 7 mg/l or greater is considered satisfactory for cold water fish like salmon and steelhead. ")
            st.write("A DO level between 5 mg/l and 7 mg/l is considered stressed becasue it puts the Juvenile salmonids in great distress and alters their ability to swim and nourish.")
            st.write("A DO level below 5 mg/l is considered unsurvivable for most creek dwelling organisms.")
        else:
            st.markdown("**What is PH?**")
            st.write("PH is a measure of acidity of the creek. An acidic PH can be caused by many factors, including pine needles or algae output. ")
            st.markdown("**PH thresholds**")
            st.write("PH values should stay within 6.5 to 8.5 for a balance of alkalinity and acidity. Anywhere outside of this range is considered impaired.")

    elif len(param)==3:
        st.markdown("**Specific Conductance**")
        st.write("Specific Conductance is a measure of charged particles dissolved in the creek water. Conductivity generally varies from creek to creek based on the minerals located in the area. Short term changes in conductivity tend to happen right after storm events. The first surge of Conductivity after storm drain runoff in urban areas is called the first flush. This is commonly seen in urban areas, and is relevant to the Saugstad park site which faces urbanizaiton.")
        st.markdown("**Thresholds for conductivity**")
        st.write("COnductivity numbers should not be anywhere above 500 Microsemens per centimeter. Generally, a healthy creek wil have a conductivity of below 200.")

    elif param=="Turbidity":
        st.markdown("**Turbidity**")

        st.write("Turbidity is a measure of the physical clarity of creek water. Turbidity values can vary greatly after storm events, or leaks of some sort. Also, large amounts of algae can increase the turbidity of the water. Turbidity is a general indicator of surface level pollution of a creek, making it an important vital sign.")
        st.markdown("**Turbidity Thresholds**")
        st.write("A clear creek should generally have a turbidity of less than 10 NTU. A muddy creek after a storm can have a turbidity between 10-50 NTU, and any greater than that points to an underlying issue with the creek.")
        
    elif param=="Water Temp":
        st.markdown("**Water Temperature**")
        st.write("Water temperature is a key parameter that determnies whether salmonids and other species will be able to survive in a creek. In the Dry Creek watershed, temperature varies greatly between summer and winter. High temperatures during the summer are less problematic than high temepratures later in the season. Water temperature also plays a role in other paramters liek DIssolved oxygen and conductivity.")
        st.markdown("**Temperature thresholds**")
        st.write("Water temperature should fall between a range of 10 degrees to 20 degrees celsius.")
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
        st.write(F"The correlation between {p1} and {p2} is {sign} and {txt} at the Miners Ravine Site")
        st.write(F"The correlation between {p1} and {p2} is {sign2} and {txt2} at the Dry Creek Site")
elif selected_tab=="PDF fownload":
        userinput=st.text_input(label="Give a prompt for what parameter you want to download and which site you want to download.")
        pdf_download(userinput,miners_ravine,dry_creek)
elif selected_tab=="eDNA results":
    st.header("Edna results")
    st.space(size="small")
    st.write("BMI Results: Pending")
    st.space(size="small")
    st.write("New Zealand Mudsnail qPCR Results: Good news, 0 strands were detected!")
    qpcr=qpcr.to_csv(index=False)
elif selected_tab=="Simulation":
    with st.sidebar:
        no1=["DO","SPC","Water Temp","PH","Turbidity"]
        p1 = st.selectbox(label="Select The independent variable you want to manipulate!",options=no1)
        no1.remove(p1)
        yval=st.selectbox(label="Select the responding variable you want to measure",options=no1)
        if no1=="DO":
            st.slider(label="Drag to change DO value",min_value=4,max_value=20,format=None)
        elif no1=="SPC":
            st.slider(label="Drag to change Conductivity Value",min_value=10,max_value=500,step=10)
        elif no1=="Turbidity":
            st.slider(label="Drag to change Turbidity Value",)




        

    
        


    
