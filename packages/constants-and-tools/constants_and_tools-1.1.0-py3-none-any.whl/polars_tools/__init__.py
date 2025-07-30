import os
import tempfile
import polars as pl
import json
from singleton_tools import SingletonMeta


class PolarsTools(metaclass=SingletonMeta):
    def __init__(self):
        pass

    # <editor-fold desc="Archivos temporales    ----------------------------------------------------------------------------------------------------------------------------------">
    @staticmethod
    def save_temporary_df(df: pl.DataFrame) -> tempfile.NamedTemporaryFile:
        """
        Guarda un DataFrame en un archivo temporal y devuelve la ruta del archivo.
        :param df: DataFrame de polars a guardar.
        :return: Un objeto de archivo temporal que necesita ser cerrado después de su uso.
        """
        # Crear un archivo temporal para el DataFrame
        temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.parquet')

        # Guardar el DataFrame en el archivo temporal
        df.write_parquet(temp_file.name)

        # Devolver el objeto de archivo temporal para su posterior uso
        return temp_file

    @staticmethod
    def load_temporary_df(temp_file_object) -> pl.DataFrame:
        """
        Lee un DataFrame desde un archivo temporal dado.
        :param temp_file_object: Objeto de archivo temporal desde el cual leer el DataFrame.
        :return: DataFrame de polars leído desde el archivo.
        """
        # Leer el DataFrame desde el archivo temporal
        df = pl.read_parquet(temp_file_object.name)

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
    def boolean_imputer(df: pl.DataFrame, colname: str, value_to_fill):
        """
        Este método se usa para imputar columnas boleanas transformandolas a entero y agregando un nuevo valor para los NA
        :param df:
        :param colname:
        :param value_to_fill:
        :return:
        """
        df = df.with_columns(pl.col(colname).cast(pl.Int64, strict=False).fill_null(value_to_fill))
        return df

    @staticmethod
    def stringColsToList(str_text: str):
        lst = list(str_text.replace("[", "").replace("]", "").split(sep=","))
        return [z.strip() for z in lst]

    # </editor-fold>

    # <editor-fold desc="Transformación y tipado    ------------------------------------------------------------------------------------------------------------------------------">

    @staticmethod
    def tipping_by_dict(df: pl.DataFrame, colname_type_dict: dict, date_format: str) -> pl.DataFrame:
        """
        Tipar las columnas que se encuentran en un dict.
        Options: [Int64, Float64, Datetime, Utf8, Categorical]
        :param date_format:
        :param df:
        :param colname_type_dict:
        :return:
        """
        df_cols_list: list = df.columns
        for colname, coltype in colname_type_dict.items():
            if colname in df_cols_list:
                match coltype:
                    case "Int64":
                        df = df.with_columns(pl.col(colname).cast(pl.Int64, strict=False))
                    case "Float64":
                        df = df.with_columns(pl.col(colname).cast(pl.Float64, strict=False))
                    case "Datetime":
                        df = df.with_columns(pl.col(colname).str.strptime(pl.Datetime, format=date_format, strict=False))
                    case "Utf8":
                        df = df.with_columns(pl.col(colname).cast(pl.Utf8, strict=False))
                    case "Categorical":
                        df = df.with_columns(pl.col(colname).cast(pl.Categorical, strict=False))
                    case _:
                        pass
        return df

    @staticmethod
    def to_polars_int64(df_column: pl.Series):
        return df_column.cast(pl.Int64, strict=False)

    @staticmethod
    def to_polars_bool(df_column: pl.Series, firstInt64: bool = True):
        if firstInt64:
            return df_column.cast(pl.Int64, strict=False).cast(pl.Boolean, strict=False)
        else:
            return df_column.cast(pl.Boolean, strict=False)

    @staticmethod
    def to_polars_float64(df_column: pl.Series):
        return df_column.cast(pl.Float64, strict=False)

    @staticmethod
    def to_polars_datetime(df_column: pl.Series | str, formatter: str = "%Y-%m-%d"):
        try:
            if isinstance(df_column, str):
                return pl.Series([df_column]).str.strptime(pl.Datetime, format=formatter, strict=False)[0]
            return df_column.str.strptime(pl.Datetime, format=formatter, strict=False)
        except Exception as e:
            r = df_column.str.strptime(pl.Datetime, format=formatter.replace(" %H:%M:%S", ""), strict=False)
            if r.null_count() == r.len():
                raise TypeError(f"El formatter indicado ha arrojado un ValueError {e}, se ha reintentado con %Y-%m-%d y ha hecho nula la columna")
            return r

    @staticmethod
    def to_polars_timedelta(df_column: pl.Series | str):
        if isinstance(df_column, str):
            return pl.Series([df_column]).cast(pl.Duration, strict=False)[0]
        return df_column.cast(pl.Duration, strict=False)

    @staticmethod
    def to_polars_object(df_column: pl.Series):
        return df_column.cast(pl.Object, strict=False)

    @staticmethod
    def to_polars_string(df_column: pl.Series):
        return df_column.cast(pl.Utf8, strict=False)

    @staticmethod
    def to_polars_categorical(df_column: pl.Series):
        return df_column.cast(pl.Categorical, strict=False)

    # </editor-fold>

    # <editor-fold desc="Carga y guardado de dataframes    -----------------------------------------------------------------------------------------------------------------------">

    @staticmethod
    def read_csv_infering(file_path: str, sep: str = ",", usecols: list | None = None) -> pl.DataFrame:
        """
        Metodo para leer archivos csv
        :param file_path: Ruta del archivo y extension (csv)
        :param sep: Default = "," -> Separador del csv
        :param usecols: En caso de querer solo algunas columnas, las especificamos en una lista
        :return: pl.DataFrame
        """

        return pl.read_csv(file_path, separator=sep, columns=usecols)

    @staticmethod
    def read_excel_infering(file_path: str, sheet_name: str | int = 0, usecols: list | None = None) -> pl.DataFrame:
        """
        Método para leer archivos Excel.
        :param file_path: Ruta del archivo y extensión (xlsx, xls).
        :param sheet_name: Nombre o índice de la hoja de cálculo que se desea leer. Por defecto es la primera hoja.
        :param usecols: En caso de querer solo algunas columnas, las especificamos en una lista.
        :return: pl.DataFrame
        """
        return pl.read_excel(file_path, sheet_name=sheet_name, columns=usecols)

    @staticmethod
    def df_to_csv(path: str, df: pl.DataFrame, header: bool = False):
        """
        Metodo para guardar dataframes de polars en archivos csv
        :param path: ruta/archivo.csv
        :param df: pl.Dataframe
        :param header: Añadir columna de header, por defecto false
        :return: True si ha creado el archivo, False si ya existe
        """
        if not os.path.exists(path):
            print(f"---> dfToCsv: Guardando {path} ...")
            df.write_csv(path, include_header=header)
            print(f"---> dfToCsv: {path} guardado con exito. Su shape es: {df.shape}")
        else:
            print(f"---> dfToCsv: El archivo {path} ya existe")

    @staticmethod
    def df_to_parquet(path: str, df: pl.DataFrame, index: bool = True):
        """
        Metodo para guardar dataframes de polars en archivos parquet
        :param path: ruta/archivo.parquet
        :param df: pl.Dataframe
        :param index: Añadir columna de indices, por defecto false
        :return: True si ha creado el archivo, False si ya existe
        """
        if not os.path.exists(path):
            print(f"---> dfToParquet: Guardando {path} ...")
            if not index:
                df.with_row_index(name=None)
            df.write_parquet(path)
            print(f"---> dfToParquet: {path} guardado con exito. Su shape es: {df.shape}")
        else:
            print(f"---> dfToParquet: El archivo {path} ya existe")

    @staticmethod
    def read_parquet_infering(file_path: str) -> pl.DataFrame:
        """
        Metodo para leer archivos Parquet
        :param file_path: Ruta del archivo y extension (Parquet)
        :return: pl.DataFrame
        """
        return pl.read_parquet(file_path, use_pyarrow=True)

    @staticmethod
    def df_to_json(path: str, df: pl.DataFrame, index: bool = False):
        """
        Metodo para guardar dataframes de polars en archivos json
        :param path: ruta/archivo.json
        :param df: pl.Dataframe
        :param index: Añadir columna de indices, por defecto false
        :return: None
        """

        if not index:
            df.with_row_index(name=None)
        df.write_json(path)

    # </editor-fold>
