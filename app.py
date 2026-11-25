import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="COER Admission Intelligence AI", page_icon="🎓", layout="wide")
st.title("🎓 COER Admission Intelligence AI")
st.caption("India-wide district and city admission intelligence | Recruitment planning")

REQUIRED = ["state","district","city","applications","admissions"]
ALIASES = {"state":["state_name"],"district":["district_name"],"city":["city_name","town"],
"applications":["application_count","leads"],"admissions":["enrolments","enrollments","joined"],
"year":["admission_year"],"programme":["program","course","branch"],"pcm_students":["class12_pcm","12th_pcm_students"],
"school_count":["schools"],"coaching_count":["coaching_centres"],"marketing_spend":["spend","campaign_spend"],
"travel_km":["distance_km"],"competitor_count":["nearby_competitors"],"latitude":["lat"],"longitude":["lon","lng"]}

def normalize(df):
    df=df.copy()
    for canonical, aliases in ALIASES.items():
        for col in [canonical]+aliases:
            match=next((c for c in df.columns if str(c).strip().lower().replace(" ","_")==col),None)
            if match:
                df=df.rename(columns={match:canonical}); break
    return df

def demo_data():
    rows=[
    ["Uttarakhand","Haridwar","Roorkee",520,156,2026,6500,55,18,420000,0,8,"Engineering"],
    ["Uttarakhand","Dehradun","Dehradun",430,108,2026,7800,72,25,390000,65,12,"Management"],
    ["Uttarakhand","Haridwar","Haridwar",390,117,2026,7200,64,20,340000,30,9,"Engineering"],
    ["Uttar Pradesh","Saharanpur","Saharanpur",480,120,2026,9000,78,30,410000,45,13,"Engineering"],
    ["Uttar Pradesh","Muzaffarnagar","Muzaffarnagar",360,108,2026,6800,59,22,300000,65,10,"Management"],
    ["Uttar Pradesh","Meerut","Meerut",620,124,2026,12000,105,48,560000,110,19,"Engineering"],
    ["Delhi","New Delhi","Delhi",300,45,2026,14000,115,42,520000,210,28,"Management"],
    ["Haryana","Gurugram","Gurugram",270,54,2026,9800,85,35,450000,230,20,"Engineering"],
    ["Himachal Pradesh","Una","Una",180,54,2026,3400,32,9,180000,190,5,"Engineering"],
    ["Punjab","Ludhiana","Ludhiana",220,55,2026,8500,70,24,250000,260,15,"Management"],
    ["Rajasthan","Jaipur","Jaipur",310,62,2026,13000,110,50,480000,420,25,"Engineering"],
    ["Madhya Pradesh","Gwalior","Gwalior",190,48,2026,7800,66,25,220000,600,14,"Engineering"]]
    return pd.DataFrame(rows,columns=["state","district","city","applications","admissions","year","pcm_students","school_count","coaching_count","marketing_spend","travel_km","competitor_count","programme"])

def score(df):
    d=df.copy()
    cols=["applications","admissions","pcm_students","school_count","coaching_count","marketing_spend","travel_km","competitor_count"]
    for c in cols:
        if c not in d: d[c]=0
        d[c]=pd.to_numeric(d[c],errors="coerce").fillna(0)
    d["conversion_rate"]=np.where(d.applications>0,d.admissions/d.applications,0)
    def norm(s):
        s=pd.to_numeric(s,errors="coerce").fillna(0)
        return (s-s.min())/(s.max()-s.min()) if s.max()!=s.min() else pd.Series(0,index=s.index)
    d["potential_score"]=100*(.25*norm(d.pcm_students)+.20*norm(d.applications)+.20*norm(d.conversion_rate)+.15*norm(d.school_count+.5*d.coaching_count)+.10*(1-norm(d.travel_km))+.10*(1-norm(d.competitor_count)))
    d["priority_zone"]=pd.cut(d.potential_score,[-.01,35,60,100.01],labels=["Exploratory","Develop","Priority"])
    d["baseline_admission_estimate"]=(d.applications*d.conversion_rate).round().astype(int)
    d["cost_per_admission"]=np.where(d.admissions>0,d.marketing_spend/d.admissions,np.nan)
    return d

st.sidebar.header("Data")
uploaded=st.sidebar.file_uploader("Upload COER admission history (CSV / Excel)",type=["csv","xlsx"])
use_demo=st.sidebar.toggle("Use illustrative demo data",value=uploaded is None)
if uploaded:
    raw=pd.read_csv(uploaded) if uploaded.name.lower().endswith(".csv") else pd.read_excel(uploaded)
elif use_demo: raw=demo_data()
else:
    st.info("Upload a COER CSV/XLSX file or enable demo data."); st.stop()
raw=normalize(raw)
missing=[c for c in REQUIRED if c not in raw.columns]
if missing:
    st.error("Missing required columns: "+", ".join(missing)); st.stop()
if "year" not in raw: raw["year"]=2026
data=score(raw)
st.sidebar.success(f"Loaded {len(data)} records")
st.sidebar.caption("Demo figures are fictional and are not COER University records.")
st.sidebar.header("Filters")
states=sorted(data.state.dropna().astype(str).unique())
selected=st.sidebar.multiselect("States / UTs",states,default=states)
v=data[data.state.astype(str).isin(selected)].copy()
if v.empty: st.warning("No data for selected filters."); st.stop()
a,b,c,d=st.columns(4)
a.metric("Locations",len(v)); b.metric("Applications",f"{int(v.applications.sum()):,}")
c.metric("Admissions",f"{int(v.admissions.sum()):,}")
d.metric("Conversion",f"{(v.admissions.sum()/v.applications.sum()*100 if v.applications.sum() else 0):.1f}%")
st.subheader("Geographic admission opportunity")
if {"latitude","longitude"}.issubset(v.columns):
    v["latitude"]=pd.to_numeric(v.latitude,errors="coerce"); v["longitude"]=pd.to_numeric(v.longitude,errors="coerce")
    m=v.dropna(subset=["latitude","longitude"])
    if not m.empty:
        fig=px.scatter_mapbox(m,lat="latitude",lon="longitude",size="applications",color="potential_score",hover_name="city",hover_data=["state","district","applications","admissions"],color_continuous_scale="RdYlGn",size_max=24,zoom=3,mapbox_style="open-street-map")
        st.plotly_chart(fig,use_container_width=True)
    else: st.info("No valid coordinate pairs found.")
else: st.info("Add latitude and longitude columns to enable the interactive map; coordinates are not guessed.")
t1,t2,t3,t4=st.tabs(["Zone ranking","Forecast & trends","Programme analysis","Data & methodology"])
with t1:
    r=v.sort_values("potential_score",ascending=False)
    st.dataframe(r[["state","district","city","applications","admissions","conversion_rate","potential_score","priority_zone","baseline_admission_estimate","cost_per_admission"]],use_container_width=True,hide_index=True,
    column_config={"conversion_rate":st.column_config.NumberColumn("Conversion",format="%.1%%"),"potential_score":st.column_config.NumberColumn("Potential score",format="%.1f"),"cost_per_admission":st.column_config.NumberColumn("Spend/admission",format="₹%.0f")})
    st.plotly_chart(px.bar(r.head(20),x="potential_score",y="city",color="priority_zone",orientation="h",hover_data=["state","district"]),use_container_width=True)
    st.download_button("Download ranked zones CSV",r.to_csv(index=False).encode("utf-8"),"coer_admission_zone_ranking.csv","text/csv")
with t2:
    yearly=v.groupby("year",as_index=False).agg(applications=("applications","sum"),admissions=("admissions","sum"))
    if yearly.year.nunique()>1: st.plotly_chart(px.line(yearly,x="year",y=["applications","admissions"],markers=True),use_container_width=True)
    else: st.info("Upload multiple admission years to see trends.")
    st.metric("Baseline admission estimate",f"{int(v.baseline_admission_estimate.sum()):,}")
    st.caption("Baseline = applications × observed conversion. This is not a trained ML forecast.")
with t3:
    if "programme" in v:
        p=v.groupby("programme",as_index=False).agg(applications=("applications","sum"),admissions=("admissions","sum"))
        p["conversion_rate"]=np.where(p.applications>0,p.admissions/p.applications,0)
        st.dataframe(p,use_container_width=True,hide_index=True)
        st.plotly_chart(px.bar(p,x="programme",y="applications",color="admissions"),use_container_width=True)
    else: st.info("Add a programme column for course-wise analysis.")
with t4:
    st.markdown("""
**Required columns:** `state, district, city, applications, admissions`

**Recommended:** `year, programme, pcm_students, school_count, coaching_count, marketing_spend, travel_km, competitor_count, latitude, longitude`.

**Explainable score weights:** student pool 25%, historical applications 20%, conversion 20%, school/coaching reach 15%, accessibility 10%, lower competition 10%. Scores are relative to the uploaded dataset and are planning indicators, not causal estimates.

**Forecasting:** current baseline uses observed conversion. A trained model requires 3–5 years of clean granular data and time-based validation.
""")
    tmpl=pd.DataFrame(columns=["state","district","city","applications","admissions","year","programme","pcm_students","school_count","coaching_count","marketing_spend","travel_km","competitor_count","latitude","longitude"])
    st.download_button("Download COER CSV template",tmpl.to_csv(index=False).encode("utf-8"),"coer_admission_data_template.csv","text/csv")
st.divider()
st.caption("COER Admission Intelligence AI | Prototype | Validate uploaded data and outputs before operational decisions.")
