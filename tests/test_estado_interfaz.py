import unittest
from unittest.mock import Mock, patch

from Controller.controller_select_conection import Controller_Select_Conection
from Views.view_select_conection import View_Conect


class EstadoInterfazTests(unittest.TestCase):
    def test_controlador_exige_admin_antes_de_crear_ventana(self):
        controlador = Controller_Select_Conection.__new__(Controller_Select_Conection)
        controlador.permiso = 'normal'
        with patch('Views.view_estado_actualizaciones.ViewEstadoActualizaciones') as vista:
            with self.assertRaises(PermissionError):
                controlador.abrir_estado_actualizacion(Mock(), 'ficticio.sqlite3')
        vista.assert_not_called()

    def test_controlador_usa_lector_local_no_actualizador(self):
        controlador = Controller_Select_Conection.__new__(Controller_Select_Conection)
        controlador.permiso = 'admin'
        controlador.config = Mock()
        padre = Mock()
        with patch('Models.estado_actualizaciones.EstadoActualizaciones') as modelo, \
             patch('Views.view_estado_actualizaciones.ViewEstadoActualizaciones') as vista:
            controlador.abrir_estado_actualizacion(padre, 'ficticio.sqlite3')
        modelo.assert_called_once_with(controlador.config, 'ficticio.sqlite3')
        vista.assert_called_once_with(padre, modelo.return_value)

    def test_selector_reutiliza_y_refresca_ventana_existente(self):
        selector = View_Conect.__new__(View_Conect)
        selector.estado_actualizacion = Mock()
        selector.select_controller = Mock()
        selector.estado_actualizacion.window.winfo_exists.return_value = True
        selector.abrir_estado_actualizacion()
        selector.estado_actualizacion.refrescar.assert_called_once()
        selector.estado_actualizacion.window.lift.assert_called_once()
        selector.select_controller.abrir_estado_actualizacion.assert_not_called()

    def test_selector_reabre_ventana_cerrada(self):
        selector = View_Conect.__new__(View_Conect)
        selector.estado_actualizacion = Mock()
        selector.estado_actualizacion.window.winfo_exists.return_value = False
        selector.panel_connect = Mock()
        selector.select_controller = Mock()
        selector.abrir_estado_actualizacion()
        selector.select_controller.abrir_estado_actualizacion.assert_called_once_with(selector.panel_connect)

    def test_error_catalogo_no_muestra_excepcion_con_datos_sensibles(self):
        selector = View_Conect.__new__(View_Conect)
        selector.panel_connect = Mock()
        selector.select_controller = Mock()
        selector.select_controller.abrir_estado_actualizacion.side_effect = ValueError('SECRETO_FICTICIO')
        with patch('tkinter.messagebox.showerror') as error:
            selector.abrir_estado_actualizacion()
        error.assert_called_once()
        self.assertNotIn('SECRETO_FICTICIO', str(error.call_args))
