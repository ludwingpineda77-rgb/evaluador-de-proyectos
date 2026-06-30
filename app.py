import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import matplotlib.pyplot as plt

# =========================
# CONFIGURACIÓN GENERAL
# =========================

st.set_page_config(
    page_title="Sistema de Evaluación Económica de Proyectos de Inversión",
    page_icon="📊",
    layout="wide"
)

# =========================
# FUNCIONES
# =========================

def calcular_payback(flujos):
    acumulado = 0
    for i in range(1, len(flujos)):
        acumulado_anterior = acumulado
        acumulado += flujos[i]

        if acumulado >= abs(flujos[0]):
            faltante = abs(flujos[0]) - acumulado_anterior
            fraccion = faltante / flujos[i]
            return (i - 1) + fraccion

    return None


def calcular_bc(beneficio_anual, mantenimiento_anual, inversion, rescate, tmar, vida):
    factor_pa = (1 - (1 + tmar) ** (-vida)) / tmar

    vp_beneficios = beneficio_anual * factor_pa + rescate / ((1 + tmar) ** vida)
    vp_costos = inversion + mantenimiento_anual * factor_pa

    relacion_bc = vp_beneficios / vp_costos

    return vp_beneficios, vp_costos, relacion_bc


def calcular_valor_anual(inversion, tmar, vida):
    factor_ap = (tmar * (1 + tmar) ** vida) / (((1 + tmar) ** vida) - 1)
    return inversion * factor_ap


def formato_moneda(valor):
    return f"${valor:,.2f}"


# =========================
# ENCABEZADO
# =========================

st.title("📊 Sistema de Evaluación Económica de Proyectos de Inversión")
st.markdown("""
Esta aplicación permite evaluar la viabilidad financiera de proyectos de inversión mediante herramientas de Ingeniería Económica.

Los resultados se obtienen utilizando indicadores como:

- Valor Presente Neto (VPN)
- Tasa Interna de Retorno (TIR)
- Relación Beneficio/Costo (B/C)
- Valor Anual
- Costo Anual de Recuperación de Capital
- Periodo de Recuperación
- Flujo de Efectivo
""")

st.divider()

# =========================
# SIDEBAR
# =========================

st.sidebar.header("📥 Datos del proyecto")

inversion = st.sidebar.number_input(
    "Inversión inicial ($)",
    min_value=0.0,
    value=95303.40,
    step=1000.0
)

beneficio_anual = st.sidebar.number_input(
    "Beneficio anual estimado ($)",
    min_value=0.0,
    value=47290.00,
    step=1000.0
)

mantenimiento = st.sidebar.number_input(
    "Costo anual de mantenimiento ($)",
    min_value=0.0,
    value=4500.00,
    step=500.0
)

rescate = st.sidebar.number_input(
    "Valor de rescate ($)",
    min_value=0.0,
    value=15000.00,
    step=1000.0
)

tmar_porcentaje = st.sidebar.number_input(
    "TMAR (%)",
    min_value=0.0,
    value=12.0,
    step=1.0
)

vida = st.sidebar.number_input(
    "Vida útil del proyecto (años)",
    min_value=1,
    value=5,
    step=1
)

tmar = tmar_porcentaje / 100
vida = int(vida)

# =========================
# CÁLCULOS
# =========================

flujo_neto = beneficio_anual - mantenimiento

flujos = [-inversion]

for anio in range(1, vida + 1):
    if anio == vida:
        flujos.append(flujo_neto + rescate)
    else:
        flujos.append(flujo_neto)

vpn = npf.npv(tmar, flujos)
tir = npf.irr(flujos)
tir_porcentaje = tir * 100 if tir is not None else 0

valor_anual = calcular_valor_anual(inversion, tmar, vida)
carc = valor_anual

vp_beneficios, vp_costos, relacion_bc = calcular_bc(
    beneficio_anual,
    mantenimiento,
    inversion,
    rescate,
    tmar,
    vida
)

payback = calcular_payback(flujos)

flujo_acumulado = np.cumsum(flujos)

tabla_flujos = pd.DataFrame({
    "Año": list(range(0, vida + 1)),
    "Flujo de efectivo": flujos,
    "Flujo acumulado": flujo_acumulado
})

# =========================
# RESULTADOS PRINCIPALES
# =========================

st.header("📌 Resultados principales")

col1, col2, col3, col4 = st.columns(4)

col1.metric("VPN", formato_moneda(vpn))
col2.metric("TIR", f"{tir_porcentaje:.2f}%")
col3.metric("Relación B/C", f"{relacion_bc:.2f}")
col4.metric("Payback", f"{payback:.2f} años" if payback else "No recupera")

col5, col6, col7 = st.columns(3)

col5.metric("Flujo neto anual", formato_moneda(flujo_neto))
col6.metric("Valor anual / CARC", formato_moneda(valor_anual))
col7.metric("TMAR", f"{tmar_porcentaje:.2f}%")

st.divider()

# =========================
# DIAGNÓSTICO
# =========================

st.header("🧠 Diagnóstico automático")

if vpn > 0 and tir > tmar and relacion_bc > 1 and payback is not None and payback < vida:
    st.success(
        "✅ El proyecto es financieramente viable. "
        "El VPN es positivo, la TIR supera la TMAR, la relación B/C es mayor a 1 "
        "y la inversión se recupera antes de finalizar la vida útil del proyecto."
    )
elif vpn > 0 and tir > tmar:
    st.warning(
        "⚠️ El proyecto presenta resultados favorables, aunque conviene revisar algunos indicadores complementarios."
    )
else:
    st.error(
        "❌ El proyecto no cumple completamente con los criterios financieros de aceptación."
    )

# =========================
# TABLAS
# =========================

st.header("📋 Flujo de efectivo proyectado")

st.dataframe(
    tabla_flujos.style.format({
        "Flujo de efectivo": "${:,.2f}",
        "Flujo acumulado": "${:,.2f}"
    }),
    use_container_width=True
)

st.subheader("📊 Resumen financiero")

tabla_resumen = pd.DataFrame({
    "Indicador": [
        "Inversión inicial",
        "Beneficio anual",
        "Costo anual de mantenimiento",
        "Flujo neto anual",
        "Valor de rescate",
        "TMAR",
        "VPN",
        "TIR",
        "Relación B/C",
        "Valor anual",
        "Costo anual de recuperación de capital",
        "Periodo de recuperación"
    ],
    "Resultado": [
        formato_moneda(inversion),
        formato_moneda(beneficio_anual),
        formato_moneda(mantenimiento),
        formato_moneda(flujo_neto),
        formato_moneda(rescate),
        f"{tmar_porcentaje:.2f}%",
        formato_moneda(vpn),
        f"{tir_porcentaje:.2f}%",
        f"{relacion_bc:.2f}",
        formato_moneda(valor_anual),
        formato_moneda(carc),
        f"{payback:.2f} años" if payback else "No recupera"
    ]
})

st.dataframe(tabla_resumen, use_container_width=True)

# =========================
# GRÁFICAS
# =========================

st.header("📈 Gráficas del proyecto")

col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("Flujo de efectivo anual")
    fig1, ax1 = plt.subplots()
    ax1.bar(tabla_flujos["Año"], tabla_flujos["Flujo de efectivo"])
    ax1.axhline(0)
    ax1.set_xlabel("Año")
    ax1.set_ylabel("Flujo de efectivo ($)")
    ax1.set_title("Flujo de efectivo anual")
    st.pyplot(fig1)

with col_g2:
    st.subheader("Flujo acumulado")
    fig2, ax2 = plt.subplots()
    ax2.plot(tabla_flujos["Año"], tabla_flujos["Flujo acumulado"], marker="o")
    ax2.axhline(0)
    ax2.set_xlabel("Año")
    ax2.set_ylabel("Flujo acumulado ($)")
    ax2.set_title("Recuperación acumulada de la inversión")
    st.pyplot(fig2)

# =========================
# EXPLICACIÓN METODOLÓGICA
# =========================

st.header("📚 Interpretación de indicadores")

st.markdown(
    f"""
    ### Valor Presente Neto (VPN)
    El VPN obtenido es **{formato_moneda(vpn)}**.  
    Si el VPN es mayor que cero, el proyecto genera valor económico.

    ### Tasa Interna de Retorno (TIR)
    La TIR obtenida es **{tir_porcentaje:.2f}%**.  
    Se compara contra la TMAR de **{tmar_porcentaje:.2f}%**.

    ### Relación Beneficio/Costo
    La relación B/C obtenida es **{relacion_bc:.2f}**.  
    Si es mayor que 1, los beneficios superan a los costos.

    ### Valor Anual y Costo Anual de Recuperación de Capital
    El valor anual equivalente es **{formato_moneda(valor_anual)}**.  
    Este monto representa la recuperación anual necesaria para amortizar la inversión inicial.

    ### Periodo de recuperación
    La inversión se recupera en aproximadamente **{payback:.2f} años**.
    """
)

# =========================
# ESCENARIO DEL PROYECTO ORIGINAL
# =========================

st.header("📌 Datos de ejemplo")

st.info("""
Los valores cargados inicialmente corresponden a un ejemplo de evaluación económica de un proyecto desarrollado en una empresa textíl.

Todos los parámetros pueden modificarse para analizar diferentes escenarios de inversión.
""")
st.divider()

st.caption("Aplicación desarrollada en Python con Streamlit para evaluación económica de proyectos.")
