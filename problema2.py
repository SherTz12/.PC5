import pandas as pd
import sqlite3
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

os.makedirs('reportes', exist_ok=True)

df = pd.read_csv('data/winemag-data-130k-v2.csv', index_col=0)

print("\n--- EXPLORACIÓN INICIAL ---")
print("Dimensiones:", df.shape)
print("\nColumnas originales:", df.columns.tolist())
print("\nInformación general:")
print(df.info())
print("\nValores faltantes por columna:\n", df.isnull().sum().head())

# RENOMBRAR COLUMNAS

df = df.rename(columns={
    'country': 'pais',
    'description': 'descripcion',
    'points': 'puntuacion',
    'price': 'precio',
    'province': 'provincia',
    'region_1': 'region1',
    'region_2': 'region2',
    'variety': 'variedad',
    'winery': 'bodega',
    'designation': 'denominacion'
})

print("\nColumnas renombradas:", df.columns.tolist())

# CREACIÓN DE NUEVAS COLUMNAS

def clasificar_calidad(puntos):
    if puntos >= 95:
        return "Excelente"
    elif puntos >= 85:
        return "Bueno"
    elif puntos >= 75:
        return "Regular"
    else:
        return "Bajo"

df['clasificacion_calidad'] = df['puntuacion'].apply(clasificar_calidad)

def clasificar_precio(precio):
    if pd.isna(precio):
        return "Desconocido"
    elif precio > 100:
        return "Alto"
    elif precio > 40:
        return "Medio"
    else:
        return "Bajo"

df['categoria_precio'] = df['precio'].apply(clasificar_precio)
df['longitud_descripcion'] = df['descripcion'].apply(lambda x: len(str(x)))

# ASIGNAR CONTINENTE SEGÚN PAÍS
continentes = {
    'US': 'América', 'France': 'Europa', 'Italy': 'Europa', 'Spain': 'Europa',
    'Portugal': 'Europa', 'Chile': 'América', 'Argentina': 'América',
    'Australia': 'Oceanía', 'New Zealand': 'Oceanía', 'South Africa': 'África',
    'Germany': 'Europa', 'Austria': 'Europa', 'Canada': 'América'
}

df['continente'] = df['pais'].map(continentes).fillna('Desconocido')

# REPORTES

# Promedio de precio y cantidad de reviews por país
reporte1 = df.groupby('pais').agg(
    promedio_precio=('precio', 'mean'),
    cantidad_reviews=('puntuacion', 'count')
).sort_values(by='promedio_precio', ascending=False)
reporte1.to_csv('reportes/reporte1_precio_reviews.csv')

# Mejores vinos por continente (top 3 por continente)
reporte2 = df.sort_values(['continente', 'puntuacion'], ascending=[True, False]).groupby('continente').head(3)
reporte2.to_excel('reportes/reporte2_mejores_vinos.xlsx', index=False)

# Promedio de puntuación y precio según categoría de precio
reporte3 = df.groupby('categoria_precio')[['puntuacion', 'precio']].mean().sort_values('puntuacion', ascending=False)
conn = sqlite3.connect('reportes/datos_vinos.db')
reporte3.to_sql('reporte_categoria_precio', conn, if_exists='replace', index=True)
conn.close()

# Promedio de longitud de descripción según calidad
reporte4 = df.groupby('clasificacion_calidad')['longitud_descripcion'].mean().reset_index()
reporte4.to_json('reportes/reporte4_longitud_descripcion.json', orient='records')

# RESUMEN FINAL
print("\n--- RESUMEN FINAL ---")
print(f"Total de registros analizados: {len(df)}")
print(f"Países analizados: {df['pais'].nunique()}")
print(f"Continentes identificados: {df['continente'].nunique()}")
print("\nSe generaron 4 reportes en la carpeta 'reportes/' con formatos CSV, Excel, SQLite y JSON.")
print("\nEjecución completada exitosamente")

# 
# ENVÍO DE CORREO 
sender_email = "sherobrecub@gmail.com"
sender_password = open("token.txt").read().strip()
receiver_email = "0443212015@unjfsc.edu.pe"

message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email
message["Subject"] = "Reporte de análisis de vinos"

body = """Hola,

Te envío los reportes generados automáticamente del análisis de datos de vinos.

Saludos,
Sher
"""

message.attach(MIMEText(body, "plain"))

archivos = [
    "reportes/reporte1_precio_reviews.csv",
    "reportes/reporte2_mejores_vinos.xlsx",
    "reportes/datos_vinos.db",
    "reportes/reporte4_longitud_descripcion.json"
]

for archivo in archivos:
    if not os.path.exists(archivo):
        print(f"Archivo no encontrado: {archivo}")
        continue
    with open(archivo, "rb") as adj:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(adj.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(archivo)}")
    message.attach(part)

try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)
        print("Correo enviado con éxito.")
except Exception as e:
    print(f"Error al enviar el correo: {e}")

