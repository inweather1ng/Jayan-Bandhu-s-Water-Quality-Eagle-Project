import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import seaborn as sns
import json
import urllib.request
import matplotlib.dates as mdates
st.markdown("""
<style>
/* Adjust the big number value size */
[data-testid="stMetricValue"] {
    font-size: 20px;
}
/* Adjust the label text size above the number */
[data-testid="stMetricLabel"] {
    font-size: 6px;
}
/* Adjust the delta text size below the number */
[data-testid="stMetricDelta"] {
    font-size:10px;
}
</style>
""", unsafe_allow_html=True)


data=pd.read_csv("../Raw_data/Waterquality.csv")
miners_ravine=data[data['Site']=="JBDC01"]
dry_creek=data[data['Site']=="JBDC02"]
miners_ravine['Date']=pd.to_datetime(miners_ravine['Date'],format="%m/%d/%Y")
dry_creek['Date']=pd.to_datetime(dry_creek['Date'],format="%m/%d/%Y")
    
def create_threshold_zones(ax,low,mid,high):
    ax.axhspan(0,low,color="#ee0909",alpha=0.4,label="Low for fish(0-5 mg/l)")
    ax.axhspan(low,mid,color="#cdf506",alpha=0.4,label="Tolerance for warm water fish(5-7 mg/l)")
    ax.axhspan(mid,high,color="#0BE83E",alpha=0.4,label="Healthy(7-11) mg/l)")
def create_other_threshold_zones(ax,low,mid,high):
    ax.axhspan(0,low,color="#0BE83E",alpha=0.4,label="Low for fish(0-5 mg/l)")
    ax.axhspan(low,mid,color="#cdf506",alpha=0.4,label="Tolerance for warm water fish(5-7 mg/l)")
    ax.axhspan(mid,high,color="#ee0909",alpha=0.4,label="Healthy(7-11) mg/l)")
def create_third_threshold_zones(ax,lowlim,highlim,high):
    ax.axhspan(0,lowlim,color="#E83F0B",alpha=0.4,label="Low for fish(0-5 mg/l)")
    ax.axhspan(lowlim,highlim,color="#75f506",alpha=0.4,label="Tolerance for warm water fish(5-7 mg/l)")
    ax.axhspan(highlim,high,color="#ee0909",alpha=0.4,label="Healthy(7-11) mg/l)")
st.title("Dry Creek Water Quality Monitoring Project")
tab1,tab2=st.tabs(['Miners Ravine','Dry Creek_Saugstad park'])
with tab1:
    st.subheader("Water Quality Dashboard for Miner's Ravine")
    if not miners_ravine.empty:
        latest_row=miners_ravine.iloc[-1]
        latest_do=latest_row['DO']
        latest_cond=latest_row['SPC']
        latest_ph=latest_row['PH']
        col1,col2,col3=st.columns(3)
        with col1:
            if latest_do >= 7:
                do_healthy='Healthy > 7 (mg/l)' 
                color='normal'
            elif latest_do>=5 and latest_do<7 :
                do_healthy='Tolerable'
                color="off"
            else:
                do_healthy='Stressed'
                color="inverse"
            col1.metric(
                label='DIssolved Oxygen',
                value=f"{latest_do} mg/L",
                delta=do_healthy,
                delta_color=color
            )
        with col2:
            if latest_cond <= 150:
                cond_healthy='Healthy <150 ' 
                color2="normal"
            elif latest_cond>150 and latest_cond<=500 :
                cond_healthy='Moderate(150-500))'
                color2="off"
            else:
                cond_healthy='Stressed(>500 microsemens/cm)'   
                color2="inverse" 
            col1.metric(
            label='Conductivity',
            value=f"{latest_cond} µS/cm",
            delta=cond_healthy,
            delta_color=color2
            )   


    fig,ax=plt.subplots()
    sns.lineplot(data=miners_ravine,x='Date',y='DO')
    ax.set_ylim(0.0,11.0)
    ax.set_xlabel("Date")
    ax.set_ylabel("Dissolved Oxygen (mg/l)")
    ax.set_title("DO trend")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.legend(loc="upper right")
    create_threshold_zones(ax,5,7,11)
    

    plt.tight_layout()
    st.pyplot(fig)

        
    
    fig2,ax2=plt.subplots()
    sns.lineplot(data=miners_ravine,x='Date',y='SPC')
    ax2.set_ylim(0.0,800.0)
    ax2.set_xlabel("Date")
    ax2.set_ylabel("Specific Conductance")
    ax2.set_title("Specific conductivity trend")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax2.legend(loc="upper right")
    create_other_threshold_zones(ax2,150,500,800)
    

    plt.tight_layout()
    st.pyplot(fig2)
    

    fig3,ax3=plt.subplots()
    sns.lineplot(data=miners_ravine,x='Date',y='PH')
    ax3.set_ylim(0.0,11.0)
    ax3.set_xlabel("Date")
    ax3.set_ylabel("PH")
    ax3.set_title("PH trend")
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax3.legend(loc="upper right")
    create_third_threshold_zones(ax2,6,8,11)
    st.pyplot(fig2)
with tab2:
    st.subheader("Water Quality Dashboard for Dry Creek")
    if not dry_creek.empty:
        latest_row=dry_creek.iloc[-1]
        latest_do=latest_row['DO']
        latest_cond=latest_row['SPC']
        latest_ph=latest_row['PH']
        col1,col2,col3=st.columns(3)
        with col1:
            if latest_do >= 7:
                do_healthy='Healthy > 7 (mg/l)' 
                color='normal'
            elif latest_do>=5 and latest_do<7 :
                do_healthy='Tolerable'
                color="off"
            else:
                do_healthy='Stressed'
                color="inverse"
            col1.metric(
                label='DIssolved Oxygen',
                value=f"{latest_do} mg/L",
                delta=do_healthy,
                delta_color=color
            )
        with col2:
            if latest_cond <= 150:
                cond_healthy='Healthy <150 ' 
                color2="normal"
            elif latest_cond>150 and latest_cond<=500 :
                cond_healthy='Moderate(150-500))'
                color2="off"
            else:
                cond_healthy='Stressed(>500 microsemens/cm)'   
                color2="inverse" 
            col1.metric(
            label='Conductivity',
            value=f"{latest_cond} µS/cm",
            delta=cond_healthy,
            delta_color=color2
            )   


    fig,ax=plt.subplots()
    sns.lineplot(data=dry_creek,x='Date',y='DO')
    ax.set_ylim(0.0,11.0)
    ax.set_xlabel("Date")
    ax.set_ylabel("Dissolved Oxygen (mg/l)")
    ax.set_title("DO trend")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.legend(loc="upper right")
    create_threshold_zones(ax,5,7,11)
    

    plt.tight_layout()
    st.pyplot(fig)

        
    
    fig2,ax2=plt.subplots()
    sns.lineplot(data=dry_creek,x='Date',y='SPC')
    ax2.set_ylim(0.0,800.0)
    ax2.set_xlabel("Date")
    ax2.set_ylabel("Specific Conductance")
    ax2.set_title("Specific conductivity trend")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax2.legend(loc="upper right")
    create_other_threshold_zones(ax2,150,500,800)
    

    plt.tight_layout()
    st.pyplot(fig2)
    

    fig2,ax2=plt.subplots()
    sns.lineplot(data=dry_creek,x='Date',y='PH')
    ax2.set_ylim(0.0,11.0)
    ax2.set_xlabel("Date")
    ax2.set_ylabel("PH")
    ax2.set_title("PH trend")
    ax2.legend(loc="upper right")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    create_third_threshold_zones(ax2,6,8,11)
    st.pyplot(fig2)



  

