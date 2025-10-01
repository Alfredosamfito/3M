import streamlit as st
import pandas as pd
import io
from barcode import EAN13
from barcode.writer import ImageWriter
from PIL import Image  # Importamos la librería para manejar imágenes

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Buscador Avanzado de Datos",
    page_icon="🔍",
    layout="wide",
)

# --- Encabezado con Logo ---
# Creamos dos columnas para poner el título a la izquierda y el logo a la derecha
# La primera columna es 3 veces más ancha que la segunda
col1, col2 = st.columns([3, 1])

with col1:
    st.title("🔍 Buscador REBUSS - 3M")
    st.markdown(
        "Escribe una o más palabras clave para buscar en la columna **'ABDESC'** de la base de datos.")

with col2:
    # Intentamos cargar y mostrar el logo
    try:
        logo = Image.open('logo.png')
        st.image(logo, width=200)  # Ajusta el 'width' según el tamaño deseado
    except FileNotFoundError:
        st.warning("No se encontró el archivo 'logo.png' en la carpeta raíz.")

st.markdown("---")

# --- Selección de Centro de Distribución ---
locations = {
    "Santa Isabel": "1299544230",
    "ENEA": "1200217273"
}
selected_location = st.selectbox(
    "Selecciona el Centro de Distribución:",
    options=list(locations.keys())
)
selected_gid = locations[selected_location]


# --- Función para Generar Código de Barras ---
def generate_barcode(folio):
    """Genera un código de barras EAN13 a partir de un folio y lo devuelve como una imagen en memoria."""
    try:
        # EAN13 necesita 12 dígitos para calcular el 13ro (dígito de control).
        # Rellenamos el folio con ceros a la izquierda hasta completar 12 dígitos.
        code = str(folio).zfill(12)

        # Generar el código de barras en un buffer de memoria para no crear archivos
        buffer = io.BytesIO()
        ean = EAN13(code, writer=ImageWriter())
        ean.write(buffer)
        return buffer
    except Exception:
        # Devuelve None si el folio no es válido para un código de barras (ej. contiene letras)
        return None

# --- Carga de Datos con Caché ---
# Se añade el parámetro 'gid' para cargar la hoja correcta


@st.cache_data
def load_data(gid):
    """Carga los datos desde la Google Sheet pública, según el GID seleccionado."""
    sheet_id = "1uga-VQ9UTr9lhMPe-VGjA581G2Fyjatt6bNB6JeEykk"
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    try:
        column_types = {
            "Folio Rebuss": str,
            "ABASSU": str,
            "ABDESC": str,
            "ABSER#": str,
        }
        columns_to_use = ["Folio Rebuss", "ABASSU", "ABDESC", "ABSER#"]
        df = pd.read_csv(sheet_url, usecols=columns_to_use,
                         dtype=column_types, header=5)
        df['search_col'] = df['ABDESC'].str.lower().fillna('')
        return df
    except Exception as e:
        st.error(
            f"Error al cargar los datos desde Google Sheets para {selected_location}: {e}")
        st.info("Verifica que el enlace de la hoja de cálculo sea correcto, público y que los encabezados estén en la fila 6.")
        return pd.DataFrame()


# Cargamos los datos pasando el GID seleccionado
df = load_data(selected_gid)

# --- Interfaz de Búsqueda ---
if not df.empty:
    search_query = st.text_input(
        "Ingresa tu búsqueda:",
        placeholder="Ej: motor de partida",
        help="Puedes buscar por una o varias palabras. La búsqueda encontrará filas que contengan TODAS las palabras que escribas."
    )

    # --- Lógica de Búsqueda y Visualización ---
    if search_query:
        keywords = search_query.lower().split()
        result_df = df[
            df['search_col'].apply(lambda x: all(
                keyword in x for keyword in keywords))
        ]

        st.subheader(
            f"Resultados de la Búsqueda: {len(result_df)} encontrados")

        if not result_df.empty:
            # Iteramos sobre los resultados para mostrarlos individualmente con su código de barras
            for index, row in result_df.iterrows():
                # Usamos un expander para mostrar cada resultado de forma ordenada
                with st.expander(f"Folio: {row['Folio Rebuss']} - {row['ABASSU']}"):
                    # Dividimos en dos columnas para datos y barcode
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown(f"**Folio Rebuss:** {row['Folio Rebuss']}")
                        st.markdown(f"**ABASSU:** {row['ABASSU']}")
                        st.markdown(f"**ABSER#:** {row['ABSER#']}")
                        st.markdown(
                            f"**Descripción (ABDESC):** {row['ABDESC']}")

                    with col2:
                        # Generar y mostrar el código de barras
                        barcode_image = generate_barcode(row['Folio Rebuss'])
                        if barcode_image:
                            # Se actualiza use_column_width a use_container_width según la advertencia
                            st.image(
                                barcode_image, caption=f"Código para {row['Folio Rebuss']}", use_container_width=True)
                        else:
                            st.warning(
                                "No se pudo generar el código de barras.")

        else:
            st.warning("No se encontraron resultados para tu búsqueda.")
    else:
        st.info("Esperando una consulta para mostrar los resultados.")
else:
    st.warning(
        f"No se pudieron cargar los datos para el centro '{selected_location}'.")

# --- Pie de Página ---
st.markdown("---")
st.markdown("Creado con ❤️ por ARB.")
