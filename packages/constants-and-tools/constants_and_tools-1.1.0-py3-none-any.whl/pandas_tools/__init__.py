import os
import tempfile
import pandas as pd
import json
from singleton_tools import SingletonMeta


class PandasTools(metaclass=SingletonMeta):
    def __init__(self):
        pass

    # <editor-fold desc="Archivos temporales    ----------------------------------------------------------------------------------------------------------------------------------">
    @staticmethod
    def save_temporary_df(df: pd.DataFrame) -> tempfile.NamedTemporaryFile:
        """
        Guarda un DataFrame en un archivo temporal y devuelve la ruta del archivo.
        :param df:DataFrame de pandas a guardar.
        :return:Un objeto de archivo temporal que necesita ser cerrado después de su uso.
        """
        # Crear un archivo temporal para el DataFrame
        temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.pkl')

        # Guardar el DataFrame en el archivo temporal
        df.to_pickle(temp_file.name)

        # Devolver el objeto de archivo temporal para su posterior uso
        return temp_file

    @staticmethod
    def load_temporary_df(temp_file_object) -> pd.DataFrame:
        """
        Lee un DataFrame desde un archivo temporal dado.
        :param temp_file_object: Objeto de archivo temporal desde el cual leer el DataFrame.
        :return: DataFrame de pandas leído desde el archivo.
        """

        # Leer el DataFrame desde el archivo temporal
        df = pd.read_pickle(temp_file_object.name)

        # Cerrar y eliminar el archivo temporal
        temp_file_object.close()

        return df

    # </editor-fold>

    # <editor-fold desc="Json Methods    -----------------------------------------------------------------------------------------------------------------------------------------">

    @staticmethod
    def save_json_from_dict(path_and_file_with_extension: str, to_save_dict_object: dict):
        with open(path_and_file_with_extension, 'w') as archivo_json:
            json.dump(to_save_dict_object, archivo_json)

    @staticmethod
    def load_json_in_dict(path_and_file_with_extension: str) -> dict:
        with open(path_and_file_with_extension, 'r') as f:
            return json.load(f)

    # </editor-fold>

    # <editor-fold desc="Utilidades varias    ------------------------------------------------------------------------------------------------------------------------------------">

    @staticmethod
    def boolean_imputer(df: pd.DataFrame, colname: str, value_to_fill):
        """
        Este método se usa para imputar columnas boleanas transformandolas a entero y agregando un nuevo valor para los NA
        :param df:
        :param colname:
        :param value_to_fill:
        :return:
        """
        df[colname] = pd.to_numeric(df[colname], errors='coerce').astype('Int64')
        df[colname] = df[colname].fillna(value_to_fill)

    @staticmethod
    def stringColsToList(str_text: str):
        lst = list(str_text.replace("[", "").replace("]", "").split(sep=","))
        return [z.strip() for z in lst]

    # </editor-fold>

    # <editor-fold desc="Transformación y tipado    ------------------------------------------------------------------------------------------------------------------------------">

    def tipping_by_dict(self, df: pd.DataFrame, colname_type_dict: dict, date_format: str) -> pd.DataFrame:
        """
        Tipar las columnas que se encuentran en un dict. Options: [Int64, float64, datetime, object, category]
        :param date_format:
        :param df:
        :param colname_type_dict:
        :return:
        """
        df_cols_list: list = [z for z in df.columns]
        for colname, coltype in colname_type_dict.items():
            if colname in df_cols_list:
                match coltype:
                    case "Int64":
                        df[colname] = self.to_pandas_int64(df[colname])
                    case "float64":
                        df[colname] = self.to_pandas_float64(df[colname])
                    case "datetime":
                        df[colname] = self.to_pandas_datetime(df[colname], date_format)
                    case "object":
                        df[colname] = self.to_pandas_object(df[colname])
                    case "category":
                        df[colname] = self.to_pandas_categorical(df[colname])
                    case _:
                        pass
        return df

    @staticmethod
    def to_pandas_int64(df_column: pd.Series):
        return pd.to_numeric(df_column, errors='coerce').astype('Int64')

    @staticmethod
    def to_pandas_bool(df_column: pd.Series, firstInt64: bool = True):
        if firstInt64:
            return pd.to_numeric(df_column, errors='coerce').astype('Int64').astype(pd.BooleanDtype())
        else:
            return df_column.astype(pd.BooleanDtype())

    @staticmethod
    def to_pandas_float64(df_column: pd.Series):
        return pd.to_numeric(df_column, errors='coerce').astype('float64')

    @staticmethod
    def to_pandas_datetime(df_column: pd.Series | str, formatter: str = "%Y-%m-%d"):
        try:
            return pd.to_datetime(df_column, format=f"{formatter}", errors="coerce")
        except TypeError:
            r = pd.to_datetime(df_column, format=formatter.replace(" %H:%M:%S", ""), errors="coerce")
            if r.isnull().sum() == r.size:
                raise TypeError("El formatter indicado ha arrojado un ValueError, se ha reintentado con %Y-%m-%d y ha hecho nula la columna")
            return r

    @staticmethod
    def to_pandas_timedelta(df_column: pd.Series | str):
        return pd.to_timedelta(df_column, errors="coerce")

    @staticmethod
    def to_pandas_object(df_column: pd.Series):
        return df_column.astype("object", copy=False)

    @staticmethod
    def to_pandas_string(df_column: pd.Series):
        return df_column.astype(pd.StringDtype())

    @staticmethod
    def to_pandas_categorical(df_column: pd.Series):
        return pd.Categorical(df_column)

    @staticmethod
    def to_pandas_categorical_ordered(df_column: pd.Series, ordered_values_list: list):
        return pd.Categorical(df_column, categories=ordered_values_list, ordered=True)

    # </editor-fold>

    # <editor-fold desc="Carga y guardado de dataframes    -----------------------------------------------------------------------------------------------------------------------">

    @staticmethod
    def read_csv_infering(file_path: str, sep: str | None = None, usecols: list | None = None) -> pd.DataFrame:
        """
        Metodo para leer archivos csv
        :param file_path: Ruta del archivo y extension (csv)
        :param sep: Default = "," -> Separador del csv
        :param usecols: En caso de querer solo algunas columnas, las especificamos en una lista
        :return: pd.DataFrame
        """
        return pd.read_csv(file_path, sep=sep, header=0, usecols=usecols, engine="python")

    @staticmethod
    def read_excel_infering(file_path: str, sheet_name: str | int = 0, usecols: list | None = None) -> pd.DataFrame:
        """
        Método para leer archivos Excel.
        :param file_path: Ruta del archivo y extensión (xlsx, xls).
        :param sheet_name: Nombre o índice de la hoja de cálculo que se desea leer. Por defecto es la primera hoja.
        :param usecols: En caso de querer solo algunas columnas, las especificamos en una lista.
        :return: pd.DataFrame
        """
        return pd.read_excel(file_path, sheet_name=sheet_name, usecols=usecols)

    @staticmethod
    def df_to_csv(path: str, df: pd.DataFrame, index: bool = False):
        """
        Metodo para guardar dataframes de pandas en archivos csv
        :param path: ruta/archivo.csv
        :param df: pd.Dataframe
        :param index: Añadir columna de indices, por defecto false
        :return: True si ha creado el archivo, False si ya existe
        """
        if not os.path.exists(path):
            print(f"---> dfToCsv: Guardando {path} ...")
            df.to_csv(path, index=index)
            print(f"---> dfToCsv: {path} guardado con exito. Su shape es: {df.shape}")
        else:
            print(f"---> dfToCsv: El archivo {path} ya existe")

    @staticmethod
    def df_to_parquet(path: str, df: pd.DataFrame, index: bool = True):
        """
        Metodo para guardar dataframes de pandas en archivos parquet (requiere pyarrow)
        :param path: ruta/archivo.parquet
        :param df: pd.Dataframe
        :param index: Añadir columna de indices, por defecto false
        :return: True si ha creado el archivo, False si ya existe
        """
        if not os.path.exists(path):
            print(f"---> dfToParquet: Guardando {path} ...")
            df.to_parquet(path, index=index)
            print(f"---> dfToParquet: {path} guardado con exito. Su shape es: {df.shape}")
        else:
            print(f"---> dfToParquet: El archivo {path} ya existe")

    @staticmethod
    def read_parquet_infering(file_path: str) -> pd.DataFrame:
        """
        Metodo para leer archivos Parquet (requiere pyarrow)
        :param file_path: Ruta del archivo y extension (Parquet)
        :return: pd.DataFrame
        """
        return pd.read_parquet(file_path)

    @staticmethod
    def df_to_json(path: str, df: pd.DataFrame, index: bool = False, dtype_dict: dict | None = None):
        """
        Metodo para guardar dataframes de pandas en archivos json
        :param dtype_dict: Diccionario de tipos de columna del json
        :param path: ruta/archivo.json
        :param df: pd.Dataframe
        :param index: Añadir columna de indices, por defecto false
        :return: None
        """
        if dtype_dict is not None:
            df.to_json(path, index=index, orient='records', lines=False, dtype=dtype_dict)
        else:
            df.to_json(path)

    # </editor-fold>
