# auth_handler.py
#chuta2
import streamlit as st
import requests
import json
from typing import Optional, Dict


class AuthHandler:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def register_user(self, username: str, email: str, password: str) -> bool:
        try:
            response = requests.post(
                f"{self.base_url}/auth/register",
                json={"username": username, "email": email, "password": password}
            )
            if response.ok:
                st.success("✅ Usuario registrado exitosamente")
                return True
            else:
                st.error(f"❌ Error: {response.json().get('detail', 'Error desconocido')}")
                return False
        except Exception as e:
            st.error(f"❌ Error de conexión: {str(e)}")
            return False

    def login_user(self, email: str, password: str) -> bool:
        """Iniciar sesión"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                data={"username": email, "password": password}
            )
            if response.status_code == 200:
                tokens = response.json()
                st.session_state.access_token = tokens["access_token"]
                st.session_state.refresh_token = tokens.get("refresh_token")
                st.session_state.is_authenticated = True
                return True
            else:
                st.error("❌ Credenciales incorrectas")
                return False
        except Exception as e:
            st.error(f"❌ Error de conexión: {str(e)}")
            return False

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

    def get_user_info(self) -> Optional[Dict]:
        try:
            headers = self.get_headers()
            response = requests.get(f"{self.base_url}/auth/me", headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                st.error("❌ No se pudo obtener información del usuario")
                return None
        except Exception as e:
            st.error(f"❌ Error de conexión: {str(e)}")
            return None
