# GUÍA DE TROUBLESHOOTING - Login y Registro

## Paso 1: Verificar que ambos servidores estén corriendo

### Backend (FastAPI)
```bash
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Debe mostrar: `Uvicorn running on http://127.0.0.1:8000`

### Frontend (Vite)
```bash
cd frontend
npm run dev
```
Debe mostrar: `Listening on http://localhost:3000`

---

## Paso 2: Ejecutar Diagnóstico

1. Abre el navegador en **http://localhost:3000**
2. Abre la consola del navegador: **F12** → Tab **Console**
3. Copia y pega el contenido de `DIAGNOSTICO_NAVEGADOR.js` en la consola
4. Presiona Enter

Esto ejecutará 4 pruebas:
- ✅/❌ Backend disponible
- ✅/❌ CORS funcionando
- ✅/❌ localStorage disponible
- ✅/❌ Registro funciona

---

## Paso 3: Solucionar Problemas Comunes

### Si el Backend NO está disponible (❌)
**Problema**: El frontend no puede alcanzar `http://127.0.0.1:8000`

**Soluciones**:
1. Verifica que el backend esté corriendo (ver Paso 1)
2. Si estás usando una red diferente, cambia `127.0.0.1` a `localhost` en:
   - `frontend/.env`: Cambiar `VITE_API_URL=http://127.0.0.1:8000` a `http://localhost:8000`
3. En Windows, probablemente debes usar `localhost` en lugar de `127.0.0.1`

### Si CORS falla (❌)
**Problema**: El servidor rechaza solicitudes del navegador

**Soluciones**:
1. Verifica en `backend/.env`:
   ```
   CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   ```
2. Si el frontend está en otra URL (ej: `http://192.168.x.x:3000`), añádela a CORS_ORIGINS
3. Reinicia el backend después de cambiar `.env`

### Si localStorage no funciona (❌)
**Problema**: El navegador no permite guardar datos

**Soluciones**:
1. Verifica que NO estés en modo incógnito
2. Comprueba la configuración de cookies del navegador
3. Limpia el cache: Ctrl+Shift+Del

### Si Registro falla (❌)
**Problema**: El error muestra detalles específicos

**Soluciones según el error**:
- `"El correo ya está registrado"` → Usa otro email
- `"Validation error"` → La contraseña debe tener **mínimo 8 caracteres**
- `"Email inválido"` → Verifica el formato del email
- Otros errores → Lee el mensaje de error en la consola

---

## Paso 4: Verificar en el Frontend

Una vez que el diagnóstico pasa:

1. En la página, verifica que ves el formulario de **Entrar / Registrarse**
2. Haz clic en **Registrarse**
3. Completa:
   - Nombre completo: Cualquier nombre
   - Email: `test@example.com` (o el que uses)
   - Contraseña: Mínimo 8 caracteres (ej: `password123`)
4. Haz clic en **Crear cuenta**
5. Deberías ver un toast verde diciendo "Cuenta creada"
6. Deberías ser redirigido al dashboard

---

## Paso 5: Verificar el Login

1. Haz clic en **Cerrar sesión** en la esquina superior derecha
2. Haz clic en **Entrar**
3. Usa el mismo email y contraseña del paso 4
4. Deberías ver "Bienvenido a MediFlow"
5. Deberías ver tu email en la esquina superior derecha

---

## Si Nada Funciona

1. **Reinicia todo**:
   ```bash
   # Terminal 1 - Backend
   Ctrl+C
   python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

   # Terminal 2 - Frontend
   Ctrl+C
   npm run dev
   ```

2. **Limpia la base de datos** (si necesitas empezar de nuevo):
   ```bash
   # Backend
   rm backend/mediflow.db
   # El archivo se regenerará automáticamente
   ```

3. **Revisa los logs del backend** para mensajes de error específicos

4. **Verifica el .env**:
   - `backend/.env` debe tener:
     ```
     DATABASE_URL=sqlite:///./mediflow.db
     CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
     ```
   - `frontend/.env` debe tener:
     ```
     VITE_API_URL=http://127.0.0.1:8000
     ```

---

## Errores Conocidos y Soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| `CORS error: Cross-Origin Request Blocked` | CORS no configurado | Añadir tu URL a `CORS_ORIGINS` en `backend/.env` |
| `ERR_NAME_NOT_RESOLVED` o `Failed to fetch` | Backend no disponible | Iniciar backend, verificar URL en `frontend/.env` |
| `Validation error - password` | Contraseña muy corta | Usar mínimo 8 caracteres |
| `El correo ya está registrado` | Email duplicado | Usar otro email |
| `localStorage not defined` | Modo incógnito o permisos | Usar modo normal, permitir storage |
| Botón de Login/Registro no responde | Error en el frontend | Ver console (F12) para mensajes de error específicos |

---

## Para Windows Específicamente

En Windows, usa `localhost` en lugar de `127.0.0.1`:

### backend/.env
```
DATABASE_URL=sqlite:///./mediflow.db
CORS_ORIGINS=http://localhost:3000
```

### frontend/.env
```
VITE_API_URL=http://localhost:8000
```

---

## Debug Avanzado

Si necesitas más información, ejecuta esto en la consola del navegador:

```javascript
// Ver configuración actual
console.log("API_BASE:", import.meta.env.VITE_API_URL);
console.log("Token:", localStorage.getItem("mediflow_token"));
console.log("Usuario:", localStorage.getItem("mediflow_user"));

// Hacer un test de registro manual
fetch("http://localhost:8000/auth/register", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: `test${Date.now()}@example.com`,
    password: "password123",
    display_name: "Test",
  }),
})
  .then((r) => r.json())
  .then((d) => console.log(d))
  .catch((e) => console.error(e));
```
