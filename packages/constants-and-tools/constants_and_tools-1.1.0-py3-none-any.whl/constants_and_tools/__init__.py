from info_tools import InfoTools
from pandas_tools import PandasTools
from polars_tools import PolarsTools
from os_tools import OsTools
from singleton_tools import SingletonMeta


class ConstantsAndTools(metaclass=SingletonMeta):
    def __init__(self):
        self.IT: InfoTools = InfoTools()
        self.PdT: PandasTools = PandasTools()
        self.PlT: PolarsTools = PolarsTools()
        self.OT: OsTools = OsTools()

    def create_data_directories(self, root_path: str = "./") -> tuple:
        """
        Metodo que crea la carpeta data con subcarpetas input_data y output_data y retorna las 3 rutas
        :param root_path:
        :return:
        """

        # -- Carpeta data
        self.OT.create_folder_if_not_exists(f"{root_path}data")

        # -- Carpeta input_data
        self.OT.create_folder_if_not_exists(f"{root_path}data/input_data")

        # -- Carpeta output_data
        self.OT.create_folder_if_not_exists(f"{root_path}data/output_data")

        return f"{root_path}data", f"{root_path}data/input_data", f"{root_path}data/output_data"
