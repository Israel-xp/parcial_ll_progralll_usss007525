const frm = document.getElementById("frmLogin");
const mensaje = document.getElementById("mensaje");

frm.addEventListener("submit", async (e) => {
    e.preventDefault();
    mensaje.textContent = "";
    try {
        const r = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                usuario: document.getElementById("usuario").value.trim(),
                clave: document.getElementById("clave").value,
            }),
        });
        const res = await r.json();
        if (res.ok) {
            location.href = "/usuarios";
        } else {
            mensaje.textContent = res.mensaje || "Acceso denegado";
        }
    } catch (err) {
        mensaje.textContent = "No se pudo conectar con el servidor";
    }
});