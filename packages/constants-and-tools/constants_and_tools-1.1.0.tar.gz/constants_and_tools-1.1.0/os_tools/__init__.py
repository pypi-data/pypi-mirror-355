import glob
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from singleton_tools import SingletonMeta
import os
from typing import Dict, List


class OsTools(metaclass=SingletonMeta):
    def __init__(self):
        pass

    @staticmethod
    def execute_process_pool(methods: Dict) -> Dict:
        """
        Méthod que ejecuta el poolexecutor y retorna el diccionario con las respuestas
        Adecuado para tareas que consuman procesamiento CPU
        :param methods: EXAMPLE: {'nombre_metodo_1': (mi_metodo, (param1,)), 'nombre_metodo_2': (mi_metodo2, (param1, param2,))}.
        NOTA: Los parametros deben ir en formato tupla (param1, ). En caso de poner (param1) puede dar error
        :return:
        """

        results: dict = {}
        with ProcessPoolExecutor() as executor:
            futures = {name: executor.submit(func, *args) for name, (func, args) in methods.items()}

            for name, future in futures.items():
                try:
                    results[name] = future.result()  # Obtiene el resultado de cada proceso
                except Exception as e:
                    print(f"Error en {name}: {e}")

        return results

    @staticmethod
    def execute_thread_pool(methods: Dict) -> Dict:
        """
        Méthod que ejecuta el ThreadPoolExecutor y retorna el diccionario con las respuestas.
        Adecuado para tareas I/O-bound (como llamadas a API o lectura/escritura de archivos),
        :param methods: EXAMPLE: {'nombre_metodo_1': (mi_metodo, (param1,)), 'nombre_metodo_2': (mi_metodo2, (param1, param2,))}.
        NOTA: Los parametros deben ir en formato tupla (param1, ). En caso de poner (param1) puede dar error
        :return:
        """

        results: dict = {}
        with ThreadPoolExecutor() as executor:
            futures = {name: executor.submit(func, *args) for name, (func, args) in methods.items()}

            for name, future in futures.items():
                try:
                    results[name] = future.result()  # Obtiene el resultado de cada hilo
                except Exception as e:
                    print(f"Error en {name}: {e}")

        return results

    @staticmethod
    def create_folder_if_not_exists(folder_path: str) -> None:
        """
        Método para crear una carpeta si no existe ya
        :param folder_path:
        :return:
        """

        if not os.path.exists(folder_path):
            os.mkdir(folder_path)

    @staticmethod
    def get_path_files_by_extension(folder_path: str, extension: str) -> List[str]:
        """
        Método para obtener una lista con todos los archivos de una carpeta que sean de una extension concreta.

        :param folder_path: EXAMPLE: data/input_data/extracted_files
        :param extension: EXAMPLE: png
        :return: Lista de elementos que cumplen la condicion, example [img1.png, img2.png .... imgn.png]
        """

        return [z for z in glob.glob(f"{folder_path}/*.{extension}")]
