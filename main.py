import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import folium_static

st.set_page_config(page_title="SIVIRAM — Dashboard Demo", layout="wide", page_icon="🛡️")

# ══════════════════════════════════════
# ESTILOS
# ══════════════════════════════════════
st.markdown(
    """
<style>
    .block-container { padding-top: 1rem; }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1B3A5C 0%, #2E6B9E 100%);
        border-radius: 12px; padding: 16px 20px;
        color: white; border: none;
    }
    [data-testid="stMetric"] label { color: #B0C4DE !important; font-size: 0.85rem !important; }
    [data-testid="stMetric"] div[data-testid="stMetricValue"] { color: white !important; font-weight: 700 !important; }
</style>
""",
    unsafe_allow_html=True,
)


# ══════════════════════════════════════
# DATOS SIMULADOS
# ══════════════════════════════════════
@st.cache_data
def load_data():
    np.random.seed(42)

    departamentos = {
        "Antioquia": [
            ("Medellín", 6.25, -75.56),
            ("Envigado", 6.17, -75.58),
            ("Bello", 6.34, -75.55),
            ("Itagüí", 6.18, -75.61),
            ("Turbo", 7.99, -76.73),
        ],
        "Valle del Cauca": [
            ("Cali", 3.44, -76.54),
            ("Buenaventura", 3.88, -77.00),
            ("Palmira", 3.54, -76.30),
            ("Tuluá", 4.08, -76.20),
            ("Buga", 3.90, -76.30),
        ],
        "Cundinamarca": [
            ("Bogotá", 4.71, -74.07),
            ("Soacha", 4.59, -74.22),
            ("Zipaquirá", 5.02, -74.00),
            ("Fusagasugá", 4.34, -74.36),
            ("Girardot", 4.30, -74.80),
        ],
        "Santander": [
            ("Bucaramanga", 7.12, -73.12),
            ("Floridablanca", 7.07, -73.10),
            ("Barrancabermeja", 7.07, -73.85),
            ("Girón", 7.07, -73.17),
            ("Piedecuesta", 7.04, -73.23),
        ],
        "Atlántico": [
            ("Barranquilla", 10.97, -74.79),
            ("Soledad", 10.92, -74.77),
            ("Sabanalarga", 10.63, -74.92),
            ("Malambo", 10.86, -74.78),
            ("Santo Tomás", 10.76, -74.75),
        ],
    }

    antimicrobianos = [
        "Amoxicilina",
        "Ciprofloxacina",
        "Ceftriaxona",
        "Metronidazol",
        "Eritromicina",
        "Trimetoprima",
        "Gentamicina",
        "Vancomicina",
    ]

    registros = []
    for dep, mun_list in departamentos.items():
        for mun, lat, lon in mun_list:
            for sem in range(1, 53):
                for am in np.random.choice(antimicrobianos, 3, replace=False):
                    resistencia = np.clip(
                        np.random.beta(2, 5) * 100
                        + (15 if dep == "Atlántico" else 0)
                        + (10 if am in ["Ciprofloxacina", "Ceftriaxona"] else 0)
                        + np.random.normal(0, 5),
                        0,
                        100,
                    )

                    registros.append(
                        {
                            "departamento": dep,
                            "municipio": mun,
                            "lat": lat + np.random.normal(0, 0.02),
                            "lon": lon + np.random.normal(0, 0.02),
                            "semana": sem,
                            "antimicrobiano": am,
                            "resistencia_pct": round(resistencia, 1),
                            "precipitacion_mm": round(
                                max(
                                    0,
                                    np.random.normal(120, 60)
                                    + 40 * np.sin(sem * np.pi / 26),
                                ),
                                1,
                            ),
                            "temperatura_c": round(
                                22
                                + 5 * np.sin((sem - 15) * np.pi / 26)
                                + np.random.normal(0, 1.5),
                                1,
                            ),
                            "humedad_pct": round(
                                np.clip(
                                    75
                                    + 10 * np.sin(sem * np.pi / 26)
                                    + np.random.normal(0, 5),
                                    40,
                                    99,
                                ),
                                1,
                            ),
                            "densidad_ganadera": round(
                                max(0.5, np.random.lognormal(1.5, 0.8)), 1
                            ),
                            "consumo_antimicrobianos": round(
                                max(5, np.random.normal(28, 10)), 1
                            ),
                        }
                    )

    df = pd.DataFrame(registros)
    df["nivel_riesgo"] = pd.qcut(
        df["resistencia_pct"], q=4, labels=["Bajo", "Moderado", "Alto", "Muy alto"]
    )
    return df


df = load_data()

# ══════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════
with st.sidebar:
    st.title("🛡️ SIVIRAM")
    st.caption("Sistema de Vigilancia de Resistencia Antimicrobiana")
    st.divider()

    departamentos_sel = st.multiselect(
        "Departamento", df["departamento"].unique(), default=df["departamento"].unique()
    )
    semana_range = st.slider("Semana epidemiológica", 1, 52, (1, 52))
    antimicrobianos_sel = st.multiselect(
        "Antimicrobiano",
        df["antimicrobiano"].unique(),
        default=df["antimicrobiano"].unique(),
    )

# Filtrar
df_f = df[
    (df["departamento"].isin(departamentos_sel))
    & (df["semana"] >= semana_range[0])
    & (df["semana"] <= semana_range[1])
    & (df["antimicrobiano"].isin(antimicrobianos_sel))
]

# ══════════════════════════════════════
# HEADER + KPIs
# ══════════════════════════════════════
st.markdown("# 🛡️ SIVIRAM — Dashboard de Resistencia Antimicrobiana")
st.caption("Demo con datos simulados · Sistema Digital Integrado de Vigilancia de RAM")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Prevalencia resistencia", f"{df_f['resistencia_pct'].mean():.1f}%")
c2.metric("Máxima resistencia", f"{df_f['resistencia_pct'].max():.1f}%")
c3.metric("Precipitación promedio", f"{df_f['precipitacion_mm'].mean():.0f} mm")
c4.metric(
    "Consumo antimicrobianos", f"{df_f['consumo_antimicrobianos'].mean():.1f} DDD"
)
c5.metric("Municipios activos", f"{df_f['municipio'].nunique()}")

st.divider()

# ══════════════════════════════════════
# TABS
# ══════════════════════════════════════
tab_mapa, tab_tendencia, tab_corr, tab_shap = st.tabs(
    ["🗺️ Mapa de riesgo", "📈 Tendencias", "🔗 Correlaciones", "🧠 SHAP"]
)

# ── TAB 1: MAPA ──
with tab_mapa:
    col_map, col_info = st.columns([3, 2])

    with col_map:
        df_map = (
            df_f.groupby(["municipio", "departamento", "lat", "lon"])
            .agg(
                {
                    "resistencia_pct": "mean",
                    "precipitacion_mm": "mean",
                    "temperatura_c": "mean",
                    "densidad_ganadera": "mean",
                    "consumo_antimicrobianos": "mean",
                }
            )
            .reset_index()
        )
        df_map["nivel_riesgo"] = pd.qcut(
            df_map["resistencia_pct"],
            q=4,
            labels=["Bajo", "Moderado", "Alto", "Muy alto"],
        )

        colores = {
            "Bajo": "#4CAF50",
            "Moderado": "#FFC107",
            "Alto": "#FF9800",
            "Muy alto": "#F44336",
        }

        m = folium.Map(location=[4.5, -74.0], zoom_start=6, tiles="CartoDB positron")
        for _, row in df_map.iterrows():
            color = colores.get(row["nivel_riesgo"], "#999")
            popup = f"""<div style='font-family:Calibri;width:220px'>
                <b style='font-size:14px'>{row["municipio"]}</b><br>
                <span style='color:#666'>{row["departamento"]}</span><hr style='margin:4px 0'>
                <b>Riesgo:</b> <span style='color:{color};font-weight:bold'>{row["nivel_riesgo"]}</span><br>
                <b>Resistencia:</b> {row["resistencia_pct"]:.1f}%<br>
                <b>Precipitación:</b> {row["precipitacion_mm"]:.0f} mm<br>
                <b>Temperatura:</b> {row["temperatura_c"]:.1f}°C<br>
                <b>Densidad ganadera:</b> {row["densidad_ganadera"]:.1f} heads/km²<br>
                <b>Consumo AB:</b> {row["consumo_antimicrobianos"]:.1f} DDD
            </div>"""
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=max(6, row["resistencia_pct"] / 3),
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(popup, max_width=250),
            ).add_to(m)
        folium_static(m, width=700, height=450)

    with col_info:
        st.markdown("**Resumen de riesgo**")
        conteo = df_map["nivel_riesgo"].value_counts()
        fig_pie = px.pie(
            names=conteo.index,
            values=conteo.values,
            color=conteo.index,
            color_discrete_map=colores,
            hole=0.4,
        )
        fig_pie.update_layout(
            height=200,
            margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(orientation="h", y=-0.1),
        )
        fig_pie.update_traces(textinfo="percent+label", textfont_size=12)
        st.plotly_chart(fig_pie, width="stretch")

        st.markdown("**Top 5 municipios:**")
        for _, r in df_map.nlargest(5, "resistencia_pct").iterrows():
            st.markdown(
                f"🔴 **{r['municipio']}** ({r['departamento']}) — {r['resistencia_pct']:.1f}%"
            )

# ── TAB 2: TENDENCIAS ──
with tab_tendencia:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Tendencia semanal**")
        df_t = (
            df_f.groupby(["semana", "departamento"])
            .agg({"resistencia_pct": "mean"})
            .reset_index()
        )
        fig_t = px.line(
            df_t,
            x="semana",
            y="resistencia_pct",
            color="departamento",
            color_discrete_sequence=px.colors.qualitative.Set2,
            labels={
                "semana": "Semana",
                "resistencia_pct": "Resistencia %",
                "departamento": "",
            },
        )
        fig_t.update_layout(height=350, legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig_t, width="stretch")
    with c2:
        st.markdown("**Resistencia por antimicrobiano**")
        df_am = (
            df_f.groupby(["antimicrobiano", "departamento"])
            .agg({"resistencia_pct": "mean"})
            .reset_index()
        )
        fig_am = px.bar(
            df_am,
            x="antimicrobiano",
            y="resistencia_pct",
            color="departamento",
            barmode="group",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_am.update_layout(
            height=350, xaxis_tickangle=-45, legend=dict(orientation="h", y=-0.25)
        )
        st.plotly_chart(fig_am, width="stretch")

# ── TAB 3: CORRELACIONES ──
with tab_corr:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Matriz de correlación**")
        df_corr = df_f[
            [
                "resistencia_pct",
                "precipitacion_mm",
                "temperatura_c",
                "humedad_pct",
                "densidad_ganadera",
                "consumo_antimicrobianos",
            ]
        ].corr()
        fig_corr = px.imshow(
            df_corr, text_auto=".2f", color_continuous_scale="RdBu_r", aspect="auto"
        )
        fig_corr.update_layout(height=400)
        st.plotly_chart(fig_corr, width="stretch")
    with c2:
        st.markdown("**Resistencia vs Precipitación**")
        fig_s = px.scatter(
            df_f.sample(min(2000, len(df_f))),
            x="precipitacion_mm",
            y="resistencia_pct",
            color="departamento",
            opacity=0.5,
            trendline="ols",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_s.update_layout(height=400)
        st.plotly_chart(fig_s, width="stretch")

# ── TAB 4: SHAP ──
with tab_shap:
    st.markdown("**Interpretabilidad — Valores SHAP (simulados)**")

    shap_data = pd.DataFrame(
        {
            "Variable": [
                "Densidad ganadera",
                "Consumo antimicrobianos",
                "Precipitación",
                "Temperatura",
                "Humedad",
                "Cobertura salud",
                "Población",
            ],
            "SHAP": [0.32, 0.28, 0.15, 0.12, 0.08, -0.03, -0.02],
        }
    ).sort_values("SHAP")

    colors = ["#F44336" if v > 0 else "#4CAF50" for v in shap_data["SHAP"]]
    fig = go.Figure(
        go.Bar(
            x=shap_data["SHAP"],
            y=shap_data["Variable"],
            orientation="h",
            marker_color=colors,
            text=[f"{v:+.2f}" for v in shap_data["SHAP"]],
            textposition="outside",
        )
    )
    fig.update_layout(
        height=350,
        xaxis_title="Contribución al riesgo (SHAP)",
        xaxis=dict(zeroline=True, zerolinecolor="gray"),
    )
    st.plotly_chart(fig, width="stretch")

    c1, c2 = st.columns(2)
    c1.info("🔴 **Mayor densidad ganadera** → Mayor riesgo de resistencia")
    c2.info("🟢 **Mayor cobertura de salud** → Menor riesgo de resistencia")

# ══════════════════════════════════════
# ALERTAS
# ══════════════════════════════════════
st.divider()
st.markdown("## ⚠️ Alertas tempranas")

df_alert = df_map[df_map["nivel_riesgo"].isin(["Alto", "Muy alto"])].nlargest(
    8, "resistencia_pct"
)
for _, a in df_alert.iterrows():
    color = "#F44336" if a["nivel_riesgo"] == "Muy alto" else "#FF9800"
    icon = "🔴" if a["nivel_riesgo"] == "Muy alto" else "🟠"
    st.markdown(
        f"""
    <div style='background:{color}15;border-left:4px solid {color};padding:10px 16px;
    border-radius:0 8px 8px 0;margin:6px 0'>
        {icon} <b>{a["municipio"]}</b> ({a["departamento"]}) — Resistencia: <b>{a["resistencia_pct"]:.1f}%</b> · Nivel: <b>{a["nivel_riesgo"]}</b>
    </div>""",
        unsafe_allow_html=True,
    )

st.divider()
st.caption(
    "🛡️ SIVIRAM v1.0 — Demo · Datos simulados · One Health · PostgreSQL/PostGIS · Streamlit · ML"
)
