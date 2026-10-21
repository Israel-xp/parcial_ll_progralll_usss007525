const API = "/api/usuarios";
const frm = document.getElementById("frmUsuario");
const mensaje = document.getElementById("mensaje");
const tbody = document.getElementById("tbody");
const campoBuscar = document.getElementById("buscar");

function campo(id) {
    return document.getElementById(id);
}

function mostrar(texto, ok) {
    mensaje.textContent = texto;
    mensaje.className = ok ? "ok" : "error";
}

async function enviar(datos) {
    try {
        const r = await fetch(API, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datos),
        });
        if (r.status === 401) {
            location.href = "/";
            return { ok: false };
        }
        return await r.json();
    } catch (err) {
        return { ok: false, mensaje: "No se pudo conectar con el servidor" };
    }
}

function limpiar() {
    frm.reset();
    campo("idUsuario").value = "";
    campo("titulo").textContent = "Registrar usuario";
    campo("btnGuardar").textContent = "Guardar";
}

frm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = campo("idUsuario").value;
    const datos = {
        accion: id ? "modificar" : "guardar",
        idUsuario: id,
        usuario: campo("usuario").value.trim(),
        clave: campo("clave").value,
        nombre: campo("nombre").value.trim(),
        direccion: campo("direccion").value.trim(),
        telefono: campo("telefono").value.trim(),
    };
    if (!id && !datos.clave) {
        mostrar("La clave es obligatoria", false);
        return;
    }
    const res = await enviar(datos);
    if (res.ok) {
        limpiar();
        buscar();
    }
    mostrar(res.mensaje || "", res.ok);
});

campo("btnCancelar").addEventListener("click", () => {
    limpiar();
    mensaje.textContent = "";
});

async function buscar() {
    const res = await enviar({ accion: "buscar", q: campoBuscar.value.trim() });
    tbody.innerHTML = "";
    if (!res.ok) return;
    if (res.datos.length === 0) {
        const tr = document.createElement("tr");
        const td = document.createElement("td");
        td.colSpan = 6;
        td.textContent = "No hay usuarios que coincidan";
        tr.appendChild(td);
        tbody.appendChild(tr);
        return;
    }
    res.datos.forEach((u) => {
        const tr = document.createElement("tr");
        [u.idUsuario, u.usuario, u.nombre, u.direccion, u.telefono].forEach((valor) => {
            const td = document.createElement("td");
            td.textContent = valor;
            tr.appendChild(td);
        });
        const tdAcc = document.createElement("td");
        const btnEditar = document.createElement("button");
        btnEditar.textContent = "Editar";
        btnEditar.addEventListener("click", () => editar(u));
        const btnEliminar = document.createElement("button");
        btnEliminar.textContent = "Eliminar";
        btnEliminar.className = "del";
        btnEliminar.addEventListener("click", () => eliminar(u));
        tdAcc.append(btnEditar, btnEliminar);
        tr.appendChild(tdAcc);
        tbody.appendChild(tr);
    });
}

function editar(u) {
    campo("idUsuario").value = u.idUsuario;
    campo("usuario").value = u.usuario;
    campo("clave").value = "";
    campo("nombre").value = u.nombre;
    campo("direccion").value = u.direccion;
    campo("telefono").value = u.telefono;
    campo("titulo").textContent = "Modificar usuario (clave vacía = conservar la actual)";
    campo("btnGuardar").textContent = "Guardar cambios";
    window.scrollTo({ top: 0, behavior: "smooth" });
}

async function eliminar(u) {
    if (!confirm("¿Eliminar al usuario " + u.usuario + "?")) return;
    const res = await enviar({ accion: "eliminar", idUsuario: u.idUsuario });
    mostrar(res.mensaje || "", res.ok);
    if (res.ok) buscar();
}

campo("btnBuscar").addEventListener("click", buscar);
campoBuscar.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        e.preventDefault();
        buscar();
    }
});

buscar();