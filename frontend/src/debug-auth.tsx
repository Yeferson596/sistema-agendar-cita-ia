/**
 * Componente de diagnóstico para verificar problemas con login/registro
 */

export async function debugAuth() {
  const API_BASE = "http://127.0.0.1:8000";
  
  console.log("=== DEBUG AUTH ===");
  console.log("API_BASE:", API_BASE);
  
  // Test 1: Verificar conectividad básica
  try {
    const res = await fetch(`${API_BASE}/health`);
    console.log("✓ Health check:", res.status, res.ok);
  } catch (e) {
    console.error("✗ Health check failed:", e);
  }

  // Test 2: Obtener Google Client ID
  try {
    const res = await fetch(`${API_BASE}/auth/public-google-client-id`);
    const data = await res.json();
    console.log("✓ Google Client ID endpoint:", data);
  } catch (e) {
    console.error("✗ Google Client ID failed:", e);
  }

  // Test 3: Intentar registro
  try {
    const email = `test${Date.now()}@example.com`;
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      json: { email, password: "password123", display_name: "Test" },
    } as any);
    const data = await res.json();
    console.log("✓ Register endpoint:", res.status, data);
  } catch (e) {
    console.error("✗ Register failed:", e);
  }

  // Test 4: Verificar localStorage
  console.log("✓ localStorage available:", typeof localStorage !== "undefined");
  
  // Test 5: Verificar sessionStorage
  console.log("✓ sessionStorage available:", typeof sessionStorage !== "undefined");
}

// Exportar para ser llamado desde la consola
(window as any).debugAuth = debugAuth;
