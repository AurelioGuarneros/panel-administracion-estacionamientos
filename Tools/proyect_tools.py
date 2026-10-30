import os
import json
import shutil
import platform

import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

import traceback

from openpyxl import load_workbook
from openpyxl.workbook.protection import WorkbookProtection

from os import path

from dateutil.relativedelta import relativedelta
from datetime import date

import requests
from requests.exceptions import RequestException
import traceback

from zipfile import ZipFile, ZIP_DEFLATED

clave: str = "PASE"


class Tools:
    """
    Clase que proporciona herramientas útiles para el proyecto.
    """

    def __init__(self):
        """
        Constructor de la clase.

        :return:
            - None
        """
        self.ruta_proyecto = self.get_project_path()

    def validate_entry_number(self, nuevo_valor) -> None:
        """
        Valida si un nuevo valor es un número entero.

        Args:
            nuevo_valor (any): El valor a validar.

        Returns:
            bool: True si el valor es un número entero, False de lo contrario.
        """
        try:
            return True if nuevo_valor == "" or nuevo_valor.isdigit() else False
        except ValueError:
            return False

    @staticmethod
    def get_project_path() -> None:
        """
        Método que obtiene la ruta del directorio raíz del proyecto.

        :return:
            - dirname (str): La ruta del directorio raíz del proyecto.
        """
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def listar_directorios_archivos(self) -> None:
        """
        Método que imprime una lista de todos los archivos y directorios dentro del directorio raíz del proyecto,
        excluyendo la carpeta 'env', archivos ocultos y la carpeta '.git'.

        :return:
            - None
        """
        for root, dirnames, filenames in os.walk(self.ruta_proyecto):
            # Ignorar la carpeta 'env'
            if 'env' in dirnames:
                dirnames.remove('env')
            if '.venv' in dirnames:
                dirnames.remove('.venv')
            if '.vscode' in dirnames:
                dirnames.remove('.vscode')
            if '.git' in dirnames:
                dirnames.remove('.git')
            if '__pycache__' in dirnames:
                dirnames.remove('__pycache__')
            level = root.replace(self.ruta_proyecto, '').count(os.sep)
            indent = ' ' * 4 * (level)
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 4 * (level + 1)
            # Ignorar archivos ocultos
            for f in filenames:
                if not f.startswith('.'):
                    print(f'{subindent}{f}')

    def read_path_config_file(self, type_file: str, file_path: str):
        """
        Método que lee la ruta de un archivo de configuración desde un archivo JSON.

        :param type_file (str): Nombre del diccionario.
        :param file_path (str): Nombre de los archivos de configuración.

        :return:
            - data (str): La ruta del archivo de configuración.

        :raises FileNotFoundError: Cuando el archivo no se puede abrir.
        """
        json_path = r'Config/config_files/path_files_settings.json'
        try:
            with open(json_path, encoding='utf-8') as f:
                data = json.load(f)
                return data['path_files'][0][type_file][0][file_path]

        except FileNotFoundError:
            print(f'El archivo "{json_path}" no se pudo abrir.')
            return None

    def convert_excel_to_pdf(self, excel_file: str) -> None:
        """
        Convierte un archivo de Excel a PDF.

        :param excel_file (str): Ruta al archivo de Excel que se desea convertir.

        :return:
            - None:
        :raises OSError: Si el sistema operativo no es compatible.
        """
        pdf_file = f'{excel_file[:-5]}.pdf'
        # Detecta el sistema operativo
        if platform.system() == "Windows":
            # Importa el módulo win32com.client para trabajar con Excel en Windows
            import win32com.client
            # Crea una instancia de Excel
            excel = win32com.client.Dispatch("Excel.Application")
            # Hace que Excel no sea visible para el usuario
            excel.Visible = False
            # Abre el archivo de Excel
            workbook = excel.Workbooks.Open(os.path.abspath(excel_file))
            # Exporta el archivo a PDF
            workbook.ExportAsFixedFormat(0, os.path.abspath(pdf_file))
            # Cierra el archivo sin guardar cambios
            workbook.Close(False)
            # Cierra Excel
            excel.Quit()

        elif platform.system() == "Linux":
            # Importa el módulo subprocess para trabajar con Excel en Linux
            import subprocess
            # Define el comando para convertir el archivo de Excel a PDF utilizando LibreOffice
            command = ['libreoffice', '--headless', '--convert-to',
                       'pdf', excel_file, '--outdir', os.path.dirname(pdf_file)]
            # Ejecuta el comando
            subprocess.call(command)

        else:
            # Si el sistema operativo no es compatible, genera una excepción
            raise OSError(
                f"Sistema operativo no soportado: {platform.system()}")

    def limpiar_cache(self) -> None:
        """
        Elimina todos los archivos de caché '*.pyc' y directorios '__pycache__' 
        en todas las carpetas y subcarpetas del directorio actual.

        :return:
            - None:
        :raises None:
        """

        # Recorre recursivamente todas las carpetas y elimina los archivos de caché
        for root, dirs, files in os.walk(".", topdown=False):
            for name in files:
                # Verifica si el archivo es un archivo de caché '*.pyc'
                if name.endswith(".pyc"):
                    print(
                        f"{os.path.join(root, name)} -> Eliminando archivo de caché")
                    os.remove(os.path.join(root, name))
            for name in dirs:
                # Verifica si el directorio es un directorio de caché '__pycache__'
                if name == "__pycache__":
                    print(
                        f"{os.path.join(root, name)} -> Eliminando directorio de caché")
                    shutil.rmtree(os.path.join(root, name))

    def cifrar_AES(self, texto_plano: str):
        """
        Cifra un texto usando el algoritmo AES en modo CBC y devuelve el texto cifrado y el vector de inicialización.

        :param texto_plano (str): El texto que se va a cifrar.

        :return:
            tuple: Una tupla que contiene el texto cifrado y el vector de inicialización en formato de texto.
        """
        try:
            if not texto_plano:
                return "", ""

            # Convertir la clave en una clave de 32 caracteres
            clave_hash = hashlib.sha256(clave.encode()).digest()

            # Crear un objeto de cifrado AES
            cipher = AES.new(clave_hash, AES.MODE_CBC)

            # Cifrar el texto plano y convertirlo en una cadena de bytes
            texto_cifrado_bytes = cipher.encrypt(
                pad(texto_plano.encode(), AES.block_size))

            # Codificar la cadena de bytes en Base64 y convertirlo a cadena
            texto_cifrado = base64.b64encode(texto_cifrado_bytes).decode()

            # Obtener el vector de inicialización en formato de texto
            iv_text = base64.b64encode(cipher.iv).decode()

            # Retornar el texto cifrado y el vector de inicialización como texto
            return texto_cifrado, iv_text

        except Exception as e:
            print(e)
            traceback.print_exc()
            return False

    def descifrar_AES(self, texto_cifrado: str, iv_text: str):
        """
        Descifra un texto cifrado previamente con AES en modo CBC.

        :param texto_cifrado (str): El texto cifrado a descifrar.
        :param iv_text (str): El vector de inicialización en formato de texto.

        :return:
            str: El texto descifrado.
        """
        try:
            # Convertir la clave en una clave de 32 caracteres
            clave_hash = hashlib.sha256(clave.encode()).digest()

            # Decodificar el texto cifrado y el vector de inicialización de Base64
            texto_cifrado_bytes = base64.b64decode(texto_cifrado)
            iv = base64.b64decode(iv_text)

            # Crear un objeto de descifrado AES
            cipher = AES.new(clave_hash, AES.MODE_CBC, iv)

            # Descifrar el texto cifrado y eliminar el relleno
            texto_descifrado_bytes = cipher.decrypt(texto_cifrado_bytes)
            texto_descifrado = unpad(
                texto_descifrado_bytes,
                AES.block_size).decode()

            # Retornar el texto descifrado
            return texto_descifrado

        except Exception as e:
            print(e)
            traceback.print_exc()
            return False

    def protec_EXCEL(self, path_excel: str, password: str = "PASE") -> None:
        """
        Protege un archivo de Excel con contraseña.

        :param path_excel (str): La ruta al archivo de Excel que se desea proteger.
        :param password (str): La contraseña con la que se protegerá el archivo.

        :return:
            - None
        """
        if path.isfile(path_excel) is False:
            return

        workbook = load_workbook(path_excel)

        # Establece una contraseña para la hoja de trabajo
        worksheet = workbook.active
        worksheet.protection.set_password(password)

        # Establece una contraseña para el libro de Excel
        workbook.security = WorkbookProtection(workbookPassword=password)

        # Guarda los cambios en el archivo Excel protegido
        workbook.save(path_excel)

        print(f"El archivo '{path_excel}' ha sido protegido.'.")

    def get_letter_from_column_number(self, column: int) -> str:
        """
        Obtiene la letra de una columna a partir de su número.

        :param column (int): El número de la columna.

        :return:
            str: La letra correspondiente a la columna.
        """
        columns_letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if column <= 25:
            return columns_letters[column]
        else:
            primera_letra = columns_letters[column // 26 - 1]
            segunda_letra = columns_letters[column % 26]
            return primera_letra + segunda_letra

    def get_start_end_month(self, year_param: int, month_param: int):
        """
        Obtiene la fecha y hora de inicio y fin de un mes.

        :param year_param (int): El año para el cual se desea obtener el mes.
        :param month_param (int): El mes que se desea obtener (1-12).

        :return (tuple): Una tupla que contiene la fecha y hora de inicio y fin del mes.
                 El formato de las fechas es 'YYYY-MM-DD HH:MM:SS'.
        """

        # Obtener la fecha del primer día del mes
        first_day = date(year_param, month_param, 1)
        first_day_str = first_day.strftime('%Y-%m-%d 00:00:00')

        # Obtener la fecha del último día del mes siguiente restando un día al primer día del mes después del seleccionado
        last_day = (first_day + relativedelta(months=1)) - \
            relativedelta(days=1)

        # Convertir la fecha en formato de cadena
        last_day_str = last_day.strftime('%Y-%m-%d 23:59:59')

        return first_day_str, last_day_str

    def check_internet_connection(self, url: str = "http://www.google.com", timeout: int = 5) -> bool:
        """
        Comprueba si hay una conexión activa a Internet mediante la realización de una petición HTTP a la URL dada.

        :param url (str, opcional): La URL a la que se realizará la petición. Por defecto es "http://www.google.com".
        :param timeout (int, opcional): El tiempo máximo en segundos para esperar la respuesta. Por defecto es 5.
        :return: bool: True si hay una conexión activa a Internet, False si no se puede establecer la conexión.
        """
        try:
            response = requests.get(url, timeout=timeout)
            # Lanza una excepción si la respuesta HTTP no es exitosa
            response.raise_for_status()
            print("Conexión a Internet activa.")
            return True

        except RequestException:
            print("No se pudo establecer conexión a Internet.")
            traceback.print_exc()
            return False

    def compress_file_to_zip(self, source_file: str, output_filename: str = './db/db.zip'):
        """
        Comprime un archivo en un archivo ZIP.

        :param source_file (str): Ruta al archivo que se comprimirá.
        :param output_filename (str, opcional): Ruta y nombre del archivo ZIP de salida. Por defecto es './db/db.zip'.
        :return: str or None: Ruta absoluta del archivo ZIP si la compresión es exitosa, None si hay algún error.
        """
        try:
            with ZipFile(output_filename, 'w', ZIP_DEFLATED) as zipf:
                arcname = path.basename(source_file)
                zipf.write(source_file, arcname)
                absolute_path_zip = path.abspath(output_filename)
                return absolute_path_zip

        except Exception as e:
            print(f'Error al comprimir el archivo: {e}')
            return None

    def extract_file_from_zip(self, zip_filename: str, output_directory: str = './db/'):
        """
        Extrae un archivo desde un archivo ZIP.

        :param zip_filename (str): Ruta al archivo ZIP.
        :param output_directory (str, opcional): Directorio de salida para la extracción. Por defecto es './db/'.
        :return: str or None: Ruta absoluta del archivo descomprimido si la extracción es exitosa, None si hay algún error.
        """
        try:
            with ZipFile(zip_filename, 'r') as zip_ref:
                zip_ref.extractall(output_directory)

            extracted_files = zip_ref.namelist()
            if extracted_files:
                extracted_file = extracted_files[0]
                extracted_file_path = path.join(
                    output_directory, extracted_file)

                absolute_path_db = path.abspath(extracted_file_path)

                return absolute_path_db

        except Exception as e:
            print(f'Error al extraer el archivo: {e}')
            return None


    def remove_extra_data_from_database(self, file_path_db) -> None:
        """
        Elimina datos extra de la base de datos desde un archivo SQL.

        :param file_path_db (str): Ruta al archivo SQL que contiene los datos a eliminar.
        :return:
            - None
        """
        if path.isfile(file_path_db) is False:
            return

        # Lee el contenido del archivo SQL
        with open(file_path_db, 'r', encoding='utf-8') as file:
            sql_commands = file.readlines()
        
        first_line = sql_commands[0].strip()

        # Verificar si la primera línea contiene el comentario no deseado
        if "999999" in first_line or "enable the sandbox mode" in first_line:
            sql_commands = sql_commands[1:]

        # Reescribir el archivo con el contenido limpio
        with open(file_path_db, 'w', encoding='utf-8') as file:
            file.writelines(sql_commands)
