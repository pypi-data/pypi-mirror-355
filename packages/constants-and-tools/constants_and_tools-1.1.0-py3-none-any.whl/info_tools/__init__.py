import pandas as pd
import polars as pl
import colorama
import warnings
from tabulate import tabulate
from colorama import Fore, Back, Style
from singleton_tools import SingletonMeta
colorama.init(autoreset=True)


class InfoTools(metaclass=SingletonMeta):
    def __init__(self, show_info: bool = True):
        self.show_info: bool = show_info

    @staticmethod
    def create_df_info(df: pl.DataFrame | pd.DataFrame, categoric_limit: int = 8, table_fmt: str = "fancy_grid"):
        is_polars = isinstance(df, pl.DataFrame)
        shape = df.shape

        print("#####################################################################################")
        print("Shape del DataFrame:")
        print(f"Filas: {shape[0]}")
        print(f"Columnas: {shape[1]}\n")

        info = []
        for col in df.columns:
            if is_polars:
                value_counts = df[col].value_counts(sort=True)
                unique_counts = dict(zip(
                    value_counts[col].to_list(),
                    value_counts["count"].to_list()
                ))
                null_count = df[col].null_count()
                dtype_str = str(df[col].dtype)
            else:
                unique_counts = df[col].value_counts().to_dict()
                null_count = df[col].isnull().sum()
                dtype_str = str(df[col].dtype)

            unique_counts_str = [f"{k}({v})" for k, v in unique_counts.items()]
            valores_unicos = ", ".join(unique_counts_str) if len(unique_counts) < categoric_limit else 'NO CATEGORICA'

            info.append({
                "NombreColumna": col,
                "NumeroValoresUnicos": len(unique_counts),
                "NumeroNulos": null_count,
                "ValoresUnicos": valores_unicos,
                "Dtype": dtype_str
            })

        # Crear DataFrame según el tipo de entrada
        if is_polars:
            info_df = pl.DataFrame(info)
            info_pandas = info_df.to_pandas()
        else:
            info_pandas = pd.DataFrame(info)

        print(tabulate(info_pandas, showindex=False, headers=info_pandas.columns, tablefmt=table_fmt))

    @staticmethod
    def print_polars_native(df: pl.DataFrame, row_print: int = 10):
        """
        Método alternativo para imprimir usando el formato nativo de Polars
        :param df: DataFrame de Polars a imprimir
        :param row_print: Numero de filas a imprimir
        :return: None
        """
        try:
            df_to_print = df.head(row_print)

            # Configurar opciones de display de Polars con UTF8_FULL
            with pl.Config(
                    tbl_rows=row_print,
                    tbl_cols=-1,  # Mostrar todas las columnas
                    tbl_width_chars=65000,  # Ancho máximo
                    fmt_str_lengths=1000,  # Longitud máxima de strings
                    tbl_formatting="UTF8_FULL"  # Formato UTF8 completo con bordes bonitos
            ):
                print(df_to_print)

        except Exception as e:
            print(f"Error al imprimir con formato nativo de Polars: {e}")
            print(df.head(row_print))

    def print_tabulate_df(self, df: pd.DataFrame | pl.DataFrame, show_index: bool = False, headers: list | None = None, row_print: int = 10, table_fmt: str = "fancy_grid"):
        """
        Metodo para imprimir en consola un dataframe tabulado
        :param table_fmt:
        :param df: Dataframe a imprimir
        :param show_index: Mostrar indices de fila
        :param headers: Columnas del dataframe (Si es None los muestra todos)
        :param row_print: Numero de filas a imprimir
        :return: None
        """
        try:

            # -- En caso de que sea un polars df, llamamos al metodo de polars, si es de pandas, sigue el flujo
            if isinstance(df, pl.DataFrame):
                self.print_polars_native(df, row_print=row_print)
                return

            # Guardar la configuración actual
            old_options = pd.get_option("display.float_format")

            # Configurar pandas para desactivar la notación científica
            pd.set_option('display.float_format', '{:.2f}'.format)
            pd.set_option('display.max_rows', None)  # Mostrar todas las filas
            pd.set_option('display.max_columns', None)  # Mostrar todas las columnas
            pd.set_option('display.width', None)  # Ancho de la consola sin truncamiento
            pd.set_option('display.max_colwidth', None)  # Mostrar toda la longitud de las cadenas en cada columna

            # Convertir el dataframe a string
            df = df.astype(str)

            if headers is not None:
                table = tabulate(df.head(row_print), showindex=show_index, headers=headers, tablefmt=table_fmt)
                table = table.replace('<th>', '<th style="background-color: lightgrey;">')
                print(table)
            else:
                table = tabulate(df.head(row_print), showindex=show_index, headers=df.columns, tablefmt=table_fmt)
                table = table.replace('<th>', '<th style="background-color: lightgrey;">')
                print(table)

            # Resetear las opciones de pandas a la configuración original
            pd.set_option("display.float_format", old_options)

            return
        except ValueError:
            print("NO SE PUEDE PINTAR TABULATE, PONGO EL PRINT")
            print(df.head(row_print))

    def header_print(self, text_to_print: str, text_color="light_yellow", bg_color=None, style="bright"):
        if self.show_info:
            stringVar = f'\n############################################################################################################################\n' \
                        f'############################################################################################################################\n' \
                        f'-------------------------------    {text_to_print}\n' \
                        f'############################################################################################################################\n' \
                        f'############################################################################################################################\n'

            print(self.print_colorama(stringVar, text_color=text_color, bg_color=bg_color, style=style))

    def intro_print(self, text_to_print: str, text_color="light_cyan", bg_color=None, style="bright"):
        if self.show_info:
            stringVar = f'\n#######################################################################################\n' \
                  f'----    {text_to_print}\n' \
                  f'#######################################################################################\n'

            print(self.print_colorama(stringVar, text_color=text_color, bg_color=bg_color, style=style))

    def sub_intro_print(self, text_to_print: str, text_color="light_white", bg_color=None, style=None):
        if self.show_info:
            print(f"\n{self.print_colorama('---> ' + text_to_print, text_color, bg_color, style)}")

    def info_print(self, text_to_print: str, text_color="light_green", bg_color=None, style="bright"):
        if self.show_info:
            print(f"{self.print_colorama('--------> [INFO]: ' + text_to_print, text_color, bg_color, style)}")

    def warning_print(self, text_to_print: str, text_color="light_white", bg_color="light_red", style="bright", category=UserWarning, stacklevel=2):
        if self.show_info:
            print(f"{self.print_colorama('--------> [WARNING]: ' + text_to_print, text_color, bg_color, style)}")
            warnings.warn(f"------> [WARNING]: {text_to_print}", category=category, stacklevel=stacklevel)

    @staticmethod
    def print_colorama(text, text_color=None, bg_color=None, style=None):
        """
        Imprime texto en consola con el color y estilo especificado.

        Args:
            text (str): El texto a imprimir.
            text_color (str): El color del texto. Debe ser uno de los siguientes:
                'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', None (por defecto).
            bg_color (str): El color del fondo. Debe ser uno de los siguientes:
                'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', None (por defecto).
            style (str): El estilo del texto. Debe ser uno de los siguientes:
                'reset', 'bright', 'dim', 'normal', None (por defecto).

        Raises:
            ValueError: Si el color o estilo especificado no es válido.
        """
        colors = {
            'black': Fore.BLACK,
            'red': Fore.RED,
            'green': Fore.GREEN,
            'yellow': Fore.YELLOW,
            'blue': Fore.BLUE,
            'magenta': Fore.MAGENTA,
            'cyan': Fore.CYAN,
            'white': Fore.WHITE,

            'light_black': Fore.LIGHTBLACK_EX,
            'light_red': Fore.LIGHTRED_EX,
            'light_green': Fore.LIGHTGREEN_EX,
            'light_yellow': Fore.LIGHTYELLOW_EX,
            'light_blue': Fore.LIGHTBLUE_EX,
            'light_magenta': Fore.LIGHTMAGENTA_EX,
            'light_cyan': Fore.LIGHTCYAN_EX,
            'light_white': Fore.LIGHTWHITE_EX,
            None: ''
        }

        bg_colors = {
            'black': Back.BLACK,
            'red': Back.RED,
            'green': Back.GREEN,
            'yellow': Back.YELLOW,
            'blue': Back.BLUE,
            'magenta': Back.MAGENTA,
            'cyan': Back.CYAN,
            'white': Back.WHITE,

            'light_black': Back.LIGHTBLACK_EX,
            'light_red': Back.LIGHTRED_EX,
            'light_green': Back.LIGHTGREEN_EX,
            'light_yellow': Back.LIGHTYELLOW_EX,
            'light_blue': Back.LIGHTBLUE_EX,
            'light_magenta': Back.LIGHTMAGENTA_EX,
            'light_cyan': Back.LIGHTCYAN_EX,
            'light_white': Back.LIGHTWHITE_EX,
            None: ''
        }

        styles = {
            'reset': Style.RESET_ALL,
            'bright': Style.BRIGHT,
            'dim': Style.DIM,
            'normal': Style.NORMAL,
            None: ''
        }

        if text_color not in colors:
            raise ValueError("Color de texto no válido. Los colores válidos son: black, red, green, yellow, blue, magenta, cyan, white, None")

        if bg_color not in bg_colors:
            raise ValueError("Color de fondo no válido. Los colores válidos son: black, red, green, yellow, blue, magenta, cyan, white, None")

        if style not in styles:
            raise ValueError("Estilo de texto no válido. Los estilos válidos son: reset, bright, dim, normal, None")

        color_seq = colors[text_color] + bg_colors[bg_color] + styles[style]
        reset_seq = Style.RESET_ALL

        return color_seq + text + reset_seq
