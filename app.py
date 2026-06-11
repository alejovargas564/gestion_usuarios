from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave_secreta_local")

def get_connection():
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(url)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id        SERIAL PRIMARY KEY,
            nombre    VARCHAR(100) NOT NULL,
            email     VARCHAR(150) UNIQUE NOT NULL,
            telefono  VARCHAR(20),
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# ── Página principal ─────────────────────────────────────────
@app.route("/")
def index():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM usuarios;")
        total = cur.fetchone()[0]
        cur.close()
        conn.close()
    except Exception:
        total = 0
    return render_template("index.html", total=total)

# ── Página 2: Registro + Consulta embebida ───────────────────
@app.route("/usuarios", methods=["GET", "POST"])
def usuarios():
    if request.method == "POST":
        nombre   = request.form.get("nombre", "").strip()
        email    = request.form.get("email", "").strip()
        telefono = request.form.get("telefono", "").strip()

        if not nombre or not email:
            flash("Nombre y email son obligatorios.", "danger")
            return redirect(url_for("usuarios"))

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO usuarios (nombre, email, telefono) VALUES (%s, %s, %s);",
                (nombre, email, telefono)
            )
            conn.commit()
            cur.close()
            conn.close()
            flash(f"Usuario '{nombre}' registrado exitosamente.", "success")
        except psycopg2.errors.UniqueViolation:
            flash("Ese email ya está registrado.", "warning")
        except Exception as e:
            flash(f"Error al registrar: {e}", "danger")

        return redirect(url_for("usuarios"))

    # GET: cargar lista
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, email, telefono, creado_en FROM usuarios ORDER BY id DESC;")
        lista = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        lista = []
        flash(f"Error al consultar: {e}", "danger")

    return render_template("usuarios.html", lista=lista)

# ── Registro rápido desde el home ────────────────────────────
@app.route("/registro-rapido", methods=["POST"])
def registro_rapido():
    nombre   = request.form.get("nombre", "").strip()
    email    = request.form.get("email", "").strip()
    telefono = request.form.get("telefono", "").strip()

    if not nombre or not email:
        flash("Nombre y email son obligatorios.", "danger")
        return redirect(url_for("index"))

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO usuarios (nombre, email, telefono) VALUES (%s, %s, %s);",
            (nombre, email, telefono)
        )
        conn.commit()
        cur.close()
        conn.close()
        flash(f"Usuario '{nombre}' registrado correctamente.", "success")
    except psycopg2.errors.UniqueViolation:
        flash("Ese email ya está registrado.", "warning")
    except Exception as e:
        flash(f"Error: {e}", "danger")

    return redirect(url_for("index"))

# ── Consulta rápida desde el home ────────────────────────────
@app.route("/consulta-rapida")
def consulta_rapida():
    buscar = request.args.get("q", "").strip()
    resultados = []
    if buscar:
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, nombre, email, telefono FROM usuarios WHERE nombre ILIKE %s OR email ILIKE %s;",
                (f"%{buscar}%", f"%{buscar}%")
            )
            resultados = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            flash(f"Error en consulta: {e}", "danger")
    return render_template("consulta_rapida.html", resultados=resultados, buscar=buscar)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
