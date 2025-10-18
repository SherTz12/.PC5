
import os
import requests
import zipfile
import pandas as pd
from pymongo import MongoClient 

url = "https://netsg.cs.sfu.ca/youtubedata/0303.zip"
carpeta_salida = "datos_youtube"
os.makedirs(carpeta_salida, exist_ok=True)
nombre_zip = os.path.join(carpeta_salida, "0303.zip")

print(f"Descargando archivo desde: {url}")
response = requests.get(url)
if response.status_code == 200:
    with open(nombre_zip, "wb") as f:
        f.write(response.content)
    print(f"Archivo descargado: {nombre_zip}")
else:
    raise Exception("Error al descargar el archivo ZIP.")

print("Descomprimiendo archivo...")
with zipfile.ZipFile(nombre_zip, 'r') as zip_ref:
    zip_ref.extractall(carpeta_salida)
print(f"Archivos extraídos en: {carpeta_salida}")

archivos_txt = []
for root, _, files in os.walk(carpeta_salida):
    for f in files:
        if f.endswith(".txt") and f != "log.txt":
            archivos_txt.append(os.path.join(root, f))

if not archivos_txt:
    raise FileNotFoundError("No se encontraron archivos .txt dentro del ZIP.")

print("\nArchivos encontrados dentro del ZIP:")
for a in archivos_txt:
    print("-", a)

# Combinar todos los .txt
df_list = [pd.read_csv(a, sep="\t", header=None, low_memory=False, encoding="latin1") for a in archivos_txt]
df = pd.concat(df_list, ignore_index=True)
print(f"\nArchivos combinados. Total de filas: {len(df)}")

# Asignar nombres de columnas
columnas = [
    "video_id", "uploader", "age", "category", "length", "views",
    "rate", "ratings", "comments", "related_ids",
] + [f"extra_{i}" for i in range(len(df.columns) - 10)]

df.columns = columnas[:len(df.columns)]

# Limpieza y filtrado

# Convertir views a número y eliminar filas inválidas
df["views"] = pd.to_numeric(df["views"], errors="coerce")
df = df.dropna(subset=["views"])
df["views"] = df["views"].astype(int)

# Filtrar categorías de interés
categorias_interes = ["Music", "Entertainment", "Comedy", "Sports"]
df_filtrado = df[df["category"].isin(categorias_interes)]

# Filtrar solo videos con más de 100,000 vistas
df_filtrado = df_filtrado[df_filtrado["views"] > 100000]

df_filtrado = df_filtrado[["video_id", "age", "category", "views", "rate"]]

print(f"Datos filtrados y columnas seleccionadas. Total filas: {len(df_filtrado)}")

# Exportar a MongoDB Atlas
try:
    client = MongoClient(
        "mongodb+srv://SHERTZ:awza8a76cpwmkklB@cluster0.geynzxj.mongodb.net/",
        tls=True,
        tlsAllowInvalidCertificates=True,
        serverSelectionTimeoutMS=10000
    )
    
    client.server_info()
    db = client["youtube_db"]
    coleccion = db["videos0303"]

    if not df_filtrado.empty:
        coleccion.insert_many(df_filtrado.to_dict("records"))
        print("Datos exportados correctamente a MongoDB Atlas.")
    else:
        print("⚠ No hay datos para exportar (0 registros con más de 100k vistas).")

except Exception as e:
    print(f"Error al conectar o exportar a MongoDB Atlas: {e}")

# Exportar a CSV
csv_salida = os.path.join(carpeta_salida, "youtube_filtrado.csv")
df_filtrado.to_csv(csv_salida, index=False, encoding="utf-8")
print(f"Archivo CSV listo: {csv_salida}")
























