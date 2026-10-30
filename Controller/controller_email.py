from Tools.proyect_tools import Tools

import smtplib
import imaplib

from email import message_from_bytes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from datetime import datetime

import traceback

from os import path, remove


class SendEmail:
    def __init__(self, username: str, password: str, estacionamiento: str, smtp_server: str = "smtp.pasesa.com.mx", smtp_port: int = 1025) -> None:
        """
        Inicializa una instancia de la clase SendEmail para enviar correos electrónicos con archivos adjuntos.

        :param username (str): El nombre de usuario para la cuenta de correo electrónico.
        :param password (str): La contraseña para la cuenta de correo electrónico.
        :param estacionamiento (str): Nombre del estacionamiento, utilizado en el nombre del archivo adjunto.
        :param smtp_server (str, opcional): El servidor SMTP para el envío de correos. Por defecto es "smtp.pasesa.com.mx".
        :param smtp_port (int, opcional): El puerto del servidor SMTP. Por defecto es 1025.
        :return: None
        """
        self.username = username
        self.password = password
        self.estacionamiento = estacionamiento
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.tools = Tools()

    def send_mail(self, to_email: str, subject: str, message: str, file: str) -> bool:
        """
        Envía un correo electrónico con un archivo adjunto.

        :param to_email (str): La dirección de correo electrónico del destinatario.
        :param subject (str): El asunto del correo electrónico.
        :param message (str): El contenido del correo electrónico.
        :param file (str): Ruta al archivo que se adjuntará al correo.
        :return: bool: True si el correo se envía exitosamente, False si hay algún error.
        """
        from_email = self.username

        # Verificar la conexión a Internet antes de intentar enviar el correo
        if self.tools.check_internet_connection() == False:
            return False

        try:
            # Crea la estructura del correo
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(message, 'plain'))

            # Adjuntar el archivo al correo
            with open(file, 'rb') as f:
                attached_file = MIMEApplication(f.read(), _subtype="sql")
                attached_file.add_header(
                    'content-disposition', 'attachment', filename=f'{self.estacionamiento}_DB.sql')
                msg.attach(attached_file)

            # Conectar al servidor SMTP y enviar el correo
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                # Iniciar la conexión segura TLS
                server.starttls()
                # Inicio de sesión
                server.login(self.username, self.password)
                # Enviar correo
                server.sendmail(from_email, to_email, msg.as_string())
                # Terminar la sesión
                server.quit()

            print('Correo enviado exitosamente.')
            return True

        except Exception as e:
            print(e)
            traceback.print_exc()
            return False


class ReciveEmail:
    def __init__(self, username: str, password: str, imap_server: str = "pop.pasesa.com.mx", imap_port: int = 993) -> None:
        """
        Inicializa una instancia de la clase ReciveEmail para recibir correos electrónicos y descargar archivos adjuntos.

        :param username (str): El nombre de usuario para la cuenta de correo electrónico.
        :param password (str): La contraseña para la cuenta de correo electrónico.
        :param imap_server (str, opcional): El servidor IMAP para la recepción de correos. Por defecto es "outlook.office365.com".
        :param imap_port (int, opcional): El puerto del servidor IMAP. Por defecto es 993.
        :return: None
        """
        self.username = username
        self.password = password
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.tools = Tools()

    def recive_last_mail(self, email_filter: str):
        """
        Recibe el último correo que cumple con el filtro de dirección de correo electrónico y descarga archivos adjuntos si los hay.

        :param email_filter (str): El filtro de dirección de correo electrónico para buscar correos específicos.
        :return: tuple or None or bool: Una tupla que contiene la fecha formateada del último correo con archivo adjunto descargado y la ruta al archivo descargado. Retorna None si no se encuentra ningún correo o False si ocurre un error.
        """
        # Verificar la conexión a Internet antes de intentar recibir el correo
        if self.tools.check_internet_connection() == False:
            return False

        try:
            # Conéctate al servidor y puerto IMAP dado
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.username, self.password)

            # Selecciona la bandeja de entrada
            mail.select("inbox")

            download_directory = "./db/"

            search_criteria = f'(FROM {email_filter})'
            status, email_ids = mail.search(None, search_criteria)
            email_ids = email_ids[0].split()

            # Si no hay resultados, retorna None
            if len(email_ids) == 0:
                return None

            last_email_id = email_ids[-1]

            status, email_data = mail.fetch(last_email_id, "(RFC822)")
            raw_email = email_data[0][1]
            msg = message_from_bytes(raw_email)
            date_str = msg["Date"]

            # Convertir la fecha a un objeto datetime
            date_obj = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")

            # Formatear la fecha en el formato deseado
            formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            formatted_date = datetime.strptime(
                formatted_date, "%Y-%m-%d %H:%M:%S")

            # Verifica si el correo tiene archivos adjuntos
            if msg.get_content_maintype() == "multipart":
                for part in msg.walk():
                    content_subtype = part.get_content_subtype()

                    if "zip" in content_subtype:
                        filename = part.get_filename()

                        file_path_zip = download_directory + filename

                        with open(file_path_zip, "wb") as file:
                            file.write(part.get_payload(decode=True))

                        print(f"Archivo descargado: en {file_path_zip}")

                        file_path = self.tools.extract_file_from_zip(
                            file_path_zip,
                            download_directory)

                        if file_path:
                            try:
                                remove(file_path_zip)
                                print("Archivo .zip eliminado exitosamente.")
                            except Exception as e:
                                print(
                                    f"No se pudo eliminar el archivo .zip: {e}")

                        return formatted_date, file_path

            # Cierra la conexión
            mail.logout()

        except Exception as e:
            print(e)
            traceback.print_exc()
            return False
