import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

## INDICADORES
## Comparar emisiones de co2 con energías renovables



###############################################################################
#                      CONFIGURACIÓN GENERAL DE LA APLICACIÓN                 #
###############################################################################

st.set_page_config(
    page_title='ODS 7 en Mapas',
    layout='centered',
    initial_sidebar_state='collapsed'
)

st.markdown(
    '''
    <style>
        .block-container {
            max-width: 1200px;
        }
    </style>
    ''',
    unsafe_allow_html=True
)

###############################################################################
#                 MAPA DE INDICADORES ↔ ARCHIVOS DE EXCEL                     #
###############################################################################

INDICADORES = {
    'Emisiones de CO₂ totales (kt)': {
        'archivo': 'data/EmCO2Tot.xlsx',
        'nombre_valor': 'emisiones_co2_totales'
    },
    'PIB per cápita (USD constantes)': {
        'archivo': 'data/GDPercap.xlsx',
        'nombre_valor': 'pib_per_capita'
    },
    'Participación de energías renovables (% consumo final)': {
        'archivo': 'data/RenEnergy.xlsx',
        'nombre_valor': 'participacion_renovables'
    },
    'Acceso a la electricidad (% de la población)': {
        'archivo': 'data/AccesElec.xlsx',
        'nombre_valor': 'acceso_electricidad'
    },
    'Uso de combustibles limpios para cocinar (% de la población)': {
        'archivo': 'data/CleanFuelxCK.xlsx',
        'nombre_valor': 'combustibles_limpios_cocinar'
    },
    'Crecimiento poblacional (% anual)': {
        'archivo': 'data/PopGrow.xlsx',
        'nombre_valor': 'crecimiento_poblacional'
    }
}

###############################################################################
#                         FUNCIONES AUXILIARES                                #
###############################################################################

def cargar_indicador_wdi(ruta_archivo, nombre_valor):
    '''
    Carga un archivo WDI (formato de columnas tipo 'Y2000', 'Y2001', etc.)
    y lo pasa a formato largo.

    Columnas de salida:
    - 'country_name'
    - 'country_code'
    - 'year'
    - <nombre_valor>
    '''
    # Leer el archivo .xlsx
    df_original = pd.read_excel(ruta_archivo)

    # Verificar columnas clave según el formato real de los archivos
    if 'CountryName' not in df_original.columns or 'CountryCode' not in df_original.columns:
        raise KeyError(
            f'El archivo {ruta_archivo} debe contener las columnas '
            f'"CountryName" y "CountryCode".'
        )

    # Detectar columnas de años: nombres de la forma 'Y2000', 'Y2001', ...
    columnas_anio = []
    for columna in df_original.columns:
        if isinstance(columna, str) and columna.startswith('Y') and columna[1:].isdigit():
            columnas_anio.append(columna)

    if not columnas_anio:
        raise ValueError(
            f'No se encontraron columnas de años tipo "Yxxxx" en {ruta_archivo}. '
            f'Revisa el formato del archivo.'
        )

    # Ordenar las columnas de años por el año numérico
    columnas_anio = sorted(columnas_anio, key=lambda x: int(x[1:]))

    # Pasar a formato largo
    df_largo = df_original.melt(
        id_vars=['CountryName', 'CountryCode'],
        value_vars=columnas_anio,
        var_name='year',
        value_name=nombre_valor
    )

    # Convertir 'Y2000' → 2000 (int)
    df_largo['year'] = df_largo['year'].str[1:].astype(int)

    # Renombrar columnas para uso interno uniforme
    df_largo = df_largo.rename(
        columns={
            'CountryName': 'country_name',
            'CountryCode': 'country_code'
        }
    )
    # Filtrar solo países (códigos de 3 letras)
    df_largo = df_largo[df_largo['country_code'].astype(str).str.len() == 3]

    # Filtrar años recientes (por ejemplo, desde 2000)
    df_largo = df_largo[df_largo['year'] >= 2000]

    # Eliminar filas sin datos
    df_largo = df_largo.dropna(subset=[nombre_valor])

    return df_largo


def obtener_df_indicador(nombre_indicador):
    '''
    Carga un indicador concreto, según el diccionario INDICADORES.
    '''
    info_indicador = INDICADORES[nombre_indicador]
    return cargar_indicador_wdi(info_indicador['archivo'], info_indicador['nombre_valor'])


def obtener_nombre_columna_valor(nombre_indicador):
    return INDICADORES[nombre_indicador]['nombre_valor']


###############################################################################
#                          ENCABEZADO / PORTADA                               #
###############################################################################

st.markdown('<a id="inicio"></a><br><br>', unsafe_allow_html=True)

st.image('img/encabezado.jpg')
st.html('<h2 style="color:#3D6E85;">Dashboard: ODS 7 en Mapas</h2>')
st.caption(
    'Aplicación prototipo basada en indicadores del Banco Mundial (WDI) '
    'para analizar el ODS 7 y la transición energética.'
)

###############################################################################
#                    SECCIÓN 1: ACERCA DE LOS DATOS                           #
###############################################################################

st.markdown('<a id="ruta-metodologica"></a><br><br>', unsafe_allow_html=True)
with st.container(border=True):
    with st.expander('Ver RUTA METODOLÓGICA'):
        tab1, tab2, tab3, tab4 = st.tabs(['ANTECEDENTES', 'MARCO CONCEPTUAL', 'PROBLEMA A RESOLVER', 'ADQUISICIÓN Y PROCESAMIENTO DE DATOS'])

        with tab1:
            st.write(
                '''
                El Objetivo de Desarrollo Sostenible (ODS) 7 plantea el compromiso de garantizar energía asequible, segura, sostenible y moderna para todos, lo que implica abordar tres grandes frentes, a saber: ampliar el acceso a la electricidad y a combustibles limpios, aumentar la participación de las energías renovables en la matriz mundial y mejorar de forma sustantiva la eficiencia energética. Este objetivo no se puede leer de manera aislada, sin considerar el concepto de transición energética justa, entendida como el proceso de descarbonizar las economías sin agravar las desigualdades, protegiendo a las poblaciones vulnerables, creando empleo digno y respetando los límites ambientales.

                En clave de descarbonización de las economías, la comunidad internacional ha asumido metas de reducción de gases de efecto invernadero (GEI) para mantener el calentamiento “muy por debajo de 2 °C” y, de ser posible, 1,5 °C. Sin embargo, el EGR 2023 (Emissions Gap Report ) muestra que las emisiones globales alcanzaron un récord de 57,4 GtCO₂e en 2022 y que, con las contribuciones nacionalmente determinadas (NDC) actuales, el mundo se encamina a un aumento de temperatura del orden de 2,5–2,9 °C, muy por encima de lo compatible con el Acuerdo de París. Para alinear la trayectoria con 2 °C y 1,5 °C sería necesario reducir las emisiones previstas para 2030 en aproximadamente 28 % y 42 %, respectivamente.

                Este escenario se complica por el nivel desigual de desarrollo entre países. El propio informe evidencia que el 10 % más rico de la población mundial concentra cerca de la mitad de las emisiones, mientras que los países de menores ingresos y los menos desarrollados son responsables de una fracción muy pequeña, a pesar de ser los más vulnerables a los impactos del cambio climático. Esto refuerza la idea de que una transición energética justa debe combinar tres dimensiones: mitigación ambiciosa, desarrollo humano y equidad entre y dentro de los países.

                En este contexto, un visor geográfico basado en los principales indicadores energéticos y climáticos del Banco Mundial que integre en mapas variables como acceso a la electricidad, participación de las energías renovables, intensidad energética, emisiones de CO₂ per cápita o por kWh, ingreso nacional bruto y otros indicadores socioeconómicos, sería una herramienta estratégica para el análisis de problemáticas complejas asociadas a la transición considerando brechas territoriales y temporales. 

                Adicionalmente, La dimensión histórica de las series permite analizar tendencias de varias décadas, identificar patrones de convergencia o divergencia entre regiones y evaluar si los países se están moviendo realmente hacia las metas del ODS 7 y hacia trayectorias compatibles con la reducción de GEI. Facilitando de esta forma la priorización de políticas públicas en cuanto a localización de territorios donde coexisten baja cobertura energética, alta dependencia de combustibles fósiles y vulnerabilidad social, permitiendo focalizar inversiones, cooperación internacional y proyectos piloto de energías renovables o eficiencia energética. También, para la academia y los gobiernos, abre la posibilidad de construir escenarios, comparar desempeños entre países de ingreso similar; monitorear el impacto de reformas regulatorias y programas de electrificación rural; posibilitando un ejercicio concreto, espacializado y cuantificable de seguimiento y toma de decisiones, clave para cerrar las brechas y mejorar la información entre lo que el mundo promete y lo que realmente está haciendo.

                '''
            )
        with tab2:
            st.write(
                '''
                La obtención de información reglada y normalizada para soportar los indicadores de los ODS —y en particular del ODS 17, que exige cooperación, interoperabilidad y datos comparables entre países— presenta dificultades estructurales que limitan la calidad del análisis. Como usuario experto y desarrollador de modelos de análisis espacial en ArcGIS Pro, y habiendo sido responsable del capítulo de hidrocarburos del Annual Report 2022 de Colombia ante la Agencia Internacional de la Energía (AIE), así como del relacionamiento técnico con el grupo de GEI del Banco Mundial, el autor ha podido constatar de primera mano las brechas en los flujos globales de datos. La AIE recibe reportes solo de un número reducido de países dado el alto nivel de la data mínima requerida. Del lado de la **GDB de Esri**, las fronteras geográficas solo existen para Estados con reconocimiento pleno por la ONU, lo que excluye territorios como Kosovo y restringe análisis sobre países emergentes o con conflictos con países con derecho de veto. A su vez, el **Banco Mundial** únicamente incorpora registros de países con asiento oficial en la ONU, pero la calidad, continuidad y amplitud de los indicadores varía de forma significativa entre regiones. En conjunto, estas limitaciones revelan que, aunque existen plataformas globales de referencia, los canales y fuentes de información siguen siendo limitados y heterogéneos, lo que dificulta consolidar una base de datos robusta, homogénea y plenamente alineada con las exigencias de los ODS’s.

                En consideración de lo anterior y con el objeto de buscar un camino viable para una “APP piloto” se decidió: 1) tomar los referentes conceptuales únicamente a partir de los lineamientos de AIE (Figura 1.); 2) El shape geográfico se tomaría únicamente de la base de datos geográfica ESRI complementada con la digitalización DE 17 países mas que no tienen fronteras geográficas reconocidas oficialmente y 3) La fuente de datos sobre indicadores será la World Data Indicators (https://databank.worldbank.org /source/world-development-indicators ) 2023, dado que la completitud de datos suele tener un delay de casi 2 años. 

                '''
            )
        with tab3:
            st.write(
                '''
                Entonces el problema a resolver será identificar para un set de indicadores determinado la evolución del indicador y el Delta con respecto a t=2030, que conceptualmente correspondería a la generación de planos usando como abscisa un indicador, ver figura 4.
                '''
            )
            st.image('img/cubo.png', width=600)
            st.caption('Figura 4. Representación conceptual del análisis multidimensional de indicadores ODS7 en el tiempo.')
            st.write('''
            El trabajo de completar, limpiar y estandarizar datos se ha realizado a través de pequeños bloque phyton, de la siguiente forma:
            ''')
            st.image('img/meta_algoritmo.png', width=600)
            st.caption('Figura 5. Metodología de procesamiento de datos WDI para la APP ODS7 en Mapas.')
        with tab4:
            st.write(
                '''
                Dado que los datos requeridos para el proyecto propuesto se encuentran dispersos, desactualizados y parcialmente desestructurados , y pueden ser difícilmente integrables sin un conocimiento temático y técnico suficiente; se seleccionaron dos fuentes principales para la constitución del mínimo producto viable a partir de fuentes regladas, que para el caso se soportan en el eje geográfico y en la base de datos de indicadores, como se especifica a continuación: 

                **WDIEXCEL23.xlsx**
                Fuente: https://databank.worldbank.org/source/world-development-indicators
                Fecha de descarga: Octubre 2025
                Size:  130 MB (137.232.384 bytes)
                
                **Descripción:**  Se compone de 6 hojas Data, Country, Series, country-series, series-time y footnote). La hoja Data es la matriz central del archivo y reúne los valores de los indicadores del Banco Mundial por país y por año. Cada fila representa la combinación de un país y un indicador específico, e incluye cuatro campos descriptivos —Country Name, Country Code, Indicator Name e Indicator Code— seguidos por una secuencia de columnas anuales que va desde 1960 hasta 2023. En total, la hoja posee 68 columnas, correspondientes a los campos de identificación más sesenta y cuatro años consecutivos de datos numéricos y 397.936 registros, de las cuales 73.304 corresponden a subtotales liquidados por regiones, continentes y mundo, que intrínsecamente pueden portar errores dado que se elaboran promedios incluyendo registros con ausencia de datos. 

                Las demás hojas funcionan como metadatos auxiliares. Country concentra información descriptiva de los países, como nombre, código, región o grupo de ingresos. Series documenta cada indicador, su definición, fuente, unidad de medida y características metodológicas. La hoja country-series registra observaciones particulares que aplican a ciertos indicadores en determinados países, mientras que series-time contiene anotaciones o modificaciones asociadas a los indicadores a lo largo del tiempo. Finalmente, footnote reúne notas aclaratorias complementarias.

                **Preprocesamiento:** 
                Al verificar la fuente de información se identifican que las hojas pueden ser independizables como tablas, haciendo especial énfasis los datos por país, la codificación de países, y los indicadores que permiten caracterizar el grado de madurexz de implementación del ODS7, con respecto a los datos históricos por pais al recorrer los registros se identifican que las hojas los datos tienen importantes vacíos antes del año 200 dado que la capacidad computacional lo permite resulta fácil simplificar esta fuente 

                '''
            )


st.markdown('<a id="acerca-de"></a><br><br>', unsafe_allow_html=True)
with st.container(border=True):
    with st.expander('Ver descripción del proyecto'):
        st.write(
            '''
            Esta aplicación interactiva permite explorar diversos indicadores
            relacionados con el Objetivo de Desarrollo Sostenible 7 (ODS 7)
            de las Naciones Unidas, que busca garantizar el acceso a una
            energía asequible, segura, sostenible y moderna para todos.

            Los datos provienen del conjunto de Indicadores de Desarrollo
            Mundial (WDI) del Banco Mundial, y se centran en aspectos clave
            como las emisiones de CO₂, el acceso a la electricidad, el uso
            de energías renovables, entre otros.

            La aplicación ofrece visualizaciones interactivas, incluyendo
            mapas mundiales, series temporales comparadas entre países y
            análisis de relaciones entre diferentes indicadores.
            '''
        )
        st.html('<h3 style="color:#3D6E85;">Acerca de los indicadores</h3>')

        col_izq, col_der = st.columns(2)
        with col_izq:
            st.write(
                '- Fuente: World Development Indicators (WDI) del Banco Mundial.\n'
                '- Un archivo .xlsx por indicador.\n'
                '- Cobertura temporal aproximada: 2000–2023.\n'
                '- La unidad y la definición dependen del indicador WDI original.\n'
                '- Se excluyen agregados regionales (solo países con código de 3 letras).\n'
                '- Se utiliza formato largo: país–año–valor.\n'
            )
        with col_der:
            st.write('Indicadores disponibles en esta app:')
            st.markdown(
                '\n'.join([f'- {nombre}' for nombre in INDICADORES.keys()])
            )

###############################################################################
#       SECCIÓN 2: MAPA MUNDIAL POR INDICADOR Y AÑO (CHOROPLETH)             #
###############################################################################

st.markdown('<a id="mapa"></a><br><br>', unsafe_allow_html=True)
with st.container(border=True):
    st.html('<h3 style="color:#3D6E85;">Mapa mundial por indicador y año</h3>')

    indicador_mapa = st.selectbox(
        'Selecciona el indicador para el mapa:',
        options=list(INDICADORES.keys()),
        key='indicador_mapa'
    )

    df_indicador_mapa = obtener_df_indicador(indicador_mapa)
    nombre_columna_valor_mapa = obtener_nombre_columna_valor(indicador_mapa)

    anios_disponibles = sorted(df_indicador_mapa['year'].unique())
    anio_seleccionado = st.slider(
        'Año',
        min_value=int(min(anios_disponibles)),
        max_value=int(max(anios_disponibles)),
        value=int(max(anios_disponibles)),
        step=1
    )

    df_anio_mapa = df_indicador_mapa[df_indicador_mapa['year'] == anio_seleccionado]

    st.write(
        f'Datos disponibles para {len(df_anio_mapa)} países en el año {anio_seleccionado}.'
    )

    figura_mapa = px.choropleth(
        df_anio_mapa,
        locations='country_code',
        color=nombre_columna_valor_mapa,
        hover_name='country_name',
        color_continuous_scale='Viridis',
        projection='natural earth',
        title=f'{indicador_mapa} - {anio_seleccionado}',
        labels={nombre_columna_valor_mapa: indicador_mapa}
    )
    figura_mapa.update_layout(height=500)

    st.plotly_chart(figura_mapa, use_container_width=True)

###############################################################################
#   SECCIÓN 3: SERIES TEMPORALES POR PAÍS PARA UN INDICADOR                  #
###############################################################################

st.markdown('<a id="series"></a><br><br>', unsafe_allow_html=True)
with st.container(border=True):
    st.html('<h3 style="color:#3D6E85;">Series temporales comparadas</h3>')

    indicador_series = st.selectbox(
        'Selecciona el indicador para las series temporales:',
        options=list(INDICADORES.keys()),
        key='indicador_series'
    )

    df_indicador_series = obtener_df_indicador(indicador_series)
    nombre_columna_valor_series = obtener_nombre_columna_valor(indicador_series)

    paises_disponibles = sorted(df_indicador_series['country_name'].unique())
    paises_seleccionados = st.multiselect(
        'Selecciona hasta 5 países para comparar:',
        options=paises_disponibles,
        default=paises_disponibles[:5],
        max_selections=5
    )

    if paises_seleccionados:
        df_series_seleccion = df_indicador_series[
            df_indicador_series['country_name'].isin(paises_seleccionados)
        ]

        figura_series = px.line(
            df_series_seleccion,
            x='year',
            y=nombre_columna_valor_series,
            color='country_name',
            markers=True,
            labels={
                'year': 'Año',
                nombre_columna_valor_series: indicador_series,
                'country_name': 'País'
            },
            title=f'Evolución temporal de {indicador_series}'
        )
        figura_series.update_layout(height=450)
        st.plotly_chart(figura_series, use_container_width=True)

        ultimo_anio_disponible = df_series_seleccion['year'].max()
        df_ultimo_anio = df_series_seleccion[df_series_seleccion['year'] == ultimo_anio_disponible]

        st.write(f'Valores en el último año disponible ({ultimo_anio_disponible}):')
        columnas_metricas = st.columns(len(df_ultimo_anio))
        for columna, (_, fila) in zip(columnas_metricas, df_ultimo_anio.iterrows()):
            columna.metric(
                label=fila['country_name'],
                value=f'{fila[nombre_columna_valor_series]:,.2f}'
            )
    else:
        st.info('Selecciona al menos un país para visualizar las series.')

###############################################################################
#   SECCIÓN 4: RELACIÓN ENTRE DOS INDICADORES (SCATTER PLOT)                 #
###############################################################################

st.markdown('<a id="relaciones"></a><br><br>', unsafe_allow_html=True)
with st.container(border=True):
    st.html('<h3 style="color:#3D6E85;">Relación entre indicadores</h3>')

    col_x, col_y = st.columns(2)
    with col_x:
        indicador_eje_x = st.selectbox(
            'Indicador en eje X:',
            options=list(INDICADORES.keys()),
            index=0,
            key='indicador_x'
        )
    with col_y:
        indicador_eje_y = st.selectbox(
            'Indicador en eje Y:',
            options=list(INDICADORES.keys()),
            index=1,
            key='indicador_y'
        )

    df_indicador_x = obtener_df_indicador(indicador_eje_x)
    df_indicador_y = obtener_df_indicador(indicador_eje_y)

    nombre_columna_x = obtener_nombre_columna_valor(indicador_eje_x)
    nombre_columna_y = obtener_nombre_columna_valor(indicador_eje_y)

    df_xy = pd.merge(
        df_indicador_x[['country_name', 'country_code', 'year', nombre_columna_x]],
        df_indicador_y[['country_code', 'year', nombre_columna_y]],
        on=['country_code', 'year'],
        how='inner'
    )

    anios_xy = sorted(df_xy['year'].unique())
    anio_relacion = st.slider(
        'Año para analizar la relación entre indicadores',
        min_value=int(min(anios_xy)),
        max_value=int(max(anios_xy)),
        value=int(max(anios_xy)),
        step=1
    )

    df_relacion = df_xy[df_xy['year'] == anio_relacion].dropna(subset=[nombre_columna_x, nombre_columna_y])

    st.write(
        f'Registros disponibles para {len(df_relacion)} países en {anio_relacion}.'
    )

    figura_dispersion = px.scatter(
        df_relacion,
        x=nombre_columna_x,
        y=nombre_columna_y,
        hover_name='country_name',
        labels={
            nombre_columna_x: indicador_eje_x,
            nombre_columna_y: indicador_eje_y
        },
        title=f'{indicador_eje_y} vs {indicador_eje_x} en {anio_relacion}'
    )

    figura_dispersion.update_traces(marker=dict(size=8, opacity=0.8))
    figura_dispersion.update_layout(height=450)

    st.plotly_chart(figura_dispersion, use_container_width=True)

    with st.expander('Ver tabla de datos para este año'):
        st.dataframe(
            df_relacion[['country_name', 'country_code', nombre_columna_x, nombre_columna_y]]
            .sort_values(by=nombre_columna_y, ascending=False)
        )





###############################################################################
#   SECCIÓN 5: CO₂ vs RENOVABLES (COMPARACIÓN DEDICADA)                       #
###############################################################################

st.markdown('<a id="co2-vs-renovables"></a><br><br>', unsafe_allow_html=True)
with st.container(border=True):
    st.html('<h3 style="color:#3D6E85;">Comparar emisiones de CO₂ con participación de energías renovables</h3>')

    # Indicadores fijos para esta sección
    indicador_co2 = 'Emisiones de CO₂ totales (kt)'
    indicador_ren = 'Participación de energías renovables (% consumo final)'

    # Cargar datos
    df_co2 = obtener_df_indicador(indicador_co2)
    df_ren = obtener_df_indicador(indicador_ren)

    col_co2 = obtener_nombre_columna_valor(indicador_co2)
    col_ren = obtener_nombre_columna_valor(indicador_ren)

    # Unir por país y año
    df_cmp = pd.merge(
        df_co2[['country_name', 'country_code', 'year', col_co2]],
        df_ren[['country_code', 'year', col_ren]],
        on=['country_code', 'year'],
        how='inner'
    ).dropna(subset=[col_co2, col_ren])

    # Controles
    anios_cmp = sorted(df_cmp['year'].unique())
    anio_cmp = st.slider(
        'Año para comparar CO₂ vs renovables',
        min_value=int(min(anios_cmp)),
        max_value=int(max(anios_cmp)),
        value=int(max(anios_cmp)),
        step=1,
        key='anio_cmp_co2_ren'
    )

    log_x = st.checkbox('Escala logarítmica para CO₂ (kt)', value=True)

    df_cmp_y = df_cmp[df_cmp['year'] == anio_cmp]

    st.write(f'Registros disponibles para {len(df_cmp_y)} países en {anio_cmp}.')

    # Diagrama de dispersión dedicado
    figura_cmp = px.scatter(
        df_cmp_y,
        x=col_co2,
        y=col_ren,
        hover_name='country_name',
        labels={
            col_co2: indicador_co2,
            col_ren: indicador_ren
        },
        title=f'{indicador_ren} vs {indicador_co2} en {anio_cmp}'
    )
    figura_cmp.update_traces(marker=dict(size=8, opacity=0.85))
    if log_x:
        figura_cmp.update_xaxes(type='log')
    figura_cmp.update_layout(height=470)

    st.plotly_chart(figura_cmp, use_container_width=True)

    # Métricas y tabla
    with st.expander('Ver métricas y tabla'):
        # Correlación de Pearson simple
        try:
            corr = df_cmp_y[[col_co2, col_ren]].corr().iloc[0, 1]
            st.metric('Correlación (Pearson)', f'{corr:0.3f}')
        except Exception:
            st.info('No se pudo calcular la correlación para este año.')

        st.dataframe(
            df_cmp_y[['country_name', 'country_code', col_co2, col_ren]]
            .sort_values(by=col_ren, ascending=False)
        )

    # Series temporales paralelas (opcional): seleccionar países
    with st.container(border=True):
        st.html('<h3 style="color:#3D6E85;">Comparar emisiones de CO₂ con participación de energías renovables por País</h3>')
        
        paises_cmp = sorted(df_cmp['country_name'].unique())
        seleccion_paises = st.multiselect(
            'Países (máx. 4):',
            options=paises_cmp,
            default=paises_cmp[:4],
            max_selections=4,
            key='paises_cmp_co2_ren'
        )
        if seleccion_paises:
            df_sel = df_cmp[df_cmp['country_name'].isin(seleccion_paises)]

            # Dos subgráficos lado a lado: CO2 y renovables
            col_a, col_b = st.columns(2)
            with col_a:
                fig_a = px.line(
                    df_sel,
                    x='year', y=col_co2, color='country_name', markers=True,
                    labels={'year': 'Año', col_co2: indicador_co2, 'country_name': 'País'},
                    title='Emisiones de CO₂ (kt)'
                )
                fig_a.update_layout(height=380)
                st.plotly_chart(fig_a, use_container_width=True)
            with col_b:
                fig_b = px.line(
                    df_sel,
                    x='year', y=col_ren, color='country_name', markers=True,
                    labels={'year': 'Año', col_ren: indicador_ren, 'country_name': 'País'},
                    title='Participación de energías renovables (%)'
                )
                fig_b.update_layout(height=380)
                st.plotly_chart(fig_b, use_container_width=True)





###############################################################################
#   SECCIÓN 6: PROYECCIÓN A 2030 (REGRESIÓN)                                  #
###############################################################################

st.markdown('<a id="proyeccion-2030"></a><br><br>', unsafe_allow_html=True)
with st.container(border=True):
    st.html('<h3 style="color:#3D6E85;">Proyección a 2030: CO₂ y renovables</h3>')
    st.caption(
        'Modelo simple: renovables ~ año (lineal) y CO₂ ~ año + renovables. '
        'Opcionalmente CO₂ en escala logarítmica.'
    )

    indicador_co2 = 'Emisiones de CO₂ totales (kt)'
    indicador_ren = 'Participación de energías renovables (% consumo final)'

    df_co2 = obtener_df_indicador(indicador_co2)
    df_ren = obtener_df_indicador(indicador_ren)

    col_co2 = obtener_nombre_columna_valor(indicador_co2)
    col_ren = obtener_nombre_columna_valor(indicador_ren)

    df_all = pd.merge(
        df_co2[['country_name', 'country_code', 'year', col_co2]],
        df_ren[['country_code', 'year', col_ren]],
        on=['country_code', 'year'], how='inner'
    ).dropna(subset=[col_co2, col_ren])

    # Controles
    paises_all = sorted(df_all['country_name'].unique())
    sel_paises = st.multiselect(
        'Países para proyectar (máx. 4):',
        options=paises_all,
        default=paises_all[:4],
        max_selections=4,
        key='proj_paises'
    )
    usar_log_co2 = st.checkbox('Usar CO₂ en logaritmo natural', value=True)
    anios = sorted(df_all['year'].unique())
    rango = st.slider(
        'Rango de años para ajustar',
        min_value=int(min(anios)),
        max_value=int(max(anios)),
        value=(max(int(min(anios)), 2005), int(max(anios))),
        step=1
    )

    def ajustar_lineal(x, y):
        x = x.astype(float)
        y = y.astype(float)
        A = np.vstack([x, np.ones_like(x)]).T
        coef, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
        m, b = coef[0], coef[1]
        y_pred = m * x + b
        ss_res = float(np.sum((y - y_pred) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2)) if len(y) > 1 else 0.0
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float('nan')
        return m, b, y_pred, r2

    resultados = []
    puntos_pred_ren = []
    puntos_pred_co2 = []

    if sel_paises:
        df_fit = df_all[(df_all['year'] >= rango[0]) & (df_all['year'] <= rango[1])]

        for pais in sel_paises:
            df_p = df_fit[df_fit['country_name'] == pais].sort_values('year')
            if len(df_p) < 3:
                continue

            # Ajuste renovables ~ año
            m_r, b_r, yhat_r, r2_r = ajustar_lineal(df_p['year'].to_numpy(), df_p[col_ren].to_numpy())
            ren_2030 = m_r * 2030 + b_r
            ren_2030 = float(np.clip(ren_2030, 0, 100))

            # Ajuste CO2 ~ año + renovables (opcional log)
            y_co2 = df_p[col_co2].astype(float)
            if usar_log_co2:
                y_co2 = np.log(y_co2.replace({0: np.nan})).dropna()
                df_p = df_p.loc[y_co2.index]

            X = np.column_stack([
                np.ones(len(df_p)),
                df_p['year'].to_numpy().astype(float),
                df_p[col_ren].to_numpy().astype(float)
            ])
            y = y_co2.to_numpy().astype(float)
            try:
                beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
                y_pred = X @ beta
                ss_res = float(np.sum((y - y_pred) ** 2))
                ss_tot = float(np.sum((y - np.mean(y)) ** 2)) if len(y) > 1 else 0.0
                r2_c = 1 - ss_res / ss_tot if ss_tot > 0 else float('nan')

                x2030 = np.array([1.0, 2030.0, ren_2030])
                y2030 = float(x2030 @ beta)
                co2_2030 = float(np.exp(y2030)) if usar_log_co2 else float(y2030)
            except Exception:
                r2_c = float('nan')
                co2_2030 = float('nan')

            resultados.append({
                'País': pais,
                'R² renovables~año': r2_r,
                f'{indicador_ren} 2030 (%)': ren_2030,
                'R² CO₂~año+renovables': r2_c,
                f'{indicador_co2} 2030 (kt)': co2_2030
            })

            puntos_pred_ren.append({'country_name': pais, 'year': 2030, col_ren: ren_2030, 'serie': 'Predicción 2030'})
            puntos_pred_co2.append({'country_name': pais, 'year': 2030, col_co2: co2_2030, 'serie': 'Predicción 2030'})

        # Gráficos históricos + punto 2030
        if resultados:
            df_hist = df_fit[df_fit['country_name'].isin(sel_paises)]
            df_pred_ren = pd.DataFrame(puntos_pred_ren)
            df_pred_co2 = pd.DataFrame(puntos_pred_co2)

            col_a, col_b = st.columns(2)
            with col_a:
                fig_ren = px.line(
                    df_hist, x='year', y=col_ren, color='country_name',
                    labels={'year': 'Año', col_ren: indicador_ren, 'country_name': 'País'},
                    title='Renovables: histórico y predicción 2030'
                )
                if not df_pred_ren.empty:
                    fig_ren.add_trace(
                        go.Scatter(
                            x=df_pred_ren['year'], y=df_pred_ren[col_ren], mode='markers',
                            marker=dict(color='black', symbol='x', size=10), name='Predicción 2030',
                            text=df_pred_ren['country_name']
                        )
                    )
                fig_ren.update_layout(height=380)
                st.plotly_chart(fig_ren, use_container_width=True)

            with col_b:
                fig_co2 = px.line(
                    df_hist, x='year', y=col_co2, color='country_name',
                    labels={'year': 'Año', col_co2: indicador_co2, 'country_name': 'País'},
                    title='CO₂: histórico y predicción 2030 (kt)'
                )
                if not df_pred_co2.empty:
                    fig_co2.add_trace(
                        go.Scatter(
                            x=df_pred_co2['year'], y=df_pred_co2[col_co2], mode='markers',
                            marker=dict(color='black', symbol='x', size=10), name='Predicción 2030',
                            text=df_pred_co2['country_name']
                        )
                    )
                fig_co2.update_layout(height=380)
                st.plotly_chart(fig_co2, use_container_width=True)

            st.write('Resumen de ajuste y proyección:')
            st.dataframe(pd.DataFrame(resultados))
        else:
            st.info('Selecciona países con suficiente historial para ajustar (≥ 3 años).')
    else:
        st.info('Selecciona al menos un país para proyectar.')

###############################################################################
#                       MENÚ DE NAVEGACIÓN LATERAL                            #
###############################################################################

with st.sidebar.container():
    st.markdown(
        '''
        <style>
        [data-testid="stSidebar"] a {
            display: block;
            color: #3D6E85;
            text-decoration: none;
            padding: 10px 5px;
            border-radius: 6px;
        }
        [data-testid="stSidebar"] a:hover {
            background-color: #FFFFFF;
        }
        </style>
        ''',
        unsafe_allow_html=True
    )
    st.html('<h4 style="color:#3D6E85;">Menú de navegación</h4>')
    st.markdown('[Inicio](#inicio)')
    st.markdown('[Acerca de los datos](#acerca-de)')
    st.markdown('[Mapa mundial](#mapa)')
    st.markdown('[Series temporales](#series)')
    st.markdown('[Relaciones entre indicadores](#relaciones)')
    st.markdown('[CO₂ vs Renovables](#co2-vs-renovables)')
    st.markdown('[Proyección a 2030](#proyeccion-2030)')
    st.markdown('---')
    st.caption('Contacto: jfescob@udea.edu.co')
