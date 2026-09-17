from pathlib import Path
import pandas as pd


# ============================================================
# CONFIGURACIÓN
# ============================================================

DATA_SRC = Path("data_src")
DATA_DST = Path("data_Dst")

# Crear carpeta de salida si no existe
DATA_DST.mkdir(parents=True, exist_ok=True)


# Titulaciones consideradas T de STEM en el estudio
CARRERAS_T = [
    "INGENIERÍA BIOMÉDICA",
    "INGENIERÍA EN INTELIGENCIA ARTIFICIAL",
    "INGENIERÍA EN SONIDO E IMAGEN EN TELECOMUNICACIÓN",
    "INGENIERÍA INFORMÁTICA",
    "INGENIERÍA MULTIMEDIA",
    "INGENIERÍA ROBÓTICA",
]


# ============================================================
# FUNCIÓN PARA LEER LOS EXCEL
# ============================================================

def cargar_datos(carpeta):
    """
    Lee todos los archivos .xlsx de una carpeta y los combina
    en un único DataFrame.

    Se utiliza la hoja 'cas' y se localiza automáticamente
    la fila donde comienza la tabla.

    Además, calcula el porcentaje de mujeres y hombres
    respecto al total de cada titulación.
    """

    dataframes = []

    for archivo in sorted(carpeta.glob("*.xlsx")):

        # ----------------------------------------------------
        # Leer inicialmente sin asumir dónde está la cabecera
        # ----------------------------------------------------

        df_raw = pd.read_excel(
            archivo,
            sheet_name="cas",
            header=None
        )

        # Buscar la fila que contiene "GRADOS"
        primera_columna = (
            df_raw.iloc[:, 0]
            .astype(str)
            .str.strip()
        )

        filas_cabecera = df_raw.index[
            primera_columna.str.upper() == "GRADOS"
        ]

        if len(filas_cabecera) == 0:
            print(
                f"AVISO: no se encontró la tabla "
                f"en {archivo.name}"
            )
            continue

        fila_cabecera = filas_cabecera[0]

        # ----------------------------------------------------
        # Leer de nuevo utilizando la cabecera encontrada
        # ----------------------------------------------------

        df = pd.read_excel(
            archivo,
            sheet_name="cas",
            header=fila_cabecera
        )

        # Estandarizar nombres de columnas
        df.columns = [
            "Titulacion",
            "Total",
            "Mujeres",
            "Hombres"
        ]

        # ----------------------------------------------------
        # Limpiar datos
        # ----------------------------------------------------

        # Eliminar fila TOTAL
        df = df[
            df["Titulacion"]
            .astype(str)
            .str.strip()
            .str.upper() != "TOTAL"
        ].copy()

        # Obtener curso del nombre del archivo
        # Ejemplo: 24-25.xlsx -> 24-25
        df["Curso"] = archivo.stem

        # Convertir columnas a numéricas
        for col in ["Total", "Mujeres", "Hombres"]:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

        # Limpiar nombres de titulaciones
        df["Titulacion"] = (
            df["Titulacion"]
            .astype(str)
            .str.strip()
        )

        # ----------------------------------------------------
        # Calcular porcentajes de mujeres y hombres
        # ----------------------------------------------------

        df["Porcentaje_Mujeres"] = (
            df["Mujeres"] / df["Total"] * 100
        ).round(2)

        df["Porcentaje_Hombres"] = (
            df["Hombres"] / df["Total"] * 100
        ).round(2)

        dataframes.append(df)

    # --------------------------------------------------------
    # Unir todos los cursos
    # --------------------------------------------------------

    if not dataframes:
        return pd.DataFrame(
            columns=[
                "Curso",
                "Titulacion",
                "Total",
                "Mujeres",
                "Hombres",
                "Porcentaje_Mujeres",
                "Porcentaje_Hombres"
            ]
        )

    df_final = pd.concat(
        dataframes,
        ignore_index=True
    )

    # Orden de columnas
    columnas = [
        "Curso",
        "Titulacion",
        "Total",
        "Mujeres",
        "Hombres",
        "Porcentaje_Mujeres",
        "Porcentaje_Hombres"
    ]

    return df_final[columnas]


# ============================================================
# FUNCIÓN PARA CALCULAR ESTADÍSTICAS DE GÉNERO
# ============================================================

def calcular_stats_genero(df):
    """
    Calcula estadísticas descriptivas de género para cada
    titulación utilizando todos los cursos disponibles.
    """

    resultados = []

    for titulacion, grupo in df.groupby("Titulacion"):

        # Ordenar cronológicamente
        grupo = grupo.sort_values("Curso")

        primer_curso = grupo.iloc[0]
        ultimo_curso = grupo.iloc[-1]

        # ----------------------------------------------------
        # Totales acumulados del periodo
        # ----------------------------------------------------

        total_periodo = grupo["Total"].sum()
        mujeres_periodo = grupo["Mujeres"].sum()
        hombres_periodo = grupo["Hombres"].sum()

        # ----------------------------------------------------
        # Porcentaje global ponderado
        # ----------------------------------------------------
        # No es lo mismo que la media de los porcentajes.
        # Aquí los cursos con más estudiantes tienen más peso.

        if total_periodo > 0:

            porcentaje_global_mujeres = (
                mujeres_periodo
                / total_periodo
                * 100
            )

            porcentaje_global_hombres = (
                hombres_periodo
                / total_periodo
                * 100
            )

        else:
            porcentaje_global_mujeres = float("nan")
            porcentaje_global_hombres = float("nan")

        # ----------------------------------------------------
        # Cambio entre primer y último curso
        # ----------------------------------------------------

        cambio_mujeres_pp = (
            ultimo_curso["Porcentaje_Mujeres"]
            - primer_curso["Porcentaje_Mujeres"]
        )

        cambio_hombres_pp = (
            ultimo_curso["Porcentaje_Hombres"]
            - primer_curso["Porcentaje_Hombres"]
        )

        # ----------------------------------------------------
        # Rango de representación femenina
        # ----------------------------------------------------

        rango_mujeres = (
            grupo["Porcentaje_Mujeres"].max()
            - grupo["Porcentaje_Mujeres"].min()
        )

        # ----------------------------------------------------
        # Crear fila de estadísticas
        # ----------------------------------------------------

        stats = {

            "Titulacion": titulacion,

            # Número de cursos analizados
            "Num_Cursos": len(grupo),

            # ----------------------------
            # Tamaño de la titulación
            # ----------------------------

            "Media_Total":
                grupo["Total"].mean(),

            "Total_Periodo":
                total_periodo,

            "Total_Mujeres_Periodo":
                mujeres_periodo,

            "Total_Hombres_Periodo":
                hombres_periodo,

            # ----------------------------
            # Media anual de porcentajes
            # ----------------------------

            "Media_Porcentaje_Mujeres":
                grupo["Porcentaje_Mujeres"].mean(),

            "Media_Porcentaje_Hombres":
                grupo["Porcentaje_Hombres"].mean(),

            # ----------------------------
            # Porcentaje global ponderado
            # ----------------------------

            "Porcentaje_Global_Mujeres":
                porcentaje_global_mujeres,

            "Porcentaje_Global_Hombres":
                porcentaje_global_hombres,

            # ----------------------------
            # Mínimos y máximos
            # ----------------------------

            "Min_Porcentaje_Mujeres":
                grupo["Porcentaje_Mujeres"].min(),

            "Max_Porcentaje_Mujeres":
                grupo["Porcentaje_Mujeres"].max(),

            "Min_Porcentaje_Hombres":
                grupo["Porcentaje_Hombres"].min(),

            "Max_Porcentaje_Hombres":
                grupo["Porcentaje_Hombres"].max(),

            # ----------------------------
            # Variabilidad
            # ----------------------------

            "DesvStd_Porcentaje_Mujeres":
                grupo["Porcentaje_Mujeres"].std(),

            "DesvStd_Porcentaje_Hombres":
                grupo["Porcentaje_Hombres"].std(),

            "Rango_Porcentaje_Mujeres":
                rango_mujeres,

            # ----------------------------
            # Primer curso
            # ----------------------------

            "Primer_Curso":
                primer_curso["Curso"],

            "Porcentaje_Mujeres_Primer_Curso":
                primer_curso["Porcentaje_Mujeres"],

            "Porcentaje_Hombres_Primer_Curso":
                primer_curso["Porcentaje_Hombres"],

            # ----------------------------
            # Último curso
            # ----------------------------

            "Ultimo_Curso":
                ultimo_curso["Curso"],

            "Porcentaje_Mujeres_Ultimo_Curso":
                ultimo_curso["Porcentaje_Mujeres"],

            "Porcentaje_Hombres_Ultimo_Curso":
                ultimo_curso["Porcentaje_Hombres"],

            # ----------------------------
            # Evolución en puntos porcentuales
            # ----------------------------

            "Cambio_Mujeres_pp":
                cambio_mujeres_pp,

            "Cambio_Hombres_pp":
                cambio_hombres_pp,
        }

        resultados.append(stats)

    # Convertir resultados a DataFrame
    df_stats = pd.DataFrame(resultados)

    # Redondear todas las columnas numéricas
    columnas_numericas = (
        df_stats
        .select_dtypes(include="number")
        .columns
    )

    df_stats[columnas_numericas] = (
        df_stats[columnas_numericas]
        .round(2)
    )

    return df_stats


# ============================================================
# 1. CARGAR DATOS
# ============================================================

df_matriculados = cargar_datos(
    DATA_SRC / "matricula"
)

df_graduados = cargar_datos(
    DATA_SRC / "graduacion"
)


# ============================================================
# 2. FILTRAR TITULACIONES T DE STEM
# ============================================================

df_matriculados_T = df_matriculados[
    df_matriculados["Titulacion"]
    .str.upper()
    .isin(CARRERAS_T)
].copy()

df_graduados_T = df_graduados[
    df_graduados["Titulacion"]
    .str.upper()
    .isin(CARRERAS_T)
].copy()


# ============================================================
# 3. ORDENAR LOS DATAFRAMES
# ============================================================

df_matriculados_T = (
    df_matriculados_T
    .sort_values(
        ["Curso", "Titulacion"]
    )
    .reset_index(drop=True)
)

df_graduados_T = (
    df_graduados_T
    .sort_values(
        ["Curso", "Titulacion"]
    )
    .reset_index(drop=True)
)


# ============================================================
# 4. CALCULAR ESTADÍSTICAS DE GÉNERO
# ============================================================

df_matriculados_stats = calcular_stats_genero(
    df_matriculados_T
)

df_graduados_stats = calcular_stats_genero(
    df_graduados_T
)


# ============================================================
# 5. GUARDAR CSV
# ============================================================

# Datos por curso
ruta_matriculados = (
    DATA_DST / "matriculados_T_STEM.csv"
)

ruta_graduados = (
    DATA_DST / "graduados_T_STEM.csv"
)

# Estadísticas globales
ruta_matriculados_stats = (
    DATA_DST / "matriculados_T_STEM_stats.csv"
)

ruta_graduados_stats = (
    DATA_DST / "graduados_T_STEM_stats.csv"
)


df_matriculados_T.to_csv(
    ruta_matriculados,
    index=False,
    encoding="utf-8-sig"
)

df_graduados_T.to_csv(
    ruta_graduados,
    index=False,
    encoding="utf-8-sig"
)

df_matriculados_stats.to_csv(
    ruta_matriculados_stats,
    index=False,
    encoding="utf-8-sig"
)

df_graduados_stats.to_csv(
    ruta_graduados_stats,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 6. MOSTRAR RESULTADOS POR PANTALLA
# ============================================================

print("\n" + "=" * 120)
print("MATRICULADOS - TITULACIONES T DE STEM")
print("=" * 120)

print(
    df_matriculados_T.to_string(index=False)
)


print("\n" + "=" * 120)
print("GRADUADOS - TITULACIONES T DE STEM")
print("=" * 120)

print(
    df_graduados_T.to_string(index=False)
)


print("\n" + "=" * 120)
print("ESTADÍSTICAS DE GÉNERO - MATRICULADOS")
print("=" * 120)

print(
    df_matriculados_stats.to_string(index=False)
)


print("\n" + "=" * 120)
print("ESTADÍSTICAS DE GÉNERO - GRADUADOS")
print("=" * 120)

print(
    df_graduados_stats.to_string(index=False)
)


# ============================================================
# 7. MOSTRAR ARCHIVOS GENERADOS
# ============================================================

print("\n" + "=" * 120)
print("ARCHIVOS GENERADOS")
print("=" * 120)

print(ruta_matriculados)
print(ruta_graduados)
print(ruta_matriculados_stats)
print(ruta_graduados_stats)