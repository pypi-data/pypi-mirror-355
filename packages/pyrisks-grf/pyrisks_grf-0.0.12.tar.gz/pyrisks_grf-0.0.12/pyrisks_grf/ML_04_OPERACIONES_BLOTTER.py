print('Módulo Local: Operaciones para Informe Contraparte (Operaciones_Cerradas_H_Blotter y Operac_Abiertas_Blotter)\nEste módulo contiene la ejecución del cálculo local de las Operaciones Abiertas y Cerradas para así subirlo a GCP.')

import pandas as pd
from openpyxl import load_workbook
from difflib import get_close_matches, SequenceMatcher
import os
import warnings
from difflib import get_close_matches, SequenceMatcher
from datetime import timedelta

# Para BigQuery
# pip install google-cloud-bigquery-storage
from google.cloud import bigquery

from A_TRANSVERSAL import dicc_static,RGB_F,Riesgo_F,project,dataset_id
from A_TRANSVERSAL import charge_serv,fechas_relevantes,generate_paths,multiple_query,search_business_day,Formateo_df2GCP,upload_table,retrasos_contraparte_habiles
#from A_TRANSVERSAL import next_business_day
#-----------------------------------------------------------------
# Funciones

# === 1. Match logic ===
def best_guess(word, possibilities, cutoff=0.0):
    matches = get_close_matches(word, possibilities, n=1, cutoff=cutoff)
    if matches:
        match = matches[0]
        score = SequenceMatcher(None, word, match).ratio()
        return match, score
    else:
        return None, 0.0

# === 2. Build suggestions ===
def build_guess_df(new_names, valid_names, cutoff=0.6):
    results = []
    for name in new_names:
        guess, score = best_guess(name, valid_names, cutoff=cutoff)
        results.append({
            'original_name': name,
            'suggested_match': guess,
            'similarity_score': round(score, 2)
        })
    return pd.DataFrame(results)

# === 3. Review interface (Base Python) ===
def review_matches_cli(df_matches):
    accepted = []
    rejected = []

    for i, row in df_matches.iterrows():
        print(f"\n🔍 Reviewing match {i + 1} of {len(df_matches)}")
        print(f"Original name   : {row['original_name']}")
        print(f"Suggested match : {row['suggested_match']}")
        print(f"Similarity score: {row['similarity_score']}")
       
        while True:
            choice = input("Accept match? (y/n): ").strip().lower()
            if choice == 'y':
                accepted.append(row)
                break
            elif choice == 'n':
                rejected.append(row)
                break
            else:
                print("Please enter 'y' or 'n'.")

    accepted_df = pd.DataFrame(accepted)
    rejected_df = pd.DataFrame(rejected)

    print("\n✅ Review complete!")
    print(f"✅ Accepted: {len(accepted_df)}")
    print(f"❌ Rejected: {len(rejected_df)}")

    return accepted_df, rejected_df

def match_names(df, name_list, name_columns=None):
    """
    Para una serie de nombres, realiza el match del nombre con el original, dado el formato
    del Excel 'Nombres_Contraparte'. Retorna el nombre original, es decir homogeneiza distintos nombres
    para la misma contraparte.

    Parameters:
    - df: pandas DataFrame
    - name_list: list of names to search for
    - name_columns: list of columns to search in (e.g., ['NOMBRE 1', 'NOMBRE 2', ...]).
      If None, it automatically uses columns that start with 'NOMBRE'.

    Returns:
    - List of matched values from 'NOMBRE 1'
    """
    if name_columns is None:
        name_columns = [col for col in df.columns if col.startswith('NOMBRE')]

    result = []

    for name in name_list:
        match = df[df[name_columns].apply(lambda row: name in row.values, axis=1)]
        if not match.empty:
            result.append(match.iloc[0]['NOMBRE 1'])  # First name
        else:
            result.append(None)  

    return result

def add_days_2_date(fecha, days):

        """
        Suma días de forma trivial, sin festivos ni nada.
        Parámetros: Fecha base en formato 'DD-MM-YYYY' y el número de días a sumar.

        Output: El día hábil anterior en formato 'DD-MM-YY'.
        """
        today = pd.to_datetime(fecha, dayfirst= False)
        next_day = today + timedelta(days = days)

        return next_day.strftime("%Y-%m-%d")


def global_treatment_Operaciones_Blotter_Pan(fecha:str=None,where_to_run:str='local'):
    fecha = None # SOlo use para pruebas
    where_to_run = 'local'
    # Objetos estáticos
    month_map, original_names, new_names, original_names_incumpl, new_names_incumpl = (dicc_static[k] for k in ('dicc_month_map','original_names_blotter',
                                                                                                                'new_names_blotter', 'original_names_incumplimientos',
                                                                                                                'new_names_incumplimientos'))

    
    # Generación de Fechas y Paths
    fechas = fechas_relevantes(pais = "PAN", fecha_analisis= fecha)
    fecha_corte,fecha_corte_ayer,fecha_analisis,festivos_dates = [fechas[k] for k in ['f_corte','f_corte_ayer','f_analisis','festivos']]
    all_paths = generate_paths(fecha_corte= fecha_corte, fecha_corte_ayer=fecha_corte_ayer, RGB_F=RGB_F, Riesgo_F=Riesgo_F, month_map=month_map)

    # Desagregación de Paths
    path_ruta_operaciones, ruta_cumplimientos, manual_data_path = (all_paths[k] for k in ('operaciones_blotter','incumplimientos_blotter','nombres_parametros_blotter'))
    #ruta_cumplimientos = r'K:\Cuadro Riesgo-Cumplimientos 09.05.2025.xlsx'
    #-----------------------------------------------------------------
    # Cargar Insumos
    
    # Insumo 1 Operaciones Abiertas Blotter
    # Paths de GCP
    client, dataset_ref, tables_ref = charge_serv(where_to_run=where_to_run, project = project, dataset_id = dataset_id, tables_names=[])
    #client, dataset_ref, tables_ref = charge_serv(where_to_run='local', project = project, dataset_id = dataset_id, tables_names=[])
    table_ref = ["{}.{}.{}".format(project,dataset_id,'Operac_Abiertas_Blotter')]

    # Definición de Queries
    query_list = [f"""
        SELECT*
        FROM {table_ref[0]}
        """]

    # Importe de Input 1, 2, 3.
    # Operaciones para IRL, Portafolio de Plano y Liquidez de Plano.
    Operaciones_Activas_Viejas = multiple_query(client = client, query_list = query_list)[0]

    # Formatear la fecha de trade_date
    Operaciones_Activas_Viejas['Trade_Date'] = Operaciones_Activas_Viejas['Trade_Date'].dt.tz_localize(None)
    Operaciones_Activas_Viejas['Settlement_Date'] = Operaciones_Activas_Viejas['Settlement_Date'].dt.tz_localize(None)
    Operaciones_Activas_Viejas['Real_Settlement_Date'] = Operaciones_Activas_Viejas['Real_Settlement_Date'].dt.tz_localize(None)

    ################################################################################################################
    # Insumo 2: Nuevas operaciones abiertas
    nuevas_operaciones = pd.read_excel(path_ruta_operaciones, skiprows= 2)

    # Renombrar las columnas
    rename_dict = dict(zip(original_names, new_names))
    nuevas_operaciones = nuevas_operaciones.rename(columns=rename_dict)

    # Si la trade date no coincida se debe a que no hubo operaciones en la fecha anterior y se repite el mismo operaciones ya viejo de fecha corte ayer.
    condicion_si_no_hay_nuevasop = (nuevas_operaciones['Trade_Date'] == fecha_corte_ayer).all()
    if condicion_si_no_hay_nuevasop:
        nuevas_operaciones.drop(nuevas_operaciones.index, inplace=True)
    # Eliminamos duplicados-- si los hay--
    nuevas_operaciones = nuevas_operaciones.drop_duplicates()
    ################################################################################################################
    # Insumo 3: Incumplimientos de operaciones abiertas
    operac_incumplimientos = pd.read_excel(ruta_cumplimientos)

    # Renombrar las columas para hacer el merge con operaciones activas
    rename_dict_incumpl = dict(zip(original_names_incumpl, new_names_incumpl))
    operac_incumplimientos = operac_incumplimientos.rename(columns=rename_dict_incumpl)
    operac_incumplimientos['Net'] = operac_incumplimientos['Net'].astype(float)

    # Total de incumplimientos
    print(rf"Total de incumplimientos: {operac_incumplimientos.shape[0]}") 

    ################################################################################################################
    # Input 4: Parámetros Nombres
    # Este input se debe a que los nombres de las contrapartes a veces difieren, aunque haga referencia a la misma contraparte.
    Nombres_Contrap = pd.read_excel(manual_data_path)


    #-----------------------------------------------------------------
    # Identificar las nuevas operacioes activas y las nuevas cerradas

    if operac_incumplimientos.shape[0] == 0:

        # Si no hay operaciones incumplidas. Entonces simplemente son activas todas con settlement posterior a la fecha de corte.
        New_Operaciones_Activas_Viejas = Operaciones_Activas_Viejas[Operaciones_Activas_Viejas['Settlement_Date'] >= fecha_analisis]
        # El complemento serán las operaciones que se cerraron.
        Operaciones_Cerradas =  Operaciones_Activas_Viejas[Operaciones_Activas_Viejas['Settlement_Date'] < fecha_analisis]
    else:
        # Se identifican de las operaciones realizadas cuales corresponden a retrasos y por ende siguen activas.
        merge_keys = ['Trade_Date','ISIN','Net']

        rows_retrasos = Operaciones_Activas_Viejas[merge_keys].apply(tuple, axis = 1).isin(operac_incumplimientos[merge_keys].apply(tuple, axis = 1))
        Retrasos = Operaciones_Activas_Viejas[rows_retrasos]

        # El siguiente bloque intenta automatizar cuando no hay match entre las Operaciones Activas de GCP y las operaciones
        # incumplimientos que envía alguien. Este código busca encontrar las operaciones donde no hubo match con las Operaciones
        # que ya se encuentran cerradas en GCP. Esto en un mundo ideal no debería ocurrir, pero resulta que hay un delay, la persona}
        # que envía el insumo de incumplimientos puede darse cuenta del incumplimiento e.g. una semana después de la fecha de pago.
        ########################################################################################################################

        if operac_incumplimientos.shape[0] != Retrasos.shape[0]:
            print(f"Se encontraron {operac_incumplimientos.shape[0]} incumplimientos en el insumo pero se encontró match con solo {Retrasos.shape[0]} retrasos.")

            merged = operac_incumplimientos.merge(
            Operaciones_Activas_Viejas[merge_keys].drop_duplicates(),
            how = 'left',
            on = merge_keys,
            indicator=True)

            schema_corr_incumpl = [bigquery.SchemaField(merge_keys[0], "TIMESTAMP", mode="NULLABLE"),
                                bigquery.SchemaField(merge_keys[1], "STRING", mode="NULLABLE"),
                                bigquery.SchemaField(merge_keys[2], "FLOAT64", mode="NULLABLE")]
            # Rows unmatched contiene las filas de operaciones incumplimientos que requieren ser buscadas.
            rows_unmatched = merged[merged['_merge'] == 'left_only'][merge_keys].copy()
            print(f"Se procede a buscar si los siguientes matchs faltantes están en OP_Cerradas:{rows_unmatched}")

            table_ref = ["{}.{}.{}".format(project,dataset_id,k) for k in ['Operac_Cerradas_H_Blotter','Blotter_Correccion_Incumpl']]

            # Cargamos el df sobre el cual queremos realizar el match.
            upload_table(client,big_query_table_ref=table_ref[1],table_to_append=rows_unmatched,
                        schema=schema_corr_incumpl, write_disposition='WRITE_TRUNCATE')
            

            # Columnas sobre las que realizar el merge.
            clause_merge = " AND ".join([f"main.{col} = temp.{col}" for col in merge_keys])

            # Realizamos el primer query para la extracción de los matches
            # Definición de Queries
            query_match = [f"""
                        SELECT main.*
                        FROM {table_ref[0]} AS main
                        JOIN {table_ref[1]} AS temp
                        ON {clause_merge}
                        """
                        ]

            # Trae el dataframe de Operaciones Cerradas que hizo match con los incumplimientos
            rows_matched = multiple_query(client = client, query_list = query_match)[0]



            if rows_matched.shape[0] == 0:
                raise ValueError("No se encontró matches en OP Cerradas, verifique los insumos manualmente")
            
            else:

                rows_matched['Trade_Date'] = rows_matched['Trade_Date'].dt.tz_localize(None)
                rows_matched['Settlement_Date'] = rows_matched['Settlement_Date'].dt.tz_localize(None)
                rows_matched['Real_Settlement_Date'] = rows_matched['Real_Settlement_Date'].dt.tz_localize(None)
                # Se actualizan los retrasos, con base a los matches encontrados.
                Retrasos = pd.concat([Retrasos, rows_matched])
                
                query_del = f"""
                DELETE FROM {table_ref[0]} AS main
                WHERE EXISTS (
                    SELECT 1
                    FROM {table_ref[1]} AS temp
                    WHERE {clause_merge}
                    )
                """

                client.query(query_del).result()
                #empty = multiple_query(client = client, query_list = query_del)[0]
            
                if rows_matched.shape[0] == rows_unmatched.shape[0]:
                    
                    print("Ha habido un match exacto con operaciones en OP_Cerradas, se procede a finalizar el proceso automáticamente")
                else:
                    
                    merged = operac_incumplimientos.merge(
                    Retrasos[merge_keys].drop_duplicates(),
                    how = 'left',
                    on = merge_keys,
                    indicator=True)

                    rows_still_unmatched = merged[merged['_merge'] == 'left_only'][merge_keys].copy()

                    
                    print(f"No hubo un match exacto, se procede a actualizar automáticamente los matches encontrados, pero están pendientes por hacer match las siguiente operaciones de incumplimientos: {rows_still_unmatched}.")

    ######################################################################################################################

        # Se incluyen aquellas operaciones activas.
        Op_activas_sin_retraso = Operaciones_Activas_Viejas[Operaciones_Activas_Viejas['Settlement_Date'] >= fecha_analisis]
        New_Operaciones_Activas_Viejas = pd.concat([Op_activas_sin_retraso, Retrasos])
        New_Operaciones_Activas_Viejas = New_Operaciones_Activas_Viejas.drop_duplicates()

        # Piénselo, no deberian haber duplicates pero por si acaso
        New_Operaciones_Activas_Viejas.drop_duplicates()
        
        # El complemento de lo anterior, corresponde a las operaciones cerradas
        Operaciones_Cerradas = Operaciones_Activas_Viejas[(Operaciones_Activas_Viejas['Settlement_Date'] < fecha_analisis) & (~rows_retrasos)].copy()

    #-----------------------------------------------------------------
    # Realizar Merge con las nuevas operaciones

    # Si no hay operaciones nuevas solo se toman las viejas que siguen activas.
    # Si las hay, se incluyen ambas.

    if not condicion_si_no_hay_nuevasop:

        # Se incluyen las operaciones raras de hoy en cerradas:
        operaciones_diferentes = nuevas_operaciones[(nuevas_operaciones['Status'] != 'Accepted') | (nuevas_operaciones['Settlement_Date'] < fecha_analisis)]
        
        # Únicamente se tienen en cuenta para activas de hoy, aquellas operaciones cuyo status sea aceptado.
        nuevas_operaciones = nuevas_operaciones[(nuevas_operaciones['Status'] == 'Accepted') & (nuevas_operaciones['Settlement_Date'] >= fecha_analisis)]

        if not operaciones_diferentes.empty:
            Operaciones_Cerradas = pd.concat([Operaciones_Cerradas, operaciones_diferentes])

        # Posteriormente se realiza el merge entre las nuevas y las viejas que siguen activas.
        if not New_Operaciones_Activas_Viejas.empty and not nuevas_operaciones.empty:

            Operaciones_Activas = pd.concat([New_Operaciones_Activas_Viejas, nuevas_operaciones])

        elif not New_Operaciones_Activas_Viejas.empty and nuevas_operaciones.empty:
            Operaciones_Activas = New_Operaciones_Activas_Viejas.copy()

        else:

            Operaciones_Activas = nuevas_operaciones.copy()

    else:
        if not New_Operaciones_Activas_Viejas.empty:

            Operaciones_Activas = New_Operaciones_Activas_Viejas
        else:
            Operaciones_Activas = nuevas_operaciones.copy()

    #-----------------------------------------------------------------
    # Cálculo del Real Settlement Date y Days_Difference por incumplimientos
    
    if not Operaciones_Activas.empty:
        # Este valor solo se llena con el Excel de incumplimientos, pero se crea por garantizar consistencia entre tablas.
        Operaciones_Activas['Observaciones'] = [''] * len(Operaciones_Activas)
        Operaciones_Activas['Days_Difference'] = Operaciones_Activas.apply(lambda row: retrasos_contraparte_habiles(fecha_analisis, row['Settlement_Date'], festivos_dates), axis=1)

        # Le creo al Blotter, donde caiga el settlement ese es el real settlement, salvo que haya incumplimiento. Si hay incumplimiento
        # defino el real settlement como el siguiente día hábil según Panamá.
        Operaciones_Activas['Real_Settlement_Date'] = Operaciones_Activas['Settlement_Date'].apply(lambda d: max(pd.to_datetime(d), pd.to_datetime(fecha_analisis)))


        # Días de tardanza de las operaciones.
        print(rf"Tardanza de días de las operaciones: {Operaciones_Activas['Days_Difference'].tolist()}")

    #-----------------------------------------------------------------
    # Identificar cada una de las contrapartes

    # En el siguiente fragmento se intenta hacer match de los nuevos nombres (si los hay) con los existentes. El usuario puede revisar los match propuestos y aceptar o denegar los mismos.
    # En caso de denegar, se debe modificar manualmente el Archivo de Excel de 'Nombres_Contrapartes'. 

    # Lista nombres simplemente pone en una lista todos los nombres de contrapartes mapeados en el insumo de Parámetros Nombres.
    # Este será la lista de posibilidades con quien realizar match.
    if not Operaciones_Activas.empty:

        lista_nombres = pd.Series(Nombres_Contrap[Nombres_Contrap.columns[Nombres_Contrap.columns.str.contains('NOMBRE')]].values.ravel().tolist())
        lista_nombres.dropna(inplace = True)

        # Luego, verificamos si existen nuevos nombres en Operaciones Abiertas.
        new_names = [x for x in Operaciones_Activas['Sales_Firm'].drop_duplicates().to_list() if x not in lista_nombres.to_list()]
        #new_names = ['BANK OF New YorkM','SCOTIA INC','DAV PANAMA']

    else:
        new_names = []

    if new_names:

        df_matches = build_guess_df(new_names, lista_nombres.to_list(), cutoff=0.4)
        print(df_matches)

    else:
        print("No hay nombres nuevos, se procede a finalizar la ejecución sin problemas")


    if new_names:
        accepted_df, rejected_df = review_matches_cli(df_matches)

    if new_names:

        print('-'*60+'\n','Estos son las matches aceptados:\n\n',accepted_df)

    if new_names:    
        print('-'*60+'\n','Estos son las matches rechazados:\n\n',rejected_df)

    if new_names:
        if not accepted_df.empty: 

            for index, row in accepted_df.iterrows():
                
                    nombre_match = row['suggested_match'] # Este es el nombre con el que se hizo match. El verdadero identificador si se quiere.
                    nombre_original = row['original_name'] # Este es el nombre recibido nuevo por el blotter.

                    fila = Nombres_Contrap[Nombres_Contrap.apply(lambda row: row.str.contains(nombre_match).any(), axis = 1)]

                    if fila.isna().sum(axis = 1).all() > 0:
                        columna = Nombres_Contrap.iloc[fila.index[0]].index[Nombres_Contrap.iloc[fila.index[0]].isna()].to_list()[0]
                        Nombres_Contrap.loc[fila.index[0],columna] = nombre_original
                    else:
                        columna = 'NOMBRE ' + str(len(Nombres_Contrap.columns) - 1)
                        Nombres_Contrap.loc[fila.index[0],columna] = nombre_original  
            
            # Guardar ajuste en el Excel nuevamente
            if os.path.exists(manual_data_path): 
            # Load the existing Excel file
                with pd.ExcelWriter(manual_data_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    # Load the workbook
                    workbook = load_workbook(manual_data_path)
                    # Check if the sheet already exists
                    Nombres_Contrap.to_excel(writer, sheet_name='Nombres_Contrap', index = False) 
                    print(f"Sheet 'Nombres_Contrap' has been successfully appended.") 
        else: 
            print(f"Warning: The file '{manual_data_path}' does not exist.")



    #-----------------------------------------------------------------
    # Si hay matches rechazados, se debe volver a correr el código despues de realizar el ajuste manualmente 

    # Solamente si no hay nombres nuevos o si se aceptan todos los nombres nuevos, se permite la homogeneización
    # y carga a GCP.

    if not new_names:
        matches_done = True
    else:
        if rejected_df.shape[0] == 0:
            matches_done = True
        else:
            matches_done = False

    # Se homogeneizan los nombres.

    if matches_done:

        # Homogeneizar los nombres para las operaciones activas.
        nombres_correctos_Ac = match_names(Nombres_Contrap, Operaciones_Activas['Sales_Firm'])
        Operaciones_Activas['Sales_Firm'] = nombres_correctos_Ac
        # Incluir el NIT para luego mapear a la biblia
        Operaciones_Activas['NIT'] = Operaciones_Activas['Sales_Firm'].map(Nombres_Contrap.set_index('NOMBRE 1')['NIT'])

        # Homogeneizar los nombres para las operaciones cerradas.
        nombres_correctos_Ce = match_names(Nombres_Contrap, Operaciones_Cerradas['Sales_Firm'])
        Operaciones_Cerradas['Sales_Firm'] = nombres_correctos_Ce
        Operaciones_Cerradas['NIT'] = Operaciones_Cerradas['Sales_Firm'].map(Nombres_Contrap.set_index('NOMBRE 1')['NIT'])


    #-----------------------------------------------------------------
    # Cargue a GCP

    if matches_done:

        # Formateo de Operaciones Activas a Cargar
        cols_to_datetime = ['Trade_Date','Execution_Time','Settlement_Date','Real_Settlement_Date']
        cols_to_float64 = ['Yield','Quantity_M','Principal','Sec_Number','Net','Days_Difference','NIT']
        cols_to_string = ['Status', 'Side','UserName','Customer','Security','ISIN','Contraparte_Name', 'Ord_Inq',
                        'Platform','App','Dlr_Alias','Contraparte_Code','C_Firm','Sales_Firm','Observaciones', 
                        'Exec_Time','Price']

        if not Operaciones_Activas.empty:
            Operaciones_Activas = Formateo_df2GCP(Operaciones_Activas, cols_to_datetime, cols_to_float64, cols_to_string, dayfirst=False)

        # Formateo de Operaciones Cerradas a Cargar
        cols_to_datetime = ['Trade_Date','Execution_Time','Settlement_Date','Real_Settlement_Date']
        cols_to_float64 = ['Yield','Quantity_M','Principal','Sec_Number','Net','Days_Difference','NIT']
        cols_to_string = ['Status', 'Side','UserName','Customer','Security','ISIN','Contraparte_Name', 'Ord_Inq',
                        'Platform','App','Dlr_Alias','Contraparte_Code','C_Firm','Sales_Firm','Observaciones', 
                        'Exec_Time','Price']

        if not Operaciones_Cerradas.empty:
            Operaciones_Cerradas = Formateo_df2GCP(Operaciones_Cerradas, cols_to_datetime, cols_to_float64, cols_to_string, dayfirst=False)

        schema_operac_contr = [
            bigquery.SchemaField("Status", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("Side", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("UserName", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("Customer", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("Trade_Date", "TIMESTAMP", mode="NULLABLE"),
            bigquery.SchemaField("Execution_Time", "TIMESTAMP", mode="NULLABLE"),
            bigquery.SchemaField("Security", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("Price", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("Yield", "FLOAT64", mode="NULLABLE"),
            bigquery.SchemaField("ISIN", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("Quantity_M", "FLOAT64", mode="NULLABLE"),
            bigquery.SchemaField("Principal", "FLOAT64", mode="NULLABLE"),
            bigquery.SchemaField("Contraparte_Name", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("Ord_Inq", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("Platform", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("App", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("Dlr_Alias", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("Contraparte_Code", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("Sec_Number", "FLOAT64", mode="NULLABLE"),
            bigquery.SchemaField("Net", "FLOAT64", mode="NULLABLE"),
            bigquery.SchemaField("Settlement_Date", "TIMESTAMP", mode="NULLABLE"),
            bigquery.SchemaField("C_Firm", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("Exec_Time", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("Sales_Firm", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("Real_Settlement_Date", "TIMESTAMP", mode="NULLABLE"),
            bigquery.SchemaField("Days_Difference", "FLOAT64", mode="NULLABLE"),
            bigquery.SchemaField("Observaciones", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("NIT", "INTEGER", mode="NULLABLE")
            ]

                    # Cargue Operaciones Activas
        if not Operaciones_Activas.empty:
            table_ref = "{}.{}.{}".format(project,dataset_id,'Operac_Abiertas_Blotter')
            upload_table(client,big_query_table_ref=table_ref,table_to_append=Operaciones_Activas,schema=schema_operac_contr,write_disposition='WRITE_TRUNCATE') # Truncate
                
        # Cargue Operaciones Cerradas
        if not Operaciones_Cerradas.empty:
                    
            table_ref = "{}.{}.{}".format(project,dataset_id, 'Operac_Cerradas_H_Blotter')
            upload_table(client,big_query_table_ref=table_ref,table_to_append=Operaciones_Cerradas,schema=schema_operac_contr) #Append
