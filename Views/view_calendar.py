from tkinter import ttk, IntVar
import tkinter as tk
from tkcalendar import Calendar
from datetime import datetime
from datetime import date


class Calendar_date:
    """
    Clase para seleccionar una fecha y hora a través de una interfaz gráfica de usuario utilizando Tkinter y tkcalendar.

    La clase crea una ventana de Tkinter y los widgets necesarios para seleccionar una fecha y hora utilizando un calendario y cuadros de entrada de tipo Spinbox para la hora, minutos y segundos. Una vez seleccionada la fecha y hora, la función select_datetime guarda el resultado en el atributo selected_datetime y da formato a la fecha y hora seleccionada utilizando la función format_datetime.

    La función mostrar_calendario inicia el loop principal de la ventana y la función salir_calendario detiene el loop y destruye la ventana. La función get_selected_datetime retorna la fecha y hora seleccionada en formato YYYY-MM-DD HH:MM:SS.
    """

    def __init__(self, horas: int, minutos: int, segundos: int):
        """
        Inicializa la clase Fecha_Hora, crea una ventana de Tkinter y los widgets necesarios para seleccionar una fecha y hora.

        :param horas (int): Valor inicial de las horas en el cuadro de entrada.
        :param minutos (int): Valor inicial de los minutos en el cuadro de entrada.
        :param segundos (int): Valor inicial de los segundos en el cuadro de entrada.

        :raises None: 

        :return:
            - None
        """

        self.horas = int(horas)
        self.minutos = int(minutos)
        self.segundos = int(segundos)

        root = tk.Toplevel()

        # se cambia la funcionalidad del boton de cerrar
        root.protocol("WM_DELETE_WINDOW", lambda: self.salir_calendario())

        # coloca la ventana al frente de otras ventanas
        root.attributes('-topmost', True)

        # deshabilita los botones de minimizar y maximizar
        # root.attributes('-toolwindow', True)

        self.master = root
        self.master.title("Seleccionar fecha y hora")

        # width = 320
        # height = 275

        # Establece el tamaño de la ventana y su título
        pos_x = int(root.winfo_screenwidth()/2)
        pos_y = int(root.winfo_screenheight()/10)

        self.master.geometry(f"+{pos_x}+{pos_y}")
        self.master.resizable(width=False, height=False)

        # Creamos variables de cadena para los campos de hora, minutos y segundos
        self.hour = IntVar()
        self.min = IntVar()
        self.sec = IntVar()

        self.hour.set(self.horas)
        self.min.set(self.minutos)
        self.sec.set(self.segundos)

        # Almacena la fecha y hora seleccionada
        self.selected_datetime = ""

        # Fuente para los widgets
        f = ('Times', 20)
        # Creamos dos marcos para colocar los widgets
        self.fone = ttk.LabelFrame(self.master, text='Calendario')
        self.ftwo = ttk.LabelFrame(self.master, text='Botones')

        self.fone.grid(row=0, column=0, padx=10)
        self.ftwo.grid(row=1, column=0, padx=10)

        # Creamos un calendario para seleccionar una fecha
        self.cal = Calendar(self.fone, selectmode="day", locale="es_ES", year=date.today(
        ).year, month=date.today().month, day=date.today().day)
        self.cal.pack()

        # Creamos tres cuadros de entrada de tipo Spinbox para seleccionar la hora, minutos y segundos
        self.hour_text = ttk.Spinbox(self.ftwo, from_=0, to=23, wrap=True,
                                     textvariable=self.hour, width=2, state="readonly", font=f, justify=tk.CENTER)
        self.min_text = ttk.Spinbox(self.ftwo, from_=0, to=59, wrap=True,
                                    textvariable=self.min, width=2, state="readonly", font=f, justify=tk.CENTER)
        self.sec_text = ttk.Spinbox(self.ftwo, from_=0, to=59, wrap=True,
                                    textvariable=self.sec, width=2, state="readonly", font=f, justify=tk.CENTER)

        # Añadimos los cuadros de entrada a la ventana
        self.hour_text.grid(row=0, column=0)
        self.min_text.grid(row=0, column=1)
        self.sec_text.grid(row=0, column=2)

        # Etiqueta que indica la función de los cuadros de entrada
        self.msg = ttk.Label(
            self.master, text="Hora  Minuto  Segundo", font=("Times", 12))
        self.msg.grid(row=2, column=0)

        s = ttk.Style()
        s.configure('my.TButton', font=("Times", 12))

        # Botón que llama a la función select_datetime() al hacer clic
        self.actionBtn = ttk.Button(self.master, text="Selecciona fecha y hora",
                                    command=self.select_datetime, style='my.TButton', width=20)
        self.actionBtn.grid(row=3, column=0, sticky=tk.S)

    def mostrar_calendario(self) -> None:
        """Ejecutar calendario"""
        self.master.mainloop()
        # self.master.wait_window()

    def salir_calendario(self) -> None:
        """Salir del calendario"""
        # detener el loop principal
        self.master.quit()
        # Destruye el panel principal
        self.master.destroy()

    def format_datetime(self, date: str, hour: int, minute: int, second: int) -> str:
        """
        Función que da formato a la fecha y hora seleccionada.

        :param date (str): Cadena que representa la fecha en formato dd/mm/aa.
        :param hour (int): Hora seleccionada en formato de 24 horas.
        :param minute (int): Minutos seleccionados.
        :param second (int): Segundos seleccionados.

        :return:
            - formate_date (str): Cadena que representa la fecha y hora seleccionada en formato YYYY-MM-DD HH:MM:SS.

        :raises None:
        """
        date_obj = datetime.strptime(date, "%d/%m/%y")
        date_str = date_obj.strftime("%Y-%m-%d")

        time_str = f"{hour:02}:{minute:02}:{second:02}"

        formate_date = f"{date_str} {time_str}"

        return formate_date

    def select_datetime(self) -> None:
        """
        Función que guarda la fecha y hora seleccionada.

        Obtiene la fecha seleccionada en el calendario y la hora, minutos y segundos
        seleccionados en los Spinboxes. Luego, utiliza la función format_datetime
        para dar formato a la fecha y hora seleccionada y guarda el resultado en
        el atributo selected_datetime."""
        date = self.cal.get_date()
        hour = int(self.hour.get())
        minute = int(self.min.get())
        second = int(self.sec.get())

        # Dar formato a la fecha y hora seleccionada
        self.selected_datetime = self.format_datetime(
            date, hour, minute, second)
        # print(self.selected_datetime)

        # Destruir la ventana principal
        self.salir_calendario()
