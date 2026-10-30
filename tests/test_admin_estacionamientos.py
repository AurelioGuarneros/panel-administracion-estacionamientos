"""Pruebas sin GUI, configuración real, correo ni acceso a bases de datos."""
import ast
from pathlib import Path
import unittest
from unittest.mock import Mock, MagicMock, patch
from Views.view_admin_estacionamientos import ViewAdminEstacionamientos


def clase_aislada(ruta, nombre):
    # Extrae solamente la clase; evita importar reportes y sus dependencias reales.
    arbol = ast.parse(Path(ruta).read_text(encoding="utf-8"))
    nodo = next(n for n in arbol.body if isinstance(n, ast.ClassDef) and n.name == nombre)
    espacio = {}
    exec(compile(ast.Module(body=[nodo], type_ignores=[]), ruta, 'exec'), espacio)
    return espacio[nombre]


class AdminTests(unittest.TestCase):
    def test_ventana_denegada_sin_crear_gui(self):
        for permiso in (None, 'normal'):
            with self.assertRaises(PermissionError):
                ViewAdminEstacionamientos(None, Mock(), Mock(), permiso)

    def test_confirmacion_cancelada_y_aceptada(self):
        vista = ViewAdminEstacionamientos.__new__(ViewAdminEstacionamientos)
        vista.modelo = Mock()
        vista.window = Mock()
        vista.on_change = Mock()
        vista.recargar = Mock()
        vista.seleccionado = Mock(return_value={'name_config': 'Ficticio'})
        for aceptar in (False, True):
            with patch('Views.view_admin_estacionamientos.messagebox.askyesno', return_value=aceptar):
                vista.cambiar_estado()
            if aceptar:
                vista.modelo.cambiar_estado.assert_called_once_with('Ficticio', False)
            else:
                vista.modelo.cambiar_estado.assert_not_called()
                vista.on_change.assert_not_called()
                vista.recargar.assert_not_called()

    def test_lectura_inicial_falla_sin_crear_ventana(self):
        modelo = Mock(permiso='admin')
        modelo.listar.side_effect = ValueError('JSON ficticio inválido')
        with patch('Views.view_admin_estacionamientos.tk.Toplevel') as ventana:
            with self.assertRaises(ValueError):
                ViewAdminEstacionamientos(None, modelo, Mock(), 'admin')
            ventana.assert_not_called()

    def test_fallo_construccion_destruye_ventana(self):
        modelo = Mock(permiso='admin')
        modelo.listar.return_value = []
        with patch('Views.view_admin_estacionamientos.tk.Toplevel') as ventana, patch.object(ViewAdminEstacionamientos, 'construir', side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):
                ViewAdminEstacionamientos(None, modelo, Mock(), 'admin')
            ventana.return_value.destroy.assert_called_once()

    def test_tabla_desplazable_y_pantalla_pequena(self):
        vista = ViewAdminEstacionamientos.__new__(ViewAdminEstacionamientos)
        vista.window = Mock()
        vista.window.winfo_screenwidth.return_value = 480
        vista.window.winfo_screenheight.return_value = 480
        vista.recargar = Mock()
        tabla = MagicMock()
        tabla.__getitem__.return_value = ('nombre', 'email', 'database', 'estado')
        with patch('Views.view_admin_estacionamientos.ttk.Frame'), patch('Views.view_admin_estacionamientos.ttk.Treeview', return_value=tabla), patch('Views.view_admin_estacionamientos.ttk.Scrollbar') as scroll, patch('Views.view_admin_estacionamientos.ttk.Label'), patch('Views.view_admin_estacionamientos.ttk.Entry'), patch('Views.view_admin_estacionamientos.ttk.Combobox'), patch('Views.view_admin_estacionamientos.ttk.Button'), patch('Views.view_admin_estacionamientos.tk.StringVar'):
            vista.construir([])
        vista.window.geometry.assert_called_once_with('440x400')
        self.assertEqual([c.kwargs['orient'] for c in scroll.call_args_list], ['vertical', 'horizontal'])
        self.assertEqual(tabla.configure.call_args.kwargs.keys(), {'yscrollcommand', 'xscrollcommand'})
        tabla.grid.assert_called_once_with(row=0, column=0, sticky='nsew')
        vista.recargar.assert_called_once_with([])

    def test_guardado_exitoso_con_fallo_de_refresco(self):
        for destino in ('on_change', 'recargar'):
            vista = ViewAdminEstacionamientos.__new__(ViewAdminEstacionamientos)
            vista.window = Mock()
            vista.on_change, vista.recargar = Mock(), Mock()
            getattr(vista, destino).side_effect = OSError('Fallo ficticio')
            operacion = Mock()
            with patch('Views.view_admin_estacionamientos.messagebox.showwarning') as aviso, patch('Views.view_admin_estacionamientos.messagebox.showerror') as error:
                vista.ejecutar(operacion)
            operacion.assert_called_once()
            vista.on_change.assert_called_once()
            vista.recargar.assert_called_once()
            aviso.assert_called_once()
            self.assertIn('El archivo se guardó', aviso.call_args.args[1])
            error.assert_not_called()

    def test_controlador_propaga_fallo_al_refrescar(self):
        clase = clase_aislada('Controller/controller_select_conection.py', 'Controller_Select_Conection')
        controlador = clase.__new__(clase)
        controlador.config = Mock()
        controlador.config.activos.side_effect = ValueError('Ficticio')
        with self.assertRaises(ValueError):
            controlador.get_db_list(propagar_error=True)

    def test_refrescar_selector_y_cero_activos(self):
        clase = clase_aislada('Views/view_select_conection.py', 'View_Conect')
        vista = clase.__new__(clase)
        vista.select_controller = Mock()
        vista.variable_estacionamiento = Mock()
        vista.variable_estacionamiento.get.return_value = 'Anterior'
        vista.lista_desplegable_opciones = Mock()
        vista.boton_seleccionar = Mock()
        vista.estado_catalogo = Mock()
        for opciones, seleccionado in ((['Anterior', 'Nuevo'], 'Anterior'), (['Nuevo'], 'Nuevo'), ([], '')):
            vista.select_controller.get_db_list.return_value = ([], opciones)
            vista.actualizar_estacionamientos()
            vista.variable_estacionamiento.set.assert_called_with(seleccionado)
            vista.boton_seleccionar.configure.assert_called_with(state='normal' if opciones else 'disabled')

    def test_error_guardado_no_notifica_cambio(self):
        vista = ViewAdminEstacionamientos.__new__(ViewAdminEstacionamientos)
        vista.window = Mock()
        vista.on_change = Mock()
        vista.recargar = Mock()
        with patch('Views.view_admin_estacionamientos.messagebox.showerror'):
            vista.ejecutar(Mock(side_effect=OSError))
        vista.on_change.assert_not_called()
        vista.recargar.assert_not_called()

    def test_controlador_rechaza_inactivos_y_acceso_no_admin(self):
        from Models.estacionamientos_config import exigir_admin
        clase = clase_aislada('Controller/controller_select_conection.py', 'Controller_Select_Conection')
        espacio = clase.conectar.__globals__
        espacio.update(messagebox=Mock(), View_Report=Mock(), exigir_admin=exigir_admin)
        controlador = clase.__new__(clase)
        controlador.config = Mock()
        controlador.config.activos.return_value = [{'name_config': 'Activo'}]
        controlador.conectar('Inactivo', 'Usuario ficticio', {})
        espacio['View_Report'].assert_not_called()
        controlador.conectar('Activo', 'Usuario ficticio', {})
        espacio['View_Report'].assert_called_once()
        controlador.permiso = 'normal'
        with self.assertRaises(PermissionError):
            controlador.abrir_administracion(None, Mock())

    def test_guardado_notifica_inmediatamente(self):
        vista = ViewAdminEstacionamientos.__new__(ViewAdminEstacionamientos)
        vista.on_change = Mock()
        vista.recargar = Mock()
        operacion = Mock()
        vista.ejecutar(operacion)
        operacion.assert_called_once()
        vista.on_change.assert_called_once()
        vista.recargar.assert_called_once()

    def test_sintaxis_archivos_y_rol_desde_login(self):
        for ruta in ('Controller/controller_login.py', 'Controller/controller_select_conection.py', 'Views/view_select_conection.py'):
            ast.parse(Path(ruta).read_text(encoding="utf-8"))
        arbol = ast.parse(Path('Controller/controller_login.py').read_text(encoding="utf-8"))
        llamada = next(n for n in ast.walk(arbol) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'View_Conect')
        permiso = next(k.value for k in llamada.keywords if k.arg == 'permiso')
        self.assertEqual(ast.unparse(permiso), "user_data['Permits']")
