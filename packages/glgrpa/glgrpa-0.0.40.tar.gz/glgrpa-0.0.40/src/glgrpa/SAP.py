# src/glgrpa/SAP.py

# Importaciones necesarias
import os
from selenium.webdriver.common.by import By

from .Chrome import Chrome
from .Terminal import Terminal

class SAP(Chrome, Terminal):
    def __init__(self, base_url: str, dev: bool = False):
        super().__init__(dev)
        self.base_url = base_url
        
        self.autentificacion_http_activo = False
        self.autentificacion_sap_activo = False
        self.autentificacion_microsoft_activo = False
        
        self.usuario_sap = ""
        self.clave_sap = ""
        
    def set_credenciales_usuario(self, usuario: str, clave: str):
        """ Configura las credenciales de usuario para SAP """
        self.usuario_sap = usuario
        self.clave_sap = clave
        self.mostrar(f"Credenciales configuradas para {self.usuario_sap}")
            
    def navegar_inicio_SAP(self):
        """ Navega a la página de inicio de SAP """
        self.driver = self.obtener_driver()
        self.navegar(self.base_url)
            
        if self._autentificacion_http():
            import pyautogui
            pyautogui.hotkey('shift', 'tab')
            pyautogui.press('enter')
            self.demora(2)
            self.autentificacion_http_activo = False
            
        if self._autentificacion_sap():
            self._ingresar_usuario()
            self._ingresar_contrasena(enter=True)
        
        if self._autentificacion_microsoft():
            self._ingresar_usuario()
            self._ingresar_contrasena()
            self._no_mantener_sesion_iniciada()
    
    def _autentificacion_http(self) -> bool:
        """ Verifica si la autenticación HTTP está activa """
        if self.driver.title == "": self.autentificacion_http_activo = True
        return self.autentificacion_http_activo
    
    def _autentificacion_sap(self) -> bool:
        """ Verifica si la autenticación de SAP está activa """
        if self.driver.title == "SAP Logon - SAP GUI for Windows": self.autentificacion_sap_activo = True
        return self.autentificacion_sap_activo
    
    def _autentificacion_microsoft(self) -> bool:
        """ Verifica si la autenticación de Microsoft está activa """
        if self.driver.title == "Iniciar sesión en la cuenta": self.autentificacion_microsoft_activo = True
        return self.autentificacion_microsoft_activo
            
    def _ingresar_usuario(self, tab: bool = False) -> bool:
        """ Ingresa el usuario de SAP """
        self.mostrar("Ingresando usuario de SAP")
        
        # Autenticación Microsoft
        if self.autentificacion_microsoft_activo:
            self.ingresar_texto(By.NAME ,'loginfmt', self.usuario_sap) 
            self.click_button("Siguiente", By.ID, 'idSIButton9')
            if self._ingreso_correcto():
                self.mostrar("Usuario ingresado correctamente")
                return True
            return False
        
        # Autenticación SAP
        if self.autentificacion_sap_activo:
            self.ingresar_texto(By.ID, 'USERNAME_FIELD-inner', self.usuario_sap)
            self.click_button("Continuar", By.ID, 'LOGIN_BUTTON')
            if self._ingreso_correcto():
                self.mostrar("Usuario ingresado correctamente")
                return True
            return False
        
        if tab:
            import pyautogui
            pyautogui.press('tab')
        
        return False
    
    def _ingresar_contrasena(self, enter: bool = False) -> bool:
        """ Ingresa la contraseña de SAP """
        self.mostrar("Ingresando contraseña de SAP")
        
        # Autenticación Microsoft
        if self.autentificacion_microsoft_activo:
            self.ingresar_texto(By.ID, 'i0118', self.clave_sap)
            self.click_button("Iniciar sesión", By.ID, 'idSIButton9')
            if self._ingreso_correcto():
                self.mostrar("Contraseña ingresada correctamente")
                return True
            return False
            
        # Autenticación SAP
        if self.autentificacion_sap_activo:
            self.ingresar_texto(By.ID, 'PASSWORD_FIELD-inner', self.clave_sap)
            self.click_button("Continuar", By.ID, 'LOGIN_BUTTON')
            if self._ingreso_correcto():
                self.mostrar("Contraseña ingresada correctamente")
                return True
            return False
        
        if enter:
            import pyautogui
            pyautogui.press('enter')
        
        return False
    
    def _no_mantener_sesion_iniciada(self):
        """ Selecciona la opción de no mantener la sesión iniciada """
        self.mostrar("Seleccionando opción de no mantener sesión iniciada")
        try:
            self.click_button("No", By.ID, 'idBtn_Back')
            if self._ingreso_correcto():
                self.mostrar("Opción de no mantener sesión iniciada seleccionada correctamente")
                return True
        except Exception as e:
            self.mostrar(f"Error al seleccionar la opción de no mantener sesión iniciada: {e}", True)
        return False
    
    def _ingreso_correcto(self) -> bool:
        """ Verifica que se haya ingresado correctamente """
        # Aquí se puede implementar una lógica para verificar el ingreso correcto
        # Por ejemplo, verificar si se ha redirigido a la página principal de SAP
        if self.encontrar_elemento(By.XPATH, '//*[@id="loginHeader"]/div', False):
            return True
        if self.encontrar_elemento(By.XPATH, '//*[@id="lightbox"]/div[3]/div/div[2]/div/div[1]', False):
            return True
        if self.driver.title == "Página de inicio":
            return True
        
        return False
    
    def cerrar_sesion(self):
        """ Cierra la sesión de SAP """
        self.mostrar("Cerrando sesión de SAP")
        self.click_elemento(By.ID, "id_logout")
        self.demora()
        if "Login" in self.driver.title:
            self.mostrar("Sesión cerrada correctamente")
        else:
            self.mostrar("Error al cerrar sesión", True)
            
    def ir_a_transaccion(self, transaccion: str):
        """ Navega a una transacción específica en SAP """
        transaccion_correcta = self._transaccion_correcta(transaccion)
        if transaccion_correcta is None: return
        
        if transaccion_correcta == 'url':
            self.navegar(transaccion)
        elif transaccion_correcta == 'url-relative':
            self.navegar(f"{self.base_url}{transaccion}")    
        else:
            self._buscar_transaccion(transaccion)
        
    def _transaccion_correcta(self, transaccion: str) -> str|None:
        """ Verifica si la transacción es correcta """
        if transaccion.startswith("http"): 
            return 'url'
        elif transaccion.startswith("#Shell-"):
            return 'url-relative'
        elif len(transaccion) <= 10 and transaccion.isalnum(): 
            return 'codigo'
        else:
            self.mostrar(f"Transacción {transaccion} no es válida", True)
        return None
    
    def _buscar_transaccion(self, transaccion: str) -> bool:
        """ Busca una transacción en SAP """
        menues = ['catalog', 'userMenu', 'sapMenu']
        for menu in menues:
            self.navegar(f"{self.base_url}#Shell-appfinder&/{menu}")
            
            self.ingresar_texto(By.ID, 'appFinderSearch-I', transaccion)
            self.presionar_enter(By.ID, 'appFinderSearch-I')
            
            if self.encontrar_elemento(By.ID, '__page0-text', False):
                mensaje = self.obtener_texto_elemento(By.ID, '__page0-text')
                if "No hay ninguna aplicación para visualizar" in mensaje:
                    self.mostrar(f"No se encontró la transacción {transaccion} en el menú {menu}", True)
                    continue
            
            grilla_transacciones = self.encontrar_elemento(By.ID, 'userMenuViewhierarchyAppsSearchResults_hierarchyAppsLayout', False)
            if grilla_transacciones:
                self.click_elemento_desde_elemento(grilla_transacciones, By.TAG_NAME, 'div')
                self.mostrar(f"Transacción {transaccion} encontrada en el menú {menu}")
                return True
            
        self.mostrar(f"No se encontró la transacción {transaccion} en ninguno de los menús", True)
        return False