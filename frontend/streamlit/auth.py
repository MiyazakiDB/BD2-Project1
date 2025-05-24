import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Auth App", layout="centered")

st.title("🔐 Autenticación de Usuarios")

# Tabs para Login y Registro
tab = st.radio("Selecciona una opción", ["Iniciar Sesión", "Registrarse"], horizontal=True)

username = st.text_input("Nombre de usuario")
password = st.text_input("Contraseña", type="password")

if tab == "Iniciar Sesión":
    if st.button("Ingresar"):
        if username and password:
            response = requests.post(f"{API_URL}/login", data={
                "username": username,
                "password": password
            })
            if response.status_code == 200:
                st.success(f"Bienvenido, {username} 👋")
            else:
                st.error(f"Error: {response.json().get('detail')}")
        else:
            st.warning("Por favor ingresa todos los campos.")
else:  # Registrarse
    if st.button("Registrarse"):
        if username and password:
            response = requests.post(f"{API_URL}/register", data={
                "username": username,
                "password": password
            })
            if response.status_code == 200:
                st.success("Registro exitoso ✅")
            else:
                st.error(f"Error: {response.json().get('detail')}")
        else:
            st.warning("Por favor ingresa todos los campos.")
