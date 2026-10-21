import hashlib
import json
import secrets
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import mysql.connector

WEB = Path(__file__).parent / "web"
DB = dict(host="localhost", user="root", password="", database="db_academica")
SESIONES = {}


def encriptar(texto):
    return hashlib.md5(texto.encode("utf-8")).hexdigest()


class CrudUsuarios:
    def conectar(self):
        return mysql.connector.connect(**DB)

    def crud_usuarios_usss007525(self, accion, d):
        con = self.conectar()
        cur = con.cursor(dictionary=True)
        try:
            if accion == "guardar":
                cur.execute("SELECT idUsuario FROM usuarios_usss007525 WHERE usuario=%s", (d["usuario"],))
                if cur.fetchone():
                    return {"ok": False, "mensaje": "Ese usuario ya existe"}
                cur.execute(
                    "INSERT INTO usuarios_usss007525 (usuario, clave, nombre, direccion, telefono) "
                    "VALUES (%s,%s,%s,%s,%s)",
                    (d["usuario"], encriptar(d["clave"]), d["nombre"], d["direccion"], d["telefono"]),
                )
                con.commit()
                return {"ok": True, "mensaje": "Usuario guardado"}

            if accion == "buscar":
                q = "%" + d.get("q", "") + "%"
                cur.execute(
                    "SELECT idUsuario, usuario, nombre, direccion, telefono FROM usuarios_usss007525 "
                    "WHERE usuario LIKE %s OR nombre LIKE %s ORDER BY idUsuario",
                    (q, q),
                )
                return {"ok": True, "datos": cur.fetchall()}

            if accion == "modificar":
                cur.execute(
                    "SELECT idUsuario FROM usuarios_usss007525 WHERE usuario=%s AND idUsuario<>%s",
                    (d["usuario"], d["idUsuario"]),
                )
                if cur.fetchone():
                    return {"ok": False, "mensaje": "Ese usuario ya existe"}
                if d.get("clave"):
                    cur.execute(
                        "UPDATE usuarios_usss007525 SET usuario=%s, clave=%s, nombre=%s, direccion=%s, "
                        "telefono=%s WHERE idUsuario=%s",
                        (d["usuario"], encriptar(d["clave"]), d["nombre"], d["direccion"],
                         d["telefono"], d["idUsuario"]),
                    )
                else:
                    cur.execute(
                        "UPDATE usuarios_usss007525 SET usuario=%s, nombre=%s, direccion=%s, "
                        "telefono=%s WHERE idUsuario=%s",
                        (d["usuario"], d["nombre"], d["direccion"], d["telefono"], d["idUsuario"]),
                    )
                con.commit()
                return {"ok": True, "mensaje": "Usuario modificado"}

            if accion == "eliminar":
                cur.execute("DELETE FROM usuarios_usss007525 WHERE idUsuario=%s", (d["idUsuario"],))
                con.commit()
                return {"ok": True, "mensaje": "Usuario eliminado"}

            if accion == "login":
                cur.execute(
                    "SELECT usuario FROM usuarios_usss007525 WHERE usuario=%s AND clave=%s",
                    (d["usuario"], encriptar(d["clave"])),
                )
                fila = cur.fetchone()
                if fila:
                    return {"ok": True, "usuario": fila["usuario"]}
                return {"ok": False, "mensaje": "Usuario o clave incorrectos"}

            return {"ok": False, "mensaje": "Acción no válida"}
        except mysql.connector.Error as e:
            return {"ok": False, "mensaje": "Error de base de datos: " + str(e)}
        finally:
            cur.close()
            con.close()


crud = CrudUsuarios()


class Handler(BaseHTTPRequestHandler):
    def sesion(self):
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        return SESIONES.get(cookie["sid"].value) if "sid" in cookie else None

    def responder(self, codigo, tipo, cuerpo, cabeceras=None):
        if isinstance(cuerpo, str):
            cuerpo = cuerpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo + "; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        for k, v in (cabeceras or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(cuerpo)

    def redirigir(self, destino, cabeceras=None):
        h = {"Location": destino}
        h.update(cabeceras or {})
        self.responder(302, "text/plain", "", h)

    def archivo(self, nombre, tipo):
        self.responder(200, tipo, (WEB / nombre).read_text(encoding="utf-8"))

    def do_GET(self):
        ruta = self.path.split("?")[0]
        if ruta == "/":
            self.archivo("login.html", "text/html")
        elif ruta == "/usuarios":
            if self.sesion():
                self.archivo("usuarios.html", "text/html")
            else:
                self.redirigir("/")
        elif ruta == "/login.js":
            self.archivo("login.js", "application/javascript")
        elif ruta == "/usuarios.js":
            self.archivo("usuarios.js", "application/javascript")
        elif ruta == "/logout":
            cookie = SimpleCookie(self.headers.get("Cookie", ""))
            if "sid" in cookie:
                SESIONES.pop(cookie["sid"].value, None)
            self.redirigir("/", {"Set-Cookie": "sid=; Path=/; Max-Age=0"})
        else:
            self.responder(404, "text/plain", "No encontrado")

    def do_POST(self):
        ruta = self.path.split("?")[0]
        largo = int(self.headers.get("Content-Length", 0))
        try:
            datos = json.loads(self.rfile.read(largo) or "{}")
        except json.JSONDecodeError:
            return self.responder(400, "application/json", json.dumps({"ok": False, "mensaje": "JSON inválido"}))

        cabeceras = {}
        if ruta == "/api/login":
            res = crud.crud_usuarios_usss007525("login", datos)
            if res["ok"]:
                token = secrets.token_hex(16)
                SESIONES[token] = res["usuario"]
                cabeceras["Set-Cookie"] = "sid=" + token + "; Path=/; HttpOnly"
        elif ruta == "/api/usuarios":
            if not self.sesion():
                return self.responder(401, "application/json", json.dumps({"ok": False, "mensaje": "No autorizado"}))
            accion = datos.pop("accion", "")
            res = crud.crud_usuarios_usss007525(accion, datos)
        else:
            return self.responder(404, "application/json", json.dumps({"ok": False}))
        self.responder(200, "application/json", json.dumps(res, default=str), cabeceras)


if __name__ == "__main__":
    print("Servidor listo en http://localhost:8000")
    ThreadingHTTPServer(("localhost", 8000), Handler).serve_forever()