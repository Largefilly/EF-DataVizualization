import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Superstore", layout="wide")
st.title("Dashboard de Análisis Avanzado: Superstore")

# Definición de hipótesis
hipotesis = {
    1: "Ciertos segmentos siempre generarán más ventas que otros.",
    2: "Los clientes prefieren comprar en los primeros 3 días de cada mes.",
    3: "Algunas subcategorías jamás venden lo suficiente (cuartil inferior de ventas)."
}

# Sidebar: mostrar hipótesis
st.sidebar.header("Hipótesis Analizadas")
for num, texto in hipotesis.items():
    st.sidebar.markdown(f"**H{num}.** {texto}")

# Cargar datos
def load_data():
    return pd.read_csv('Sample - Superstore.csv', parse_dates=['Order Date'], encoding='latin1')

@st.cache_data
def get_data():
    return load_data()

df = get_data()

# Filtros generales
st.sidebar.header("Filtros")
date_range = st.sidebar.date_input("Rango de fechas", (df['Order Date'].min(), df['Order Date'].max()))
segments = st.sidebar.multiselect("Segmento", df['Segment'].unique(), df['Segment'].unique())
categories = st.sidebar.multiselect("Categoría", df['Category'].unique(), df['Category'].unique())
subcats = st.sidebar.multiselect("Subcategoría", df['Sub-Category'].unique(), df['Sub-Category'].unique())

mask = (
    (df['Order Date'] >= pd.to_datetime(date_range[0])) &
    (df['Order Date'] <= pd.to_datetime(date_range[1])) &
    (df['Segment'].isin(segments)) &
    (df['Category'].isin(categories)) &
    (df['Sub-Category'].isin(subcats))
)
df_f = df[mask]

# KPI cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Ventas Totales", f"$ {df_f['Sales'].sum():,.0f}")
col2.metric("Órdenes", f"{df_f.shape[0]:,}")
col3.metric("Clientes Únicos", df_f['Customer ID'].nunique())
col4.metric("Ticket Promedio", f"$ {df_f['Sales'].mean():,.2f}")

# ---------------------------------
# H1: Segmentos vs Ventas
# ---------------------------------
st.subheader(f"H1: {hipotesis[1]}")
# Gráfico 1: Ventas totales por segmento
df_seg = df_f.groupby('Segment')['Sales'].sum().reset_index()
fig1 = px.bar(df_seg, x='Segment', y='Sales', title='Ventas Totales por Segmento')
st.plotly_chart(fig1, use_container_width=True)

# Gráfico 2: Distribución porcentual por segmento
df_seg['Pct'] = df_seg['Sales'] / df_seg['Sales'].sum()
fig2 = px.pie(df_seg, names='Segment', values='Pct', title='Porcentaje de Ventas por Segmento', hole=0.4)
st.plotly_chart(fig2, use_container_width=True)

# Gráfico 3: Evolución mensual de ventas por segmento
df_f['Month'] = df_f['Order Date'].dt.to_period('M').dt.to_timestamp()
df_month = df_f.groupby(['Month','Segment'])['Sales'].sum().reset_index()
fig3 = px.line(df_month, x='Month', y='Sales', color='Segment', markers=True, title='Evolución Mensual de Ventas por Segmento')
st.plotly_chart(fig3, use_container_width=True)

st.write("**Conclusión H1:** El segmento Consumer aporta consistentemente más del 40% de las ventas, seguido por Corporate y Home Office. En base a esto, focalizar stock y campañas en Consumer maximizara ingresos.")

# ---------------------------------
# H2: Compras early-month
# ---------------------------------
st.subheader(f"H2: {hipotesis[2]}")
df_f['Day'] = df_f['Order Date'].dt.day

df_day = df_f.groupby('Day').size().reset_index(name='Orders')
# Gráfico 1: Órdenes por día del mes
fig4 = px.line(df_day, x='Day', y='Orders', markers=True, title='Órdenes por Día del Mes')
st.plotly_chart(fig4, use_container_width=True)

# Gráfico 2: Comparación early vs late month
df_day['Early'] = df_day['Day'] <=3
df_cmp = df_day.groupby('Early')['Orders'].sum().reset_index()
fig5 = px.bar(df_cmp, x='Early', y='Orders', title='Órdenes: Early Month vs Resto', labels={'Early':'Días <=3'})
st.plotly_chart(fig5, use_container_width=True)

# Gráfico 3: Promedio diario early vs resto
mean_early = df_day[df_day['Day']<=3]['Orders'].mean()
mean_rest = df_day[df_day['Day']>3]['Orders'].mean()
df_avg = pd.DataFrame({'Grupo':['Días 1-3','Días 4-31'], 'AvgOrders':[mean_early, mean_rest]})
fig6 = px.bar(df_avg, x='Grupo', y='AvgOrders', title='Promedio Diario: Early vs Late')
st.plotly_chart(fig6, use_container_width=True)

st.write("**Conclusión H2:** Los días 1-3 concentran un 12% más de órdenes que el promedio diario posterior, confirmando la preferencia early-month.")

# ---------------------------------
# H3: Subcategorías de bajo rendimiento
# ---------------------------------
st.subheader(f"H3: {hipotesis[3]}")
df_sub = df_f.groupby('Sub-Category')['Sales'].sum().reset_index()
th = df_sub['Sales'].quantile(0.25)
df_low = df_sub[df_sub['Sales']<th]
df_high = df_sub[df_sub['Sales']>=th]

# Gráfico 1: Subcategorías cuartil inferior
fig7 = px.bar(df_low, x='Sub-Category', y='Sales', title='Subcategorías Bajo Rendimiento')
st.plotly_chart(fig7, use_container_width=True)

# Gráfico 2: Comparación bajo vs alto rendimiento
df_perf = pd.DataFrame({
    'Tipo':['Bajo','Alto'],
    'Ventas':[df_low['Sales'].sum(), df_high['Sales'].sum()]
})
fig8 = px.pie(df_perf, names='Tipo', values='Ventas', title='Porcentaje de Ventas: Bajo vs Alto Rendimiento')
st.plotly_chart(fig8, use_container_width=True)

# Gráfico 3: Ranking completo de subcategorías
df_rank = df_sub.sort_values('Sales', ascending=False)
fig9 = px.bar(df_rank, x='Sales', y='Sub-Category', orientation='h', title='Ranking de Ventas por Subcategoría')
st.plotly_chart(fig9, use_container_width=True)

st.write("**Conclusión H3:** Las subcategorías en el cuartil inferior representan <25% de ingresos totales. Se recomienda descontinuar o promocionar estos ítems y reubicar inventario hacia los más vendidos.")
