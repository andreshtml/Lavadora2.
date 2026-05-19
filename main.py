import sqlite3
import os
from datetime import datetime, timedelta
import customtkinter as ctk
from tkinter import messagebox, ttk

# === CONFIGURACIÓN DE APARIENCIA ===
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

PRECIO_POR_HORA_USD = 1.0 

class SistemaAlquiler(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AUTÉNTICOS EXPRES - Sistema de Control")
        self.geometry("1200x780")
        
        self.repartidor_logueado_id = None 
        self.usuario_actual = None
        
        self.init_db()
        self.mostrar_login()

    # === BASE DE DATOS ULTRA-ESTABLE ===
    def init_db(self):
        conn = sqlite3.connect('autenticos_expres.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                            user TEXT PRIMARY KEY, 
                            pwd TEXT NOT NULL, 
                            rol TEXT NOT NULL)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS lavadoras (
                            id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            codigo TEXT UNIQUE NOT NULL, 
                            marca TEXT NOT NULL, 
                            capacidad REAL NOT NULL,
                            estado TEXT DEFAULT 'Disponible')''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            nombre TEXT NOT NULL, 
                            telefono TEXT NOT NULL, 
                            direccion TEXT NOT NULL,
                            email TEXT)''')
                            
        cursor.execute('''CREATE TABLE IF NOT EXISTS repartidores (
                            id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            nombre TEXT NOT NULL, 
                            telefono TEXT NOT NULL, 
                            estatus TEXT DEFAULT 'Disponible',
                            usuario_asociado TEXT UNIQUE NOT NULL,
                            FOREIGN KEY(usuario_asociado) REFERENCES usuarios(user) ON DELETE CASCADE ON UPDATE CASCADE)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS alquileres (
                            id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            id_cliente INTEGER NOT NULL, 
                            id_lavadora INTEGER NOT NULL, 
                            id_repartidor INTEGER NOT NULL, 
                            fecha_vencimiento DATETIME NOT NULL, 
                            monto REAL NOT NULL, 
                            metodo_pago TEXT NOT NULL, 
                            moneda TEXT NOT NULL, 
                            estatus TEXT DEFAULT 'Activo',
                            FOREIGN KEY(id_cliente) REFERENCES clientes(id) ON DELETE RESTRICT,
                            FOREIGN KEY(id_lavadora) REFERENCES lavadoras(id) ON DELETE RESTRICT,
                            FOREIGN KEY(id_repartidor) REFERENCES repartidores(id) ON DELETE RESTRICT)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS hoja_ruta (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            id_alquiler INTEGER NOT NULL,
                            tipo_viaje TEXT NOT NULL, 
                            estatus_viaje TEXT DEFAULT 'Pendiente',
                            FOREIGN KEY(id_alquiler) REFERENCES alquileres(id) ON DELETE CASCADE)''')
        
        cursor.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', '1234', 'Admin')")
        cursor.execute("INSERT OR IGNORE INTO usuarios VALUES ('juan', '0000', 'Repartidor')")
        cursor.execute("INSERT OR IGNORE INTO repartidores (id, nombre, telefono, estatus, usuario_asociado) VALUES (1, 'Juan', '04121234567', 'Disponible', 'juan')")
        
        conn.commit()
        conn.close()

    def obtener_conexion(self):
        conn = sqlite3.connect('autenticos_expres.db')
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    # === INTERFAZ DE LOGIN ===
    def mostrar_login(self):
        self.login_frame = ctk.CTkFrame(self, width=350, height=380)
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(self.login_frame, text="AUTÉNTICOS EXPRES", font=("sans-serif", 20, "bold"), text_color="#3498db").pack(pady=25)
        self.user_ent = ctk.CTkEntry(self.login_frame, placeholder_text="Usuario", width=240)
        self.user_ent.pack(pady=10)
        
        self.pwd_ent = ctk.CTkEntry(self.login_frame, placeholder_text="Contraseña", show="*", width=240)
        self.pwd_ent.pack(pady=10)
        
        self.pwd_ent.bind("<Return>", lambda event: self.validar_login())
        
        ctk.CTkButton(self.login_frame, text="Iniciar Sesión", command=self.validar_login, width=240).pack(pady=25)

    def validar_login(self):
        u, p = self.user_ent.get().strip(), self.pwd_ent.get()
        conn = self.obtener_conexion()
        res = conn.execute("SELECT rol FROM usuarios WHERE user=? AND pwd=?", (u, p)).fetchone()
        
        if res:
            rol = res[0]
            self.usuario_actual = u
            if rol == "Repartidor":
                rep_info = conn.execute("SELECT id FROM repartidores WHERE usuario_asociado=?", (u,)).fetchone()
                self.repartidor_logueado_id = rep_info[0] if rep_info else 1
            conn.close()
            
            self.login_frame.destroy()
            if rol == "Admin":
                self.construir_interfaz_admin()
                self.bucle_monitoreo_automatico()
            else:
                self.construir_interfaz_repartidor()
        else:
            conn.close()
            messagebox.showerror("Error", "Credenciales incorrectas")

    def cerrar_sesion(self):
        if hasattr(self, 'menu_lateral') and self.menu_lateral: self.menu_lateral.destroy()
        if hasattr(self, 'contenedor') and self.contenedor: self.contenedor.destroy()
        if hasattr(self, 'frame_repa') and self.frame_repa: self.frame_repa.destroy()
        self.repartidor_logueado_id = None
        self.usuario_actual = None
        self.mostrar_login()

    # === ENTORNO ADMINISTRADOR ===
    def construir_interfaz_admin(self):
        self.menu_lateral = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.menu_lateral.pack(side="left", fill="y")
        
        ctk.CTkLabel(self.menu_lateral, text="PANEL PRINCIPAL", font=("sans-serif", 14, "bold")).pack(pady=15, padx=10)

        ctk.CTkButton(self.menu_lateral, text="Clientes", fg_color="transparent", anchor="w", command=lambda: self.mostrar_pantalla_clientes()).pack(pady=2, padx=5, fill="x")
        ctk.CTkButton(self.menu_lateral, text="Inventario / Equipos", fg_color="transparent", anchor="w", command=lambda: self.mostrar_pantalla_inventario()).pack(pady=2, padx=5, fill="x")
        ctk.CTkButton(self.menu_lateral, text="Gestionar Choferes", fg_color="transparent", anchor="w", command=lambda: self.mostrar_pantalla_repartidores()).pack(pady=2, padx=5, fill="x")
        ctk.CTkButton(self.menu_lateral, text="Nuevo Alquiler", fg_color="transparent", anchor="w", command=lambda: self.mostrar_pantalla_alquiler()).pack(pady=2, padx=5, fill="x")
        ctk.CTkButton(self.menu_lateral, text="Alquileres Activos", fg_color="transparent", anchor="w", command=lambda: self.mostrar_pantalla_ver_alquileres()).pack(pady=2, padx=5, fill="x")
        ctk.CTkButton(self.menu_lateral, text="Hoja de Ruta", fg_color="transparent", anchor="w", command=lambda: self.mostrar_hoja_ruta_admin()).pack(pady=2, padx=5, fill="x")
        ctk.CTkButton(self.menu_lateral, text="Configuración", fg_color="transparent", anchor="w", command=lambda: self.mostrar_pantalla_configuracion()).pack(pady=2, padx=5, fill="x")
        
        lbl_espacio = ctk.CTkLabel(self.menu_lateral, text="")
        lbl_espacio.pack(fill="both", expand=True)

        ctk.CTkButton(self.menu_lateral, text="Salir", fg_color="#c0392b", hover_color="#962d22", command=self.cerrar_sesion).pack(pady=15, padx=5, fill="x")

        self.contenedor = ctk.CTkFrame(self, corner_radius=5)
        self.contenedor.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        self.frame_clientes = None
        self.frame_alquiler = None
        self.frame_ver_alquileres = None
        self.frame_inventario = None
        self.frame_hoja_ruta = None
        self.frame_repartidores = None
        self.frame_config = None

        self.mostrar_pantalla_clientes()

    def cambiar_pantalla(self, pantalla_destino):
        for child in self.contenedor.winfo_children():
            child.pack_forget()
        pantalla_destino.pack(fill="both", expand=True, padx=5, pady=5)

    # === GESTIÓN DE CLIENTES ===
    def mostrar_pantalla_clientes(self):
        if self.frame_clientes: self.frame_clientes.destroy()
        self.frame_clientes = ctk.CTkFrame(self.contenedor, fg_color="transparent")
        
        scroll_c = ctk.CTkScrollableFrame(self.frame_clientes)
        scroll_c.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(scroll_c, text="Administración de Clientes", font=("sans-serif", 16, "bold"), text_color="#1abc9c").pack(pady=10)
        
        self.cli_id_sel = ctk.CTkLabel(scroll_c, text="ID Seleccionado: Ninguno (Modo: Registrar)", font=("sans-serif", 12, "italic"), text_color="#e67e22")
        self.cli_id_sel.pack(pady=2)

        self.c_nombre = ctk.CTkEntry(scroll_c, placeholder_text="Nombre Completo", width=260)
        self.c_nombre.pack(pady=5)
        self.c_telef = ctk.CTkEntry(scroll_c, placeholder_text="Teléfono", width=260)
        self.c_telef.pack(pady=5)
        self.c_email = ctk.CTkEntry(scroll_c, placeholder_text="Correo Electrónico (Email)", width=260)
        self.c_email.pack(pady=5)
        self.c_direc = ctk.CTkEntry(scroll_c, placeholder_text="Dirección de Habitación", width=260)
        self.c_direc.pack(pady=5)
        
        self.c_direc.bind("<Return>", lambda event: self.cli_guardar_automatico())
        
        btn_box = ctk.CTkFrame(scroll_c, fg_color="transparent")
        btn_box.pack(pady=12)
        ctk.CTkButton(btn_box, text="Registrar", fg_color="#1abc9c", font=("sans-serif", 11, "bold"), width=80, command=self.db_guardar_cliente).pack(side="left", padx=4)
        ctk.CTkButton(btn_box, text="Modificar", fg_color="#3498db", font=("sans-serif", 11, "bold"), width=80, command=self.cli_crud_editar).pack(side="left", padx=4)
        ctk.CTkButton(btn_box, text="Eliminar", fg_color="#e74c3c", font=("sans-serif", 11, "bold"), width=80, command=self.cli_crud_eliminar).pack(side="left", padx=4)

        t_frame = ctk.CTkFrame(scroll_c, height=200)
        t_frame.pack(fill="x", pady=10)
        
        sx = ttk.Scrollbar(t_frame, orient="horizontal"); sy = ttk.Scrollbar(t_frame, orient="vertical")
        self.tabla_clientes_crud = ttk.Treeview(t_frame, columns=("id", "nombre", "telefono", "email", "direccion"), show="headings", xscrollcommand=sx.set, yscrollcommand=sy.set, height=6)
        sx.config(command=self.tabla_clientes_crud.xview); sy.config(command=self.tabla_clientes_crud.yview)
        sx.pack(side="bottom", fill="x"); sy.pack(side="right", fill="y")
        self.tabla_clientes_crud.pack(side="left", fill="both", expand=True)
        
        self.tabla_clientes_crud.heading("id", text="ID"); self.tabla_clientes_crud.heading("nombre", text="Nombre"); self.tabla_clientes_crud.heading("telefono", text="Teléfono"); self.tabla_clientes_crud.heading("email", text="Email"); self.tabla_clientes_crud.heading("direccion", text="Dirección")
        self.tabla_clientes_crud.column("id", width=40); self.tabla_clientes_crud.column("nombre", width=120); self.tabla_clientes_crud.column("telefono", width=100); self.tabla_clientes_crud.column("email", width=110); self.tabla_clientes_crud.column("direccion", width=150)
        
        self.tabla_clientes_crud.bind("<<TreeviewSelect>>", self.cargar_cliente_formulario)
        self.actualizar_tabla_clientes_pantalla()
        self.cambiar_pantalla(self.frame_clientes)

    def actualizar_tabla_clientes_pantalla(self):
        for item in self.tabla_clientes_crud.get_children(): self.tabla_clientes_crud.delete(item)
        conn = self.obtener_conexion()
        for r in conn.execute("SELECT id, nombre, telefono, email, direccion FROM clientes").fetchall(): self.tabla_clientes_crud.insert("", "end", values=r)
        conn.close()

    def cargar_cliente_formulario(self, event):
        sel = self.tabla_clientes_crud.selection()
        if sel:
            v = self.tabla_clientes_crud.item(sel[0], 'values')
            self.cli_id_sel.configure(text=f"ID Seleccionado: {v[0]} (Modo: Editar/Borrar)", text_color="#3498db")
            self.c_nombre.delete(0, 'end'); self.c_nombre.insert(0, v[1])
            self.c_telef.delete(0, 'end'); self.c_telef.insert(0, v[2])
            self.c_email.delete(0, 'end'); self.c_email.insert(0, v[3])
            self.c_direc.delete(0, 'end'); self.c_direc.insert(0, v[4])

    def cli_guardar_automatico(self):
        if self.tabla_clientes_crud.selection(): self.cli_crud_editar()
        else: self.db_guardar_cliente()

    def db_guardar_cliente(self):
        n, t, e, d = self.c_nombre.get().strip(), self.c_telef.get().strip(), self.c_email.get().strip(), self.c_direc.get().strip()
        if n and t and d:
            conn = self.obtener_conexion()
            conn.execute("INSERT INTO clientes (nombre, telefono, email, direccion) VALUES (?,?,?,?)", (n, t, e, d))
            conn.commit(); conn.close()
            messagebox.showinfo("Éxito", "Cliente registrado con éxito")
            self.c_nombre.delete(0, 'end'); self.c_telef.delete(0, 'end'); self.c_email.delete(0, 'end'); self.c_direc.delete(0, 'end')
            self.actualizar_tabla_clientes_pantalla()
        else: messagebox.showwarning("Atención", "Complete los campos obligatorios (Nombre, Teléfono y Dirección)")

    def cli_crud_editar(self):
        sel = self.tabla_clientes_crud.selection()
        if not sel: return
        id_fijo = self.tabla_clientes_crud.item(sel[0], 'values')[0]
        n, t, e, d = self.c_nombre.get().strip(), self.c_telef.get().strip(), self.c_email.get().strip(), self.c_direc.get().strip()
        if n and t and d:
            conn = self.obtener_conexion()
            conn.execute("UPDATE clientes SET nombre=?, telefono=?, email=?, direccion=? WHERE id=?", (n, t, e, d, id_fijo))
            conn.commit(); conn.close()
            messagebox.showinfo("Éxito", "Datos de cliente modificados")
            self.c_nombre.delete(0, 'end'); self.c_telef.delete(0, 'end'); self.c_email.delete(0, 'end'); self.c_direc.delete(0, 'end')
            self.cli_id_sel.configure(text="ID Seleccionado: Ninguno (Modo: Registrar)", text_color="#e67e22")
            self.actualizar_tabla_clientes_pantalla()

    def cli_crud_eliminar(self):
        sel = self.tabla_clientes_crud.selection()
        if not sel: return
        v = self.tabla_clientes_crud.item(sel[0], 'values')
        if messagebox.askyesno("Confirmar", f"¿Eliminar al cliente {v[1]}?"):
            conn = self.obtener_conexion()
            try:
                conn.execute("DELETE FROM clientes WHERE id=?", (v[0],))
                conn.commit()
                messagebox.showinfo("Éxito", "Cliente eliminado.")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error de Integridad", "No se puede eliminar este cliente porque posee contratos de alquiler en curso.")
            finally:
                conn.close()
            self.c_nombre.delete(0, 'end'); self.c_telef.delete(0, 'end'); self.c_email.delete(0, 'end'); self.c_direc.delete(0, 'end')
            self.cli_id_sel.configure(text="ID Seleccionado: Ninguno (Modo: Registrar)", text_color="#e67e22")
            self.actualizar_tabla_clientes_pantalla()

    # === GESTIÓN DE INVENTARIO / LAVADORAS ===
    def mostrar_pantalla_inventario(self):
        if self.frame_inventario: self.frame_inventario.destroy()
        self.frame_inventario = ctk.CTkFrame(self.contenedor, fg_color="transparent")
        
        scroll_l = ctk.CTkScrollableFrame(self.frame_inventario)
        scroll_l.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(scroll_l, text="Control General de Inventario", font=("sans-serif", 16, "bold"), text_color="#3498db").pack(pady=10)
        
        self.lav_id_sel = ctk.CTkLabel(scroll_l, text="ID Seleccionado: Ninguno (Modo: Registrar)", font=("sans-serif", 12, "italic"), text_color="#e67e22")
        self.lav_id_sel.pack(pady=2)

        self.l_codigo = ctk.CTkEntry(scroll_l, placeholder_text="Código Interno (Ej: L-10)", width=260)
        self.l_codigo.pack(pady=5)
        self.l_marca = ctk.CTkEntry(scroll_l, placeholder_text="Marca del Equipo", width=260)
        self.l_marca.pack(pady=5)
        self.l_capacidad = ctk.CTkEntry(scroll_l, placeholder_text="Capacidad en Kg (Ej: 12.5)", width=260)
        self.l_capacidad.pack(pady=5)
        
        self.l_capacidad.bind("<Return>", lambda event: self.lav_guardar_automatico())
        
        self.l_estado = ctk.CTkComboBox(scroll_l, values=["Disponible", "Ocupado", "En mantenimiento"], width=260)
        self.l_estado.pack(pady=5)
        
        btn_box = ctk.CTkFrame(scroll_l, fg_color="transparent")
        btn_box.pack(pady=12)
        ctk.CTkButton(btn_box, text="Registrar", fg_color="#3498db", font=("sans-serif", 11, "bold"), width=80, command=self.db_guardar_lavadora).pack(side="left", padx=4)
        ctk.CTkButton(btn_box, text="Modificar", fg_color="#e67e22", font=("sans-serif", 11, "bold"), width=80, command=self.lav_crud_editar).pack(side="left", padx=4)
        ctk.CTkButton(btn_box, text="Eliminar", fg_color="#e74c3c", font=("sans-serif", 11, "bold"), width=80, command=self.lav_crud_eliminar).pack(side="left", padx=4)

        t_frame = ctk.CTkFrame(scroll_l, height=200)
        t_frame.pack(fill="x", pady=10)
        
        sx = ttk.Scrollbar(t_frame, orient="horizontal"); sy = ttk.Scrollbar(t_frame, orient="vertical")
        self.tabla_inventario_crud = ttk.Treeview(t_frame, columns=("id", "codigo", "marca", "capacidad", "estado"), show="headings", xscrollcommand=sx.set, yscrollcommand=sy.set, height=6)
        sx.config(command=self.tabla_inventario_crud.xview); sy.config(command=self.tabla_inventario_crud.yview)
        sx.pack(side="bottom", fill="x"); sy.pack(side="right", fill="y")
        self.tabla_inventario_crud.pack(side="left", fill="both", expand=True)
        
        self.tabla_inventario_crud.heading("id", text="ID"); self.tabla_inventario_crud.heading("codigo", text="Código"); self.tabla_inventario_crud.heading("marca", text="Marca"); self.tabla_inventario_crud.heading("capacidad", text="Capacidad"); self.tabla_inventario_crud.heading("estado", text="Estado")
        self.tabla_inventario_crud.column("id", width=40); self.tabla_inventario_crud.column("codigo", width=100); self.tabla_inventario_crud.column("marca", width=110); self.tabla_inventario_crud.column("capacidad", width=90); self.tabla_inventario_crud.column("estado", width=120)
        
        self.tabla_inventario_crud.bind("<<TreeviewSelect>>", self.cargar_lavadora_formulario)
        self.actualizar_tabla_lavadoras_pantalla()
        self.cambiar_pantalla(self.frame_inventario)

    def actualizar_tabla_lavadoras_pantalla(self):
        for item in self.tabla_inventario_crud.get_children(): self.tabla_inventario_crud.delete(item)
        conn = self.obtener_conexion()
        for eq in conn.execute("SELECT id, codigo, marca, capacidad, estado FROM lavadoras").fetchall(): self.tabla_inventario_crud.insert("", "end", values=(eq[0], eq[1], eq[2], f"{eq[3]} Kg", eq[4]))
        conn.close()

    def cargar_lavadora_formulario(self, event):
        sel = self.tabla_inventario_crud.selection()
        if sel:
            v = self.tabla_inventario_crud.item(sel[0], 'values')
            self.lav_id_sel.configure(text=f"ID Seleccionado: {v[0]} (Modo: Editar/Borrar)", text_color="#3498db")
            self.l_codigo.delete(0, 'end'); self.l_codigo.insert(0, v[1])
            self.l_marca.delete(0, 'end'); self.l_marca.insert(0, v[2])
            cap_limpia = v[3].replace(" Kg", "")
            self.l_capacidad.delete(0, 'end'); self.l_capacidad.insert(0, cap_limpia)
            self.l_estado.set(v[4])

    def lav_guardar_automatico(self):
        if self.tabla_inventario_crud.selection(): self.lav_crud_editar()
        else: self.db_guardar_lavadora()

    def db_guardar_lavadora(self):
        c, m, cap, est = self.l_codigo.get().strip().upper(), self.l_marca.get().strip(), self.l_capacidad.get().strip(), self.l_estado.get()
        if c and m and cap and est:
            try:
                conn = self.obtener_conexion()
                conn.execute("INSERT INTO lavadoras (codigo, marca, capacidad, estado) VALUES (?,?,?,?)", (c, m, float(cap), est))
                conn.commit(); conn.close()
                messagebox.showinfo("Éxito", f"Lavadora {c} registrada.")
                self.l_codigo.delete(0, 'end'); self.l_marca.delete(0, 'end'); self.l_capacidad.delete(0, 'end')
                self.actualizar_tabla_lavadoras_pantalla()
            except ValueError: messagebox.showerror("Error", "Capacidad numérica incorrecta.")
            except sqlite3.IntegrityError: messagebox.showerror("Error", "Ese código de lavadora ya existe.")
        else: messagebox.showwarning("Atención", "Complete todos los campos.")

    def lav_crud_editar(self):
        sel = self.tabla_inventario_crud.selection()
        if not sel: return
        id_fijo = self.tabla_inventario_crud.item(sel[0], 'values')[0]
        c, m, cap, est = self.l_codigo.get().strip().upper(), self.l_marca.get().strip(), self.l_capacidad.get().strip(), self.l_estado.get()
        if c and m and cap and est:
            try:
                conn = self.obtener_conexion()
                conn.execute("UPDATE lavadoras SET codigo=?, marca=?, capacidad=?, estado=? WHERE id=?", (c, m, float(cap), est, id_fijo))
                conn.commit(); conn.close()
                messagebox.showinfo("Éxito", "Lavadora modificada correctamente.")
                self.l_codigo.delete(0, 'end'); self.l_marca.delete(0, 'end'); self.l_capacidad.delete(0, 'end')
                self.lav_id_sel.configure(text="ID Seleccionado: Ninguno (Modo: Registrar)", text_color="#e67e22")
                self.actualizar_tabla_lavadoras_pantalla()
            except ValueError: messagebox.showerror("Error", "La capacidad debe ser un número válido.")
            except sqlite3.IntegrityError: messagebox.showerror("Error", "El código asignado colisiona con otro existente.")
        else: messagebox.showwarning("Atención", "No deje espacios vacíos.")

    def lav_crud_eliminar(self):
        sel = self.tabla_inventario_crud.selection()
        if not sel: return
        v = self.tabla_inventario_crud.item(sel[0], 'values')
        if messagebox.askyesno("Confirmar", f"¿Eliminar lavadora {v[1]} del inventario?"):
            conn = self.obtener_conexion()
            try:
                conn.execute("DELETE FROM lavadoras WHERE id=?", (v[0],))
                conn.commit()
                messagebox.showinfo("Éxito", "Lavadora borrada.")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error de protección", "No puedes eliminar una lavadora alquilada actualmente.")
            finally:
                conn.close()
            self.l_codigo.delete(0, 'end'); self.l_marca.delete(0, 'end'); self.l_capacidad.delete(0, 'end')
            self.lav_id_sel.configure(text="ID Seleccionado: Ninguno (Modo: Registrar)", text_color="#e67e22")
            self.actualizar_tabla_lavadoras_pantalla()

    # === GESTIÓN DE REPARTIDORES ===
    def mostrar_pantalla_repartidores(self):
        if self.frame_repartidores: self.frame_repartidores.destroy()
        self.frame_repartidores = ctk.CTkFrame(self.contenedor, fg_color="transparent")
        
        scroll_repa = ctk.CTkScrollableFrame(self.frame_repartidores)
        scroll_repa.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(scroll_repa, text="Panel de Control de Repartidores", font=("sans-serif", 16, "bold"), text_color="#2ecc71").pack(pady=10)
        
        self.rep_id_sel = ctk.CTkLabel(scroll_repa, text="ID Seleccionado: Ninguno (Modo: Crear)", font=("sans-serif", 12, "italic"), text_color="#e67e22")
        self.rep_id_sel.pack(pady=2)

        self.rep_nombre = ctk.CTkEntry(scroll_repa, placeholder_text="Nombre del Repartidor", width=260)
        self.rep_nombre.pack(pady=5)
        self.rep_telef = ctk.CTkEntry(scroll_repa, placeholder_text="Teléfono Celular", width=260)
        self.rep_telef.pack(pady=5)
        
        ctk.CTkLabel(scroll_repa, text="Estado del Chofer:").pack(anchor="w", padx=45)
        self.rep_estado = ctk.CTkComboBox(scroll_repa, values=["Disponible", "En ruta", "Inactivo"], width=260)
        self.rep_estado.pack(pady=5)
        
        self.rep_user = ctk.CTkEntry(scroll_repa, placeholder_text="Usuario de Acceso", width=260)
        self.rep_user.pack(pady=5)
        self.rep_pwd = ctk.CTkEntry(scroll_repa, placeholder_text="Contraseña de Acceso", show="*", width=260)
        self.rep_pwd.pack(pady=5)
        
        self.rep_pwd.bind("<Return>", lambda event: self.rep_guardar_automatico())

        btn_box = ctk.CTkFrame(scroll_repa, fg_color="transparent")
        btn_box.pack(pady=12)
        ctk.CTkButton(btn_box, text="Registrar", fg_color="#2ecc71", font=("sans-serif", 11, "bold"), width=80, command=self.rep_crud_crear).pack(side="left", padx=4)
        ctk.CTkButton(btn_box, text="Modificar", fg_color="#3498db", font=("sans-serif", 11, "bold"), width=80, command=self.rep_crud_editar).pack(side="left", padx=4)
        ctk.CTkButton(btn_box, text="Eliminar", fg_color="#e74c3c", font=("sans-serif", 11, "bold"), width=80, command=self.rep_crud_eliminar).pack(side="left", padx=4)

        t_frame = ctk.CTkFrame(scroll_repa, height=200)
        t_frame.pack(fill="x", pady=10)
        
        sx = ttk.Scrollbar(t_frame, orient="horizontal"); sy = ttk.Scrollbar(t_frame, orient="vertical")
        self.tabla_repartidores_crud = ttk.Treeview(t_frame, columns=("id", "nombre", "telefono", "estado", "usuario", "clave"), show="headings", xscrollcommand=sx.set, yscrollcommand=sy.set, height=6)
        sx.config(command=self.tabla_repartidores_crud.xview); sy.config(command=self.tabla_repartidores_crud.yview)
        sx.pack(side="bottom", fill="x"); sy.pack(side="right", fill="y")
        self.tabla_repartidores_crud.pack(side="left", fill="both", expand=True)
        
        self.tabla_repartidores_crud.heading("id", text="ID"); self.tabla_repartidores_crud.heading("nombre", text="Nombre"); self.tabla_repartidores_crud.heading("telefono", text="Teléfono"); self.tabla_repartidores_crud.heading("estado", text="Estado"); self.tabla_repartidores_crud.heading("usuario", text="Usuario"); self.tabla_repartidores_crud.heading("clave", text="Contraseña")
        self.tabla_repartidores_crud.column("id", width=40); self.tabla_repartidores_crud.column("nombre", width=110); self.tabla_repartidores_crud.column("telefono", width=100); self.tabla_repartidores_crud.column("estado", width=90); self.tabla_repartidores_crud.column("usuario", width=90); self.tabla_repartidores_crud.column("clave", width=90)
        
        self.tabla_repartidores_crud.bind("<<TreeviewSelect>>", self.cargar_repartidor_formulario)
        self.actualizar_tabla_repartidores_pantalla()
        self.cambiar_pantalla(self.frame_repartidores)

    def actualizar_tabla_repartidores_pantalla(self):
        for item in self.tabla_repartidores_crud.get_children(): self.tabla_repartidores_crud.delete(item)
        conn = self.obtener_conexion()
        lista = conn.execute('''SELECT r.id, r.nombre, r.telefono, r.estatus, r.usuario_asociado, u.pwd 
                                FROM repartidores r JOIN usuarios u ON r.usuario_asociado = u.user''').fetchall()
        conn.close()
        for r in lista: self.tabla_repartidores_crud.insert("", "end", values=r)

    def cargar_repartidor_formulario(self, event):
        sel = self.tabla_repartidores_crud.selection()
        if sel:
            v = self.tabla_repartidores_crud.item(sel[0], 'values')
            self.rep_id_sel.configure(text=f"ID Seleccionado: {v[0]} (Modo: Editar/Borrar)", text_color="#3498db")
            self.rep_nombre.delete(0, 'end'); self.rep_nombre.insert(0, v[1])
            self.rep_telef.delete(0, 'end'); self.rep_telef.insert(0, v[2])
            self.rep_estado.set(v[3])
            self.rep_user.delete(0, 'end'); self.rep_user.insert(0, v[4])
            self.rep_pwd.delete(0, 'end'); self.rep_pwd.insert(0, v[5])

    def rep_guardar_automatico(self):
        if self.tabla_repartidores_crud.selection(): self.rep_crud_editar()
        else: self.rep_crud_crear()

    def rep_crud_crear(self):
        nom, tlf, est, usr, pwd = self.rep_nombre.get().strip(), self.rep_telef.get().strip(), self.rep_estado.get(), self.rep_user.get().strip().lower(), self.rep_pwd.get()
        if nom and tlf and usr and pwd:
            conn = self.obtener_conexion()
            cur = conn.cursor()
            try:
                cur.execute("BEGIN TRANSACTION;")
                cur.execute("INSERT INTO usuarios (user, pwd, rol) VALUES (?,?,'Repartidor')", (usr, pwd))
                cur.execute("INSERT INTO repartidores (nombre, telefono, estatus, usuario_asociado) VALUES (?,?,?,?)", (nom, tlf, est, usr))
                conn.commit()
                messagebox.showinfo("Éxito", f"Chofer '{nom}' registrado.")
                self.rep_nombre.delete(0, 'end'); self.rep_telef.delete(0, 'end'); self.rep_user.delete(0, 'end'); self.rep_pwd.delete(0, 'end')
                self.rep_id_sel.configure(text="ID Seleccionado: Ninguno (Modo: Crear)", text_color="#e67e22")
                self.actualizar_tabla_repartidores_pantalla()
            except sqlite3.IntegrityError:
                conn.rollback()
                messagebox.showerror("Error", "El nombre de usuario ya se encuentra registrado.")
            finally:
                conn.close()
        else: messagebox.showwarning("Atención", "Complete todos los campos.")

    def rep_crud_editar(self):
        sel = self.tabla_repartidores_crud.selection()
        if not sel: return
        id_fijo = self.tabla_repartidores_crud.item(sel[0], 'values')[0]
        user_antiguo = self.tabla_repartidores_crud.item(sel[0], 'values')[4]
        nom, tlf, est_nue, usr_nue, pwd_nue = self.rep_nombre.get().strip(), self.rep_telef.get().strip(), self.rep_estado.get(), self.rep_user.get().strip().lower(), self.rep_pwd.get()
        
        if nom and tlf and usr_nue and pwd_nue:
            conn = self.obtener_conexion()
            cur = conn.cursor()
            try:
                cur.execute("BEGIN TRANSACTION;")
                cur.execute("UPDATE usuarios SET user=?, pwd=? WHERE user=?", (usr_nue, pwd_nue, user_antiguo))
                cur.execute("UPDATE repartidores SET nombre=?, telefono=?, estatus=?, usuario_asociado=? WHERE id=?", (nom, tlf, est_nue, usr_nue, id_fijo))
                conn.commit()
                messagebox.showinfo("Éxito", "Registro actualizado correctamente.")
                self.rep_nombre.delete(0, 'end'); self.rep_telef.delete(0, 'end'); self.rep_user.delete(0, 'end'); self.rep_pwd.delete(0, 'end')
                self.rep_id_sel.configure(text="ID Seleccionado: Ninguno (Modo: Crear)", text_color="#e67e22")
                self.actualizar_tabla_repartidores_pantalla()
            except sqlite3.IntegrityError:
                conn.rollback()
                messagebox.showerror("Error", "El nuevo usuario ya está en uso.")
            finally:
                conn.close()
        else: messagebox.showwarning("Atención", "No deje campos vacíos.")

    def rep_crud_eliminar(self):
        sel = self.tabla_repartidores_crud.selection()
        if not sel: return
        v = self.tabla_repartidores_crud.item(sel[0], 'values')
        if messagebox.askyesno("Confirmar", f"¿Eliminar por completo a {v[1]}?"):
            conn = self.obtener_conexion()
            try:
                conn.execute("DELETE FROM repartidores WHERE id=?", (v[0],))
                conn.execute("DELETE FROM usuarios WHERE user=?", (v[4],))
                conn.commit()
                messagebox.showinfo("Eliminado", "Repartidor removido.")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "No se puede eliminar un repartidor con despachos vinculados activos.")
            finally:
                conn.close()
            self.rep_nombre.delete(0, 'end'); self.rep_telef.delete(0, 'end'); self.rep_user.delete(0, 'end'); self.rep_pwd.delete(0, 'end')
            self.rep_id_sel.configure(text="ID Seleccionado: Ninguno (Modo: Crear)", text_color="#e67e22")
            self.actualizar_tabla_repartidores_pantalla()

    # === NUEVO ALQUILER ===
    def mostrar_pantalla_alquiler(self):
        if self.frame_alquiler: self.frame_alquiler.destroy()
        self.frame_alquiler = ctk.CTkFrame(self.contenedor, fg_color="transparent")
        
        form_scroll = ctk.CTkScrollableFrame(self.frame_alquiler)
        form_scroll.pack(side="top", fill="both", expand=True, pady=5, padx=5)

        ctk.CTkLabel(form_scroll, text="Operación de Alquiler", font=("sans-serif", 16, "bold")).pack(pady=5)

        conn = self.obtener_conexion()
        lista_clientes = [f"{r[0]} - {r[1]}" for r in conn.execute("SELECT id, nombre FROM clientes").fetchall()]
        lista_repas = [f"{r[0]} - {r[1]}" for r in conn.execute("SELECT id, nombre FROM repartidores WHERE estatus='Disponible'").fetchall()]
        lista_lavadoras = [f"{r[0]} - {r[1]} ({r[2]} Kg)" for r in conn.execute("SELECT id, codigo, capacidad FROM lavadoras WHERE estado='Disponible'").fetchall()]
        conn.close()

        self.var_horas = ctk.StringVar(value="24")
        self.var_tasa = ctk.StringVar(value="")
        self.var_horas.trace_add("write", self.calcular_precio_automatico)
        self.var_tasa.trace_add("write", self.calcular_precio_automatico)

        ctk.CTkLabel(form_scroll, text="1. Cliente:").pack(anchor="w", padx=15)
        self.combo_cliente = ctk.CTkComboBox(form_scroll, values=lista_clientes if lista_clientes else ["No hay clientes"], width=240)
        self.combo_cliente.pack(pady=3)

        ctk.CTkLabel(form_scroll, text="2. Lavadora:").pack(anchor="w", padx=15)
        self.combo_lavadora = ctk.CTkComboBox(form_scroll, values=lista_lavadoras if lista_lavadoras else ["No hay equipos libres"], width=240)
        self.combo_lavadora.pack(pady=3)

        ctk.CTkLabel(form_scroll, text="Repartidor Asignado:").pack(anchor="w", padx=15)
        self.combo_repa = ctk.CTkComboBox(form_scroll, values=lista_repas if lista_repas else ["1 - Juan"], width=240)
        self.combo_repa.pack(pady=3)

        ctk.CTkLabel(form_scroll, text="3. Horas de Uso:").pack(anchor="w", padx=15)
        self.horas_ent = ctk.CTkEntry(form_scroll, textvariable=self.var_horas, width=240)
        self.horas_ent.pack(pady=3)

        ctk.CTkLabel(form_scroll, text="4. Método de Pago:").pack(anchor="w", padx=15)
        self.metodo_pago = ctk.CTkComboBox(form_scroll, values=["Efectivo $", "Pago Móvil", "Efectivo Bs", "Transferencia"], command=lambda v: self.calcular_precio_automatico(), width=240)
        self.metodo_pago.pack(pady=3)

        ctk.CTkLabel(form_scroll, text="5. Tasa de Cambio (Bs/$):").pack(anchor="w", padx=15)
        self.tasa_ent = ctk.CTkEntry(form_scroll, textvariable=self.var_tasa, width=240)
        self.tasa_ent.pack(pady=3)
        
        self.tasa_ent.bind("<Return>", lambda event: self.procesar_alquiler_completo())

        self.lbl_total_automatico = ctk.CTkLabel(form_scroll, text="TOTAL: $0.00", font=("sans-serif", 14, "bold"), text_color="#2ecc71")
        self.lbl_total_automatico.pack(pady=10)

        ctk.CTkButton(form_scroll, text="Procesar Transacción", fg_color="green", font=("sans-serif", 12, "bold"), command=self.procesar_alquiler_completo, width=240).pack(pady=10)

        self.calcular_precio_automatico()
        self.cambiar_pantalla(self.frame_alquiler)

    def calcular_precio_automatico(self, *args):
        try:
            horas = int(self.var_horas.get() if self.var_horas.get() else 0)
            total_usd = horas * PRECIO_POR_HORA_USD
            metodo = self.metodo_pago.get()
            if "Bs" in metodo or metodo == "Pago Móvil":
                tasa = float(self.var_tasa.get() if self.var_tasa.get() else 0)
                self.lbl_total_automatico.configure(text=f"TOTAL: {total_usd * tasa:,.2f} Bs", text_color="#3498db")
            else:
                self.lbl_total_automatico.configure(text=f"TOTAL: ${total_usd:,.2f}", text_color="#2ecc71")
        except ValueError: self.lbl_total_automatico.configure(text="TOTAL: Esperando datos...", text_color="#e67e22")

    def procesar_alquiler_completo(self):
        try:
            horas = int(self.horas_ent.get())
            metodo = self.metodo_pago.get()
            id_cli = self.combo_cliente.get().split(" - ")[0]
            id_lav = self.combo_lavadora.get().split(" - ")[0]
            id_rep = self.combo_repa.get().split(" - ")[0]
            total_usd = horas * PRECIO_POR_HORA_USD
            moneda = "$" if "$" in metodo else "Bs"
            monto_final = total_usd * float(self.tasa_ent.get()) if moneda == "Bs" else total_usd
            vence = datetime.now() + timedelta(hours=horas)

            conn = self.obtener_conexion()
            cur = conn.cursor()
            try:
                cur.execute("BEGIN TRANSACTION;")
                cur.execute("INSERT INTO alquileres (id_cliente, id_lavadora, id_repartidor, fecha_vencimiento, monto, metodo_pago, moneda) VALUES (?,?,?,?,?,?,?)", (id_cli, id_lav, id_rep, vence, monto_final, metodo, moneda))
                cur.execute("UPDATE lavadoras SET estado='Ocupado' WHERE id=?", (id_lav,))
                cur.execute("UPDATE repartidores SET estatus='En ruta' WHERE id=?", (id_rep,))
                cur.execute("INSERT INTO hoja_ruta (id_alquiler, tipo_viaje) VALUES (?, 'Entrega')", (cur.lastrowid,))
                conn.commit()
                messagebox.showinfo("Éxito", "¡Alquiler procesado con éxito!")
            except sqlite3.Error as e:
                conn.rollback()
                messagebox.showerror("Error SQL", f"No se pudo guardar: {str(e)}")
            finally:
                conn.close()
            self.mostrar_pantalla_alquiler()
        except: messagebox.showerror("Error", "Verifique los datos numéricos.")

    # === ALQUILERES ACTIVOS ===
    def mostrar_pantalla_ver_alquileres(self):
        if self.frame_ver_alquileres: self.frame_ver_alquileres.destroy()
        self.frame_ver_alquileres = ctk.CTkFrame(self.contenedor, fg_color="transparent")
        
        ctk.CTkLabel(self.frame_ver_alquileres, text="ALQUILERES ACTIVOS", font=("sans-serif", 16, "bold"), text_color="#2ecc71").pack(pady=10)
        
        list_frame = ctk.CTkFrame(self.frame_ver_alquileres)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        sx = ttk.Scrollbar(list_frame, orient="horizontal"); sy = ttk.Scrollbar(list_frame, orient="vertical")
        self.tabla_alquiladas = ttk.Treeview(list_frame, columns=("id", "cliente", "lavadora", "vencimiento", "monto", "pago"), show="headings", xscrollcommand=sx.set, yscrollcommand=sy.set)
        sx.config(command=self.tabla_alquiladas.xview); sy.config(command=self.tabla_alquiladas.yview)
        sx.pack(side="bottom", fill="x"); sy.pack(side="right", fill="y")
        self.tabla_alquiladas.pack(side="left", fill="both", expand=True)
        
        self.tabla_alquiladas.heading("id", text="Alquiler #"); self.tabla_alquiladas.heading("cliente", text="Cliente"); self.tabla_alquiladas.heading("lavadora", text="Lavadora"); self.tabla_alquiladas.heading("vencimiento", text="Vence"); self.tabla_alquiladas.heading("monto", text="Monto"); self.tabla_alquiladas.heading("pago", text="Método")
        self.tabla_alquiladas.column("id", width=70); self.tabla_alquiladas.column("cliente", width=130); self.tabla_alquiladas.column("lavadora", width=100); self.tabla_alquiladas.column("vencimiento", width=140); self.tabla_alquiladas.column("monto", width=100); self.tabla_alquiladas.column("pago", width=100)
        
        conn = self.obtener_conexion()
        for r in conn.execute('''SELECT a.id, c.nombre, l.codigo, a.fecha_vencimiento, a.monto || " " || a.moneda, a.metodo_pago 
                               FROM alquileres a JOIN clientes c ON a.id_cliente = c.id JOIN lavadoras l ON a.id_lavadora = l.id WHERE a.estatus='Activo' ''').fetchall(): self.tabla_alquiladas.insert("", "end", values=r)
        conn.close()
        self.cambiar_pantalla(self.frame_ver_alquileres)

    # === HOJA DE RUTA GENERAL ===
    def mostrar_hoja_ruta_admin(self):
        if self.frame_hoja_ruta: self.frame_hoja_ruta.destroy()
        self.frame_hoja_ruta = ctk.CTkFrame(self.contenedor, fg_color="transparent")
        ctk.CTkLabel(self.frame_hoja_ruta, text="HOJA DE RUTA GENERAL", font=("sans-serif", 16, "bold"), text_color="#1abc9c").pack(pady=10)
        
        t_frame = ctk.CTkFrame(self.frame_hoja_ruta)
        t_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        sx = ttk.Scrollbar(t_frame, orient="horizontal"); sy = ttk.Scrollbar(t_frame, orient="vertical")
        self.tabla_ruta = ttk.Treeview(t_frame, columns=("id", "tipo", "cliente", "telefono", "direccion", "lavadora", "repartidor", "estatus"), show="headings", xscrollcommand=sx.set, yscrollcommand=sy.set)
        sx.config(command=self.tabla_ruta.xview); sy.config(command=self.tabla_ruta.yview)
        sx.pack(side="bottom", fill="x"); sy.pack(side="right", fill="y")
        self.tabla_ruta.pack(side="left", fill="both", expand=True)
        
        self.tabla_ruta.heading("id", text="ID"); self.tabla_ruta.heading("tipo", text="Tipo"); self.tabla_ruta.heading("cliente", text="Cliente"); self.tabla_ruta.heading("telefono", text="Teléfono"); self.tabla_ruta.heading("direccion", text="Dirección"); self.tabla_ruta.heading("lavadora", text="Equipo"); self.tabla_ruta.heading("repartidor", text="Chofer"); self.tabla_ruta.heading("estatus", text="Estatus")
        self.tabla_ruta.column("id", width=40); self.tabla_ruta.column("tipo", width=80); self.tabla_ruta.column("cliente", width=110); self.tabla_ruta.column("telefono", width=100); self.tabla_ruta.column("direccion", width=200); self.tabla_ruta.column("lavadora", width=70); self.tabla_ruta.column("repartidor", width=90); self.tabla_ruta.column("estatus", width=90)
        
        conn = self.obtener_conexion()
        viajes = conn.execute('''SELECT hr.id, hr.tipo_viaje, c.nombre, c.telefono, c.direccion, l.codigo, r.nombre, hr.estatus_viaje
                                 FROM hoja_ruta hr JOIN alquileres a ON hr.id_alquiler = a.id JOIN clientes c ON a.id_cliente = c.id
                                 JOIN lavadoras l ON a.id_lavadora = l.id JOIN repartidores r ON a.id_repartidor = r.id''').fetchall()
        conn.close()
        for v in viajes: self.tabla_ruta.insert("", "end", values=v)
        self.cambiar_pantalla(self.frame_hoja_ruta)

    # === CONFIGURACIÓN ===
    def mostrar_pantalla_configuracion(self):
        if self.frame_config: self.frame_config.destroy()
        self.frame_config = ctk.CTkFrame(self.contenedor, fg_color="transparent")
        ctk.CTkLabel(self.frame_config, text="SEGURIDAD Y CREDENCIALES", font=("sans-serif", 16, "bold"), text_color="#e67e22").pack(pady=10)
        
        self.pwd_nueva_admin = ctk.CTkEntry(self.frame_config, placeholder_text="Nueva Contraseña Administrador", show="*", width=240)
        self.pwd_nueva_admin.pack(pady=15)
        self.pwd_nueva_admin.bind("<Return>", lambda event: self.config_cambiar_clave_admin())
        
        ctk.CTkButton(self.frame_config, text="Actualizar Clave Admin", fg_color="#e67e22", command=self.config_cambiar_clave_admin).pack(pady=5)
        self.cambiar_pantalla(self.frame_config)

    def config_cambiar_clave_admin(self):
        nueva = self.pwd_nueva_admin.get()
        if nueva:
            conn = self.obtener_conexion()
            conn.execute("UPDATE usuarios SET pwd=? WHERE user=?", (nueva, self.usuario_actual))
            conn.commit(); conn.close()
            messagebox.showinfo("Seguridad", "¡Contraseña actualizada!")
            self.pwd_nueva_admin.delete(0, 'end')
        else: messagebox.showwarning("Error", "Escriba una clave válida.")

    # === MONITOR AUTOMÁTICO DE RECOGIDAS ===
    def bucle_monitoreo_automatico(self):
        conn = self.obtener_conexion()
        limite_10_min = datetime.now() + timedelta(minutes=10)
        alertas = conn.execute('''SELECT a.id, c.nombre, a.id_repartidor FROM alquileres a JOIN clientes c ON a.id_cliente = c.id 
                                 WHERE a.estatus='Activo' AND a.fecha_vencimiento <= ?''', (limite_10_min,)).fetchall()
        for a in alertas:
            if not conn.execute("SELECT id FROM hoja_ruta WHERE id_alquiler=? AND tipo_viaje='Retiro'", (a[0],)).fetchone():
                conn.execute("INSERT INTO hoja_ruta (id_alquiler, tipo_viaje) VALUES (?, 'Retiro')", (a[0],))
                conn.execute("UPDATE repartidores SET estatus='En ruta' WHERE id=?", (a[2],))
                conn.commit()
        conn.close()
        self.after(30000, self.bucle_monitoreo_automatico)

    # === ENTORNO REPARTIDOR (MÓDULO PROPIO) ===
    def construir_interfaz_repartidor(self):
        self.frame_repa = ctk.CTkFrame(self, corner_radius=5)
        self.frame_repa.pack(padx=5, pady=5, fill="both", expand=True)
        
        # Consultar el estatus real actual en la BD
        conn = self.obtener_conexion()
        estatus_actual = conn.execute("SELECT estatus FROM repartidores WHERE id=?", (self.repartidor_logueado_id,)).fetchone()[0]
        conn.close()

        # Encabezado informativo del Chofer
        ctk.CTkLabel(self.frame_repa, text="ENTREGAS Y RETIROS ASIGNADOS", font=("sans-serif", 16, "bold"), text_color="#2ecc71").pack(pady=5)
        
        # Caja de control de Estatus Propio para el Chofer
        estatus_frame = ctk.CTkFrame(self.frame_repa, fg_color="transparent")
        estatus_frame.pack(pady=5)
        
        self.lbl_mi_estatus = ctk.CTkLabel(estatus_frame, text=f"Mi Estado Actual: {estatus_actual}", font=("sans-serif", 12, "bold"), text_color="#e67e22")
        self.lbl_mi_estatus.pack(side="left", padx=10)
        
        self.combo_mi_estatus = ctk.CTkComboBox(estatus_frame, values=["Disponible", "En ruta", "Inactivo"], width=130)
        self.combo_mi_estatus.set(estatus_actual)
        self.combo_mi_estatus.pack(side="left", padx=5)
        
        ctk.CTkButton(estatus_frame, text="Cambiar Estado", width=100, fg_color="#3498db", font=("sans-serif", 11, "bold"), command=self.chofer_cambiar_estatus_propio).pack(side="left", padx=5)

        # Tabla de viajes pendientes
        t_frame = ctk.CTkFrame(self.frame_repa)
        t_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        sx = ttk.Scrollbar(t_frame, orient="horizontal"); sy = ttk.Scrollbar(t_frame, orient="vertical")
        self.tabla_repa_ruta = ttk.Treeview(t_frame, columns=("id", "tipo", "cliente", "telefono", "direccion", "lavadora"), show="headings", xscrollcommand=sx.set, yscrollcommand=sy.set)
        sx.config(command=self.tabla_repa_ruta.xview); sy.config(command=self.tabla_repa_ruta.yview)
        sx.pack(side="bottom", fill="x"); sy.pack(side="right", fill="y")
        self.tabla_repa_ruta.pack(side="left", fill="both", expand=True)
        
        self.tabla_repa_ruta.heading("id", text="ID"); self.tabla_repa_ruta.heading("tipo", text="Tipo"); self.tabla_repa_ruta.heading("cliente", text="Cliente"); self.tabla_repa_ruta.heading("telefono", text="Teléfono"); self.tabla_repa_ruta.heading("direccion", text="Dirección"); self.tabla_repa_ruta.heading("lavadora", text="Equipo")
        self.tabla_repa_ruta.column("id", width=40); self.tabla_repa_ruta.column("tipo", width=80); self.tabla_repa_ruta.column("cliente", width=110); self.tabla_repa_ruta.column("telefono", width=100); self.tabla_repa_ruta.column("direccion", width=180); self.tabla_repa_ruta.column("lavadora", width=70)
        
        btn_frame = ctk.CTkFrame(self.frame_repa, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        ctk.CTkButton(btn_frame, text="MARCAR COMO COMPLETADO", fg_color="#2ecc71", font=("sans-serif", 12, "bold"), command=self.completar_viaje_repartidor).pack(side="left", padx=10, expand=True, fill="x")
        ctk.CTkButton(btn_frame, text="Salir", fg_color="#c0392b", command=self.cerrar_sesion, width=100).pack(side="right", padx=10)
        self.actualizar_tabla_repartidor()

    def chofer_cambiar_estatus_propio(self):
        nuevo_est = self.combo_mi_estatus.get()
        conn = self.obtener_conexion()
        conn.execute("UPDATE repartidores SET estatus=? WHERE id=?", (nuevo_est, self.repartidor_logueado_id))
        conn.commit()
        conn.close()
        self.lbl_mi_estatus.configure(text=f"Mi Estado Actual: {nuevo_est}")
        messagebox.showinfo("Éxito", f"Tu estado se ha actualizado a: {nuevo_est}")

    def actualizar_tabla_repartidor(self):
        for item in self.tabla_repa_ruta.get_children(): self.tabla_repa_ruta.delete(item)
        conn = self.obtener_conexion()
        viajes = conn.execute('''SELECT hr.id, hr.tipo_viaje, c.nombre, c.telefono, c.direccion, l.codigo FROM hoja_ruta hr
                                 JOIN alquileres a ON hr.id_alquiler = a.id JOIN clientes c ON a.id_cliente = c.id
                                 JOIN lavadoras l ON a.id_lavadora = l.id 
                                 WHERE a.id_repartidor = ? AND hr.estatus_viaje = 'Pendiente' ''', (self.repartidor_logueado_id,)).fetchall()
        conn.close()
        for v in viajes: self.tabla_repa_ruta.insert("", "end", values=v)

    def completar_viaje_repartidor(self):
        sel = self.tabla_repa_ruta.selection()
        if not sel: return
        valores = self.tabla_repa_ruta.item(sel[0], 'values')
        conn = self.obtener_conexion()
        cur = conn.cursor()
        try:
            cur.execute("BEGIN TRANSACTION;")
            cur.execute("UPDATE hoja_ruta SET estatus_viaje='Completado' WHERE id=?", (valores[0],))
            
            id_alq = cur.execute("SELECT id_alquiler FROM hoja_ruta WHERE id=?", (valores[0],)).fetchone()[0]
            id_rep = cur.execute("SELECT id_repartidor FROM alquileres WHERE id=?", (id_alq,)).fetchone()[0]
            
            if "Retiro" in valores[1]:
                cur.execute("UPDATE alquileres SET estatus='Finalizado' WHERE id=?", (id_alq,))
                lav_id = cur.execute("SELECT id_lavadora FROM alquileres WHERE id=?", (id_alq,)).fetchone()[0]
                cur.execute("UPDATE lavadoras SET estado='Disponible' WHERE id=?", (lav_id,))
            
            cur.execute("UPDATE repartidores SET estatus='Disponible' WHERE id=?", (id_rep,))
            conn.commit()
            
            self.lbl_mi_estatus.configure(text="Mi Estado Actual: Disponible")
            self.combo_mi_estatus.set("Disponible")
            messagebox.showinfo("Éxito", "Hoja de ruta completada y estado restablecido a Disponible.")
        except sqlite3.Error:
            conn.rollback()
            messagebox.showerror("Error", "Fallo al procesar la actualización en base de datos.")
        finally:
            conn.close()
        self.actualizar_tabla_repartidor()

if __name__ == "__main__":
    app = SistemaAlquiler()
    app.mainloop()
