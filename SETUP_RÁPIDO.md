# 🚀 GUÍA RÁPIDA - MediFlow AI

## 📋 Instalación inicial completa

### 🔧 Backend
```bash
# Crear entorno virtual
cd backend
python -m venv .venv

# Activar entorno virtual (Windows)
.venv\Scripts\Activate

# Instalar dependencias
pip install groq
pip install -r requirements.txt

# Iniciar servidor backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ El backend estará corriendo en: `http://localhost:8000`

---

### 🎨 Frontend
```bash
cd frontend
npm install
npm run dev
```

✅ El frontend estará corriendo en: `http://localhost:3000`

---

## ¿Qué cambié para arreglarlo?

1. ✅ Cambié de `127.0.0.1` a `localhost` (funciona mejor en Windows)
2. ✅ Actualicé CORS para aceptar más orígenes
3. ✅ Arreglé la configuración del frontend
4. ✅ Creé herramientas de diagnóstico

## Pasos para que funcione

### 1️⃣ Reinicia el Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --host localhost --port 8000
```
Deberías ver: `Uvicorn running on http://localhost:8000`

### 2️⃣ Reinicia el Frontend  
```bash
cd frontend
npm run dev
```
Deberías ver: `ready in XXX ms` y `Local: http://localhost:3000`

### 3️⃣ Abre en el Navegador
Ve a: **http://localhost:3000**

### 4️⃣ Intenta Registrarte
- Haz clic en **Registrarse**
- Nombre: Cualquier nombre
- Email: `prueba@example.com`
- Contraseña: **Mínimo 8 caracteres** (ej: `password123`)
- Haz clic en **Crear cuenta**

### 5️⃣ Intenta hacer Login
- Haz clic en **Entrar** (si saliste)
- Email: el que usaste arriba
- Contraseña: la misma
- Haz clic en **Iniciar sesión**

---

## Si No Funciona

### Opción A: Ejecutar Diagnóstico
1. Abre la consola del navegador: **F12** → **Console**
2. Copia y pega todo el contenido de `DIAGNOSTICO_NAVEGADOR.js`
3. Presiona Enter
4. Verás qué parte está fallando

### Opción B: Ver la Guía Completa
Lee el archivo: `TROUBLESHOOTING.md`

---

## Cambios que Hice

### Backend (`backend/.env`)
```env
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://0.0.0.0:3000
```
Ahora acepta solicitudes desde más orígenes.

### Frontend (`frontend/.env`)
```env
VITE_API_URL=http://localhost:8000
```
Cambié de `127.0.0.1` a `localhost`.

### Código Frontend
- `frontend/src/api/client.ts` → Usa `localhost:8000` por defecto
- `frontend/src/main.tsx` → Usa `localhost:8000` por defecto
- `frontend/vite.config.ts` → Mejoré la configuración del alias

---

## Quick Test en la Consola del Navegador

Si quieres hacer un test rápido sin UI:

```javascript
// Test 1: ¿El backend está disponible?
fetch("http://localhost:8000/health").then(r => console.log("Backend OK:", r.status));

// Test 2: ¿Puedo registrarme?
fetch("http://localhost:8000/auth/register", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: `test${Date.now()}@example.com`,
    password: "password123",
    display_name: "Test"
  })
}).then(r => r.json()).then(d => console.log("Registro:", d));
```

---

## Variables de Entorno (`.env`)

Si necesitas cambiar la URL del backend:

**Windows (recomendado)**:
```env
VITE_API_URL=http://localhost:8000
```

**Linux/Mac**:
```env
VITE_API_URL=http://127.0.0.1:8000
```

Luego reinicia el frontend:
```bash
npm run dev
```

---

## ¿Qué debo hacer si aún no funciona?

1. **Cierra todos los navegadores y terminals**
2. **Limpia la base de datos** (opcional):
   ```bash
   cd backend
   rm mediflow.db  # Se regenerará automáticamente
   ```
3. **Reinicia todo desde cero**:
   ```bash
   # Terminal 1
   cd backend
   python -m uvicorn app.main:app --reload --host localhost --port 8000

   # Terminal 2
   cd frontend
   npm run dev
   ```
4. **Abre http://localhost:3000 en un navegador nuevo**
5. **Abre la consola (F12) y ejecuta el diagnóstico**

---

## Contacto

Si algo no funciona aún, comparte:
1. El resultado del diagnóstico (F12 → Console)
2. Los logs del backend
3. El navegador que uses


