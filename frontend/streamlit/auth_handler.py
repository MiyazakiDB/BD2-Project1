# auth_handler.py
import streamlit as st
import requests
import json
from typing import Optional, Dict


class AuthHandler:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def register_user(self, name: str, email: str, password: str) -> bool:
        """Registrar nuevo usuario"""
        try:
            response = requests.post(
                f"{self.base_url}/register",
                json={"name": name, "email": email, "password": password}
            )
            if response.status_code == 200:
                st.success("✅ Usuario registrado exitosamente")
                return True
            else:
                st.error(f"❌ Error: {response.json().get('detail', 'Error desconocido')}")
                return False
        except Exception as e:
            st.error(f"❌ Error de conexión: {str(e)}")
            return False

    def login_user(self, email: str, password: str) -> Optional[Dict]:
        """Iniciar sesión"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                data={"username": email, "password": password}
            )
            if response.status_code == 200:
                user_data = response.json()
                # Guardar tokens en session_state
                st.session_state.access_token = user_data["access_token"]
                st.session_state.user_info = user_data["user"]
                st.session_state.is_authenticated = True
                return user_data
            else:
                st.error("❌ Credenciales incorrectas")
                return None
        except Exception as e:
            st.error(f"❌ Error de conexión: {str(e)}")
            return None

    def logout(self):
        """Cerrar sesión"""
        for key in ["access_token", "user_info", "is_authenticated"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    def get_headers(self) -> Dict[str, str]:
        """Obtener headers con token de autorización"""
        if "access_token" in st.session_state:
            return {"Authorization": f"Bearer {st.session_state.access_token}"}
        return {}

    def is_authenticated(self) -> bool:
        """Verificar si el usuario está autenticado"""
        return st.session_state.get("is_authenticated", False)