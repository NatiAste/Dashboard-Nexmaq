import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Precios Competitivos",
    page_icon="💰",
    layout="wide"
)

# Título principal
st.title("🎯 Dashboard de Análisis de Precios Competitivos")

# Función para cargar datos
@st.cache_data
def load_data(file):
    """Carga el archivo Excel o CSV"""
    try:
        if file.name.endswith('.xlsx'):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        return None

# Sidebar para cargar archivo
st.sidebar.header("📁 Carga de Datos")
uploaded_file = st.sidebar.file_uploader(
    "Sube tu archivo de precios (CSV o Excel)",
    type=['csv', 'xlsx']
)

if uploaded_file is not None:
    # Cargar datos
    df = load_data(uploaded_file)
    
    if df is not None:
        st.sidebar.success(f"✅ Archivo cargado: {len(df)} productos")
        
        # Mostrar las columnas disponibles
        st.sidebar.write("**Columnas detectadas:**")
        st.sidebar.write(df.columns.tolist())
        
        # Configuración de columnas
        st.sidebar.header("⚙️ Configuración")
        
        # Detectar automáticamente columnas de precio (contienen números)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Selector de columna de SKU/Producto
        sku_col = st.sidebar.selectbox(
            "Columna de SKU/Producto",
            df.columns.tolist(),
            index=0
        )
        
        # Selector de columna de nombre de producto (opcional)
        producto_cols = [col for col in df.columns if col != sku_col]
        nombre_col = st.sidebar.selectbox(
            "Columna de Nombre del Producto",
            ["Ninguna"] + producto_cols,
            index=1 if len(producto_cols) > 0 else 0
        )
        
        # Selector de columna de tu precio
        mi_precio_col = st.sidebar.selectbox(
            "Columna de TU PRECIO",
            numeric_cols,
            index=0 if len(numeric_cols) > 0 else 0
        )
        
        # Selectores múltiples para competidores
        competidor_cols = st.sidebar.multiselect(
            "Columnas de PRECIOS COMPETIDORES",
            [col for col in numeric_cols if col != mi_precio_col],
            default=[col for col in numeric_cols if col != mi_precio_col][:3]
        )
        
        # Umbral de diferencia para marcar en rojo
        umbral = st.sidebar.slider(
            "Umbral de alerta (% más caro que competencia)",
            min_value=0,
            max_value=50,
            value=5,
            step=1,
            help="Productos que estés vendiendo X% más caro se marcarán en rojo"
        )
        
        # Procesamiento de datos
        if competidor_cols:
            # Calcular el precio mínimo de la competencia
            df['Precio_Min_Competencia'] = df[competidor_cols].min(axis=1)
            
            # Calcular diferencia porcentual
            df['Diferencia_%'] = ((df[mi_precio_col] - df['Precio_Min_Competencia']) / df['Precio_Min_Competencia'] * 100).round(2)
            
            # Marcar productos con alerta
            df['Alerta'] = df['Diferencia_%'] > umbral
            
            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_productos = len(df)
                st.metric("📦 Total Productos", total_productos)
            
            with col2:
                productos_caros = df['Alerta'].sum()
                st.metric("🔴 Productos Más Caros", productos_caros)
            
            with col3:
                productos_competitivos = len(df[df['Diferencia_%'] <= 0])
                st.metric("🟢 Productos Competitivos", productos_competitivos)
            
            with col4:
                precio_promedio = df[mi_precio_col].mean()
                st.metric("💵 Precio Promedio", f"${precio_promedio:,.0f}")
            
            # Filtros
            st.subheader("🔍 Filtros")
            col_f1, col_f2 = st.columns(2)
            
            with col_f1:
                filtro_alerta = st.selectbox(
                    "Filtrar por estado",
                    ["Todos", "Solo productos más caros", "Solo productos competitivos"]
                )
            
            with col_f2:
                if nombre_col != "Ninguna":
                    buscar_producto = st.text_input("Buscar producto por nombre")
                else:
                    buscar_producto = ""
            
            # Aplicar filtros
            df_filtrado = df.copy()
            
            if filtro_alerta == "Solo productos más caros":
                df_filtrado = df_filtrado[df_filtrado['Alerta'] == True]
            elif filtro_alerta == "Solo productos competitivos":
                df_filtrado = df_filtrado[df_filtrado['Alerta'] == False]
            
            if buscar_producto and nombre_col != "Ninguna":
                df_filtrado = df_filtrado[df_filtrado[nombre_col].str.contains(buscar_producto, case=False, na=False)]
            
            # Tabla de productos con formato
            st.subheader("📊 Detalle de Productos")
            
            # Preparar columnas para mostrar
            cols_mostrar = [sku_col]
            if nombre_col != "Ninguna":
                cols_mostrar.append(nombre_col)
            cols_mostrar.extend([mi_precio_col, 'Precio_Min_Competencia', 'Diferencia_%'])
            cols_mostrar.extend(competidor_cols)
            
            # Crear DataFrame para mostrar
            df_display = df_filtrado[cols_mostrar].copy()
            
            # Función para colorear filas
            def highlight_rows(row):
                if row['Diferencia_%'] > umbral:
                    return ['background-color: #ffcccc'] * len(row)
                elif row['Diferencia_%'] <= 0:
                    return ['background-color: #ccffcc'] * len(row)
                else:
                    return [''] * len(row)
            
            # Aplicar estilo
            styled_df = df_display.style.apply(highlight_rows, axis=1)
            
            # Formatear columnas numéricas
            format_dict = {}
            for col in [mi_precio_col, 'Precio_Min_Competencia'] + competidor_cols:
                format_dict[col] = "${:,.0f}"
            format_dict['Diferencia_%'] = "{:.2f}%"
            
            styled_df = styled_df.format(format_dict)
            
            st.dataframe(styled_df, use_container_width=True, height=400)
            
            # Descargar resultados
            st.subheader("💾 Exportar Resultados")
            
            # Convertir a CSV
            csv = df_filtrado.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="📥 Descargar análisis completo (CSV)",
                data=csv,
                file_name=f'analisis_precios_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv',
            )
            
            # Información adicional
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 📌 Leyenda")
            st.sidebar.markdown("🔴 **Rojo**: Precio más alto que competencia")
            st.sidebar.markdown("🟢 **Verde**: Precio competitivo")
            st.sidebar.markdown("⚪ **Blanco**: Dentro del umbral aceptable")
            
        else:
            st.warning("⚠️ Por favor selecciona al menos una columna de competidor")
    
else:
    # Instrucciones cuando no hay archivo
    st.info("""
    👋 **Bienvenido al Dashboard de Análisis de Precios**
    
    Para comenzar:
    1. Sube tu archivo CSV o Excel usando el panel lateral
    2. Configura las columnas correspondientes
    3. Ajusta el umbral de alerta según tus necesidades
    
    El dashboard identificará automáticamente los productos donde estás vendiendo más caro que la competencia.
    """)
    
    # Mostrar ejemplo de estructura esperada
    st.subheader("📋 Ejemplo de estructura de archivo")
    
    ejemplo_df = pd.DataFrame({
        'SKU': ['PROD001', 'PROD002', 'PROD003'],
        'Producto': ['Producto A', 'Producto B', 'Producto C'],
        'Mi_Precio': [100, 250, 450],
        'Competidor_1': [95, 260, 420],
        'Competidor_2': [98, 245, 440],
        'Competidor_3': [102, 255, 435]
    })
    
    st.dataframe(ejemplo_df, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("💡 **Tip**: Actualiza tu archivo y vuelve a cargarlo para ver los cambios en tiempo real")