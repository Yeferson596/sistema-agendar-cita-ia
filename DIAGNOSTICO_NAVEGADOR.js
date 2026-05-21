// SCRIPT DE DIAGNÓSTICO - Pegá esto en la consola del navegador (F12)
// Prueba cada parte del proceso de login/registro

async function diagnosticar() {
  const API_BASE = "http://127.0.0.1:8000";
  const results = [];

  console.clear();
  console.log("🔍 DIAGNÓSTICO DE LOGIN/REGISTRO");
  console.log("================================\n");

  // Test 1: Backend disponible
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      console.log("✅ Backend disponible en", API_BASE);
      results.push({ test: "Backend disponible", ok: true });
    } else {
      console.log("❌ Backend responde con status", res.status);
      results.push({ test: "Backend disponible", ok: false, status: res.status });
    }
  } catch (e) {
    console.log("❌ Backend NO disponible:", e.message);
    results.push({ test: "Backend disponible", ok: false, error: e.message });
  }

  // Test 2: CORS permitido
  try {
    const res = await fetch(`${API_BASE}/auth/public-google-client-id`);
    if (res.ok) {
      const data = await res.json();
      console.log("✅ CORS funcionando correctamente");
      results.push({ test: "CORS", ok: true });
    } else {
      console.log("❌ Error CORS o servidor:", res.status);
      results.push({ test: "CORS", ok: false, status: res.status });
    }
  } catch (e) {
    console.log("❌ Error de CORS:", e.message);
    results.push({ test: "CORS", ok: false, error: e.message });
  }

  // Test 3: Verificar localStorage
  try {
    localStorage.setItem("test", "1");
    localStorage.removeItem("test");
    console.log("✅ localStorage funcionando");
    results.push({ test: "localStorage", ok: true });
  } catch (e) {
    console.log("❌ localStorage no disponible:", e.message);
    results.push({ test: "localStorage", ok: false, error: e.message });
  }

  // Test 4: Probar registro
  try {
    const email = `test${Date.now()}@example.com`;
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password: "password123456",
        display_name: "Test User",
      }),
    });
    const data = await res.json();
    if (res.ok) {
      console.log("✅ Registro funciona - Token:", data.access_token?.substring(0, 20) + "...");
      results.push({ test: "Registro", ok: true });
    } else {
      console.log("❌ Error en registro:", res.status, data.detail);
      results.push({ test: "Registro", ok: false, error: data.detail });
    }
  } catch (e) {
    console.log("❌ Error al probar registro:", e.message);
    results.push({ test: "Registro", ok: false, error: e.message });
  }

  // Resumen
  console.log("\n================================");
  console.log("📋 RESUMEN:");
  const ok = results.filter((r) => r.ok).length;
  const total = results.length;
  console.log(`${ok}/${total} pruebas pasaron`);

  if (ok === total) {
    console.log("✅ ¡Todo funciona! El problema podría estar en el frontend.");
  } else {
    console.log("❌ Hay problemas. Ver detalles arriba.");
  }

  return results;
}

// Ejecutar
diagnosticar().catch(console.error);
