/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useCallback, useContext, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Toaster } from '@/components/ui/sonner';
import { toast } from 'sonner';
import {
  LogIn,
  LogOut,
  Stethoscope,
  LayoutDashboard,
  Calendar as CalendarIcon,
  User as UserIcon,
  Trash2,
} from 'lucide-react';
import TriageForm, { TriageResult } from './components/TriageForm';
import AssistantPanel from './components/AssistantPanel';
import Dashboard, { AppointmentVM } from './components/Dashboard';
import { motion, AnimatePresence } from 'motion/react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { api, clearSession, getStoredUser, getToken, setSession, UserProfile } from '@/src/api/client';
import { GoogleLogin } from '@react-oauth/google';
import { GoogleClientIdContext } from './GoogleClientContext';

const appointmentStatusLabels: Record<string, string> = {
  scheduled: 'Confirmada',
  completed: 'Completada',
  cancelled: 'Cancelada',
  'no-show': 'No asistida',
};

function toAppointmentVM(rows: Awaited<ReturnType<typeof api.appointments>>): AppointmentVM[] {
  return rows.map((r) => ({
    id: r.id,
    patientName: r.patient_name || 'Paciente',
    specialty: r.specialty,
    urgency: r.urgency,
    status: r.status,
    description: r.description,
    triageReasoning: r.triage_reasoning,
    noShowRisk: typeof r.no_show_risk === 'number' ? r.no_show_risk : 0,
    date: new Date(r.start_at),
  }));
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <Card className="bento-item border-none shadow-2xl hover:-translate-y-1 transition-all duration-500 bg-gradient-to-br from-slate-50 to-white p-8 flex flex-col items-start text-left group">
      <div className="mb-6 p-4 rounded-2xl bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white transition-colors duration-500">
        {icon}
      </div>
      <h3 className="text-xl font-black mb-3 tracking-tight">{title}</h3>
      <p className="text-muted-foreground font-medium leading-relaxed">{description}</p>
    </Card>
  );
}

export default function App() {
  const googleClientId = useContext(GoogleClientIdContext);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [appointments, setAppointments] = useState<AppointmentVM[]>([]);
  const [riskAlerts, setRiskAlerts] = useState<Awaited<ReturnType<typeof api.riskAlerts>>>([]);
  const [loading, setLoading] = useState(true);
  const [isScheduling, setIsScheduling] = useState(false);
  const [expandedAppointmentId, setExpandedAppointmentId] = useState<string | null>(null);

  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authName, setAuthName] = useState('');
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  const refreshData = useCallback(async () => {
    const list = await api.appointments();
    setAppointments(toAppointmentVM(list));
    try {
      const alerts = await api.riskAlerts(0.55);
      setRiskAlerts(alerts);
    } catch {
      setRiskAlerts([]);
    }
  }, []);

  useEffect(() => {
    const bootstrap = async () => {
      const t = getToken();
      const cached = getStoredUser();
      if (!t || !cached) {
        setLoading(false);
        return;
      }
      try {
        const me = await api.me();
        setUser(me);
        localStorage.setItem('mediflow_user', JSON.stringify(me));
        await refreshData();
      } catch {
        clearSession();
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    bootstrap();
  }, [refreshData]);

  const loginPassword = async () => {
    const email = authEmail.trim();
    if (!email) {
      toast.error('Indica un correo electrónico');
      return;
    }
    if (authMode === 'register' && authPassword.length < 8) {
      toast.error('La contraseña debe tener al menos 8 caracteres');
      return;
    }
    try {
      const tr =
        authMode === 'register'
          ? await api.register(email, authPassword, authName.trim() || undefined)
          : await api.login(email, authPassword);
      setSession(tr);
      setUser(tr.user);
      toast.success(authMode === 'register' ? 'Cuenta creada' : 'Bienvenido a MediFlow');
      await refreshData();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Error de autenticación');
    }
  };

  const logout = () => {
    clearSession();
    setUser(null);
    setAppointments([]);
    setRiskAlerts([]);
    toast.info('Sesión cerrada');
  };

  const handleSchedule = async (triage: TriageResult, startAt: Date) => {
    if (!user) return;
    setIsScheduling(true);
    try {
      await api.createAppointment({
        specialty: triage.specialty,
        urgency: triage.urgency,
        start_at: startAt.toISOString(),
        description: triage.reasoning,
        triage_reasoning: triage.reasoning,
      });
      toast.success('Cita agendada exitosamente');
      await refreshData();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Error al agendar');
    } finally {
      setIsScheduling(false);
    }
  };

  const deleteAppointment = async (id: string) => {
    try {
      await api.deleteAppointment(id);
      toast.success('Cita eliminada correctamente');
      await refreshData();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Error al eliminar');
    }
  };

  if (loading) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-background">
        <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}>
          <Stethoscope className="h-12 w-12 text-primary" />
        </motion.div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen bg-background text-foreground font-sans selection:bg-primary/10">
      <Toaster position="top-center" richColors />
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 overflow-hidden">
        <div className="absolute left-1/2 top-0 h-72 w-72 -translate-x-1/2 rounded-full bg-primary/10 blur-3xl" />
        <div className="absolute left-10 top-40 h-56 w-56 rounded-full bg-cyan-200/20 blur-3xl" />
        <div className="absolute right-0 top-56 h-96 w-96 rounded-full bg-slate-400/10 blur-3xl" />
      </div>

      <header className="sticky top-0 z-50 w-full bg-background/80 backdrop-blur-md border-b border-border/50">
        <div className="container mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 bg-primary rounded-full animate-pulse" />
            <span className="text-xl font-black tracking-tighter text-foreground uppercase italic">
              MediFlow <span className="text-primary not-italic">AI</span>
            </span>
          </div>
          {user ? (
            <div className="flex items-center gap-4">
              <div className="hidden sm:flex items-center bg-secondary/50 border border-primary/10 px-4 py-2 rounded-full">
                <span className="text-xs font-bold text-primary tracking-wide uppercase">
                  {user.display_name || user.email} • {user.role === 'admin' ? 'Gestión' : 'Paciente'}
                </span>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={logout}
                className="rounded-full hover:bg-destructive/10 hover:text-destructive transition-colors"
              >
                <LogOut className="h-5 w-5" />
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground hidden md:inline">IA médica · Agenda inteligente · FastAPI</span>
            </div>
          )}
        </div>
      </header>

      <main className="container mx-auto px-6 py-12">
        {!user ? (
          <div className="max-w-7xl mx-auto space-y-16">
            <div className="grid gap-10 lg:grid-cols-[1.2fr_0.9fr] items-center">
              <motion.div
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
                className="space-y-8"
              >
                <Badge
                  variant="outline"
                  className="inline-flex px-4 py-1 rounded-full border-primary/20 text-primary font-bold tracking-widest uppercase text-[10px]"
                >
                  Portal de pacientes
                </Badge>
                <div className="space-y-6">
                  <h1 className="text-5xl md:text-6xl font-black tracking-tight text-foreground leading-tight">
                    Agenda consultas médicas con <span className="text-gradient">IA inteligente</span> y gestión
                    simplificada.
                  </h1>
                  <p className="max-w-2xl text-lg text-muted-foreground leading-relaxed">
                    Regístrate o inicia sesión en el entorno seguro de MediFlow. Recibe triaje automático, disponibilidad
                    por especialidad y alertas de no-show en una sola plataforma.
                  </p>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-[28px] border border-border/60 bg-white p-6 shadow-sm">
                    <p className="text-xs uppercase tracking-[0.25em] text-muted-foreground mb-3">Velocidad</p>
                    <p className="font-semibold text-2xl text-foreground">Agendamiento instantáneo</p>
                  </div>
                  <div className="rounded-[28px] border border-border/60 bg-white p-6 shadow-sm">
                    <p className="text-xs uppercase tracking-[0.25em] text-muted-foreground mb-3">Precisión</p>
                    <p className="font-semibold text-2xl text-foreground">Triaging con respaldo</p>
                  </div>
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: 30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.8, ease: 'easeOut', delay: 0.1 }}
                className="relative rounded-[32px] border border-border/70 bg-slate-950/95 p-8 shadow-2xl shadow-slate-950/20 overflow-hidden"
              >
                <div className="absolute -right-10 -top-10 h-36 w-36 rounded-full bg-primary/20 blur-2xl" />
                <div className="absolute left-0 top-1/2 h-32 w-32 rounded-full bg-cyan-500/10 blur-2xl" />
                <div className="relative space-y-6 text-white">
                  <div>
                    <p className="text-xs uppercase tracking-[0.3em] text-cyan-200/80">Acceso seguro</p>
                    <h2 className="mt-3 text-3xl font-black tracking-tight">Bienvenido a MediFlow</h2>
                    <p className="mt-2 text-sm text-slate-300 leading-6">
                      Controla tu agenda médica, solicita triaje y recibe recomendaciones en un solo lugar.
                    </p>
                  </div>

                  <div className="rounded-[28px] border border-slate-800/80 bg-slate-950/90 p-6 shadow-lg shadow-slate-950/20">
                    <div className="flex items-center justify-between gap-3 mb-6">
                      <Button
                        variant={authMode === 'login' ? 'default' : 'outline'}
                        className={`flex-1 rounded-2xl text-sm font-black ${
                          authMode === 'login'
                            ? 'bg-cyan-500 text-slate-900 shadow-cyan-500/20'
                            : 'bg-slate-900 text-slate-200 border border-slate-700'
                        }`}
                        onClick={() => setAuthMode('login')}
                      >
                        Entrar
                      </Button>
                      <Button
                        variant={authMode === 'register' ? 'default' : 'outline'}
                        className={`flex-1 rounded-2xl text-sm font-black ${
                          authMode === 'register'
                            ? 'bg-emerald-500 text-slate-900 shadow-emerald-500/20'
                            : 'bg-slate-900 text-slate-200 border border-slate-700'
                        }`}
                        onClick={() => setAuthMode('register')}
                      >
                        Registrarse
                      </Button>
                    </div>

                    <div className="space-y-4">
                      {authMode === 'register' && (
                        <div className="space-y-2">
                          <label className="text-xs text-slate-400 uppercase tracking-[0.25em]">Nombre completo</label>
                          <Input
                            value={authName}
                            onChange={(e) => setAuthName(e.target.value)}
                            className="h-12 rounded-3xl bg-slate-900/80 border-slate-700 text-white"
                          />
                        </div>
                      )}
                      <div className="space-y-2">
                        <label className="text-xs text-slate-400 uppercase tracking-[0.25em]">Email</label>
                        <Input
                          type="email"
                          value={authEmail}
                          onChange={(e) => setAuthEmail(e.target.value)}
                          className="h-12 rounded-3xl bg-slate-900/80 border-slate-700 text-white"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs text-slate-400 uppercase tracking-[0.25em]">Contraseña</label>
                        <Input
                          type="password"
                          value={authPassword}
                          onChange={(e) => setAuthPassword(e.target.value)}
                          className="h-12 rounded-3xl bg-slate-900/80 border-slate-700 text-white"
                          autoComplete={authMode === 'register' ? 'new-password' : 'current-password'}
                        />
                        {authMode === 'register' && (
                          <p className="text-[11px] text-slate-400">Mínimo 8 caracteres.</p>
                        )}
                      </div>
                      <Button
                        type="button"
                        className="w-full h-14 rounded-3xl bg-gradient-to-r from-cyan-500 to-sky-500 text-slate-950 font-black shadow-lg shadow-cyan-500/20"
                        onClick={() => void loginPassword()}
                      >
                        <LogIn className="mr-2 h-4 w-4" />
                        {authMode === 'register' ? 'Crear cuenta' : 'Iniciar sesión'}
                      </Button>
                    </div>

                    {googleClientId ? (
                      <div className="mt-6 rounded-3xl border border-slate-800/80 bg-slate-950/90 p-4 text-center">
                        <p className="text-xs text-slate-400 uppercase tracking-[0.25em] mb-3">O utiliza Google</p>
                        <div className="w-full flex justify-center [&>div]:!w-full [&_iframe]:!mx-auto">
                          <GoogleLogin
                            size="large"
                            width="320"
                            text={authMode === 'register' ? 'signup_with' : 'signin_with'}
                            onSuccess={async (cred) => {
                              if (!cred.credential) return;
                              try {
                                const tr = await api.google(cred.credential);
                                setSession(tr);
                                setUser(tr.user);
                                toast.success('Sesión con Google');
                                await refreshData();
                              } catch (e) {
                                toast.error(e instanceof Error ? e.message : 'Error Google');
                              }
                            }}
                            onError={() => toast.error('No se pudo iniciar sesión con Google')}
                          />
                        </div>
                      </div>
                    ) : (
                      <p className="mt-6 text-xs text-slate-400 leading-relaxed">
                        Para activar Google Sign-In, crea un cliente OAuth de tipo <strong>Aplicación web</strong> en Google
                        Cloud. Copia el ID de cliente en <code className="rounded-md bg-slate-900/70 px-1 py-0.5 text-[11px]">GOOGLE_CLIENT_ID</code>
                        dentro de <code className="rounded-md bg-slate-900/70 px-1 py-0.5 text-[11px]">backend/.env</code>.
                      </p>
                    )}
                  </div>
                </div>
              </motion.div>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
              <FeatureCard
                icon={<Stethoscope className="h-10 w-10 text-primary" />}
                title="Triaje clínico AI"
                description="Clasificación automática de síntomas para priorizar la atención."
              />
              <FeatureCard
                icon={<LayoutDashboard className="h-10 w-10 text-primary" />}
                title="Riesgo de no-show"
                description="Alertas predictivas para reducir cancelaciones y optimizar agenda."
              />
              <FeatureCard
                icon={<CalendarIcon className="h-10 w-10 text-primary" />}
                title="Horarios en tiempo real"
                description="Solo muestra bloques disponibles que realmente se pueden agendar."
              />
              <FeatureCard
                icon={<UserIcon className="h-10 w-10 text-primary" />}
                title="Inicio con Google"
                description="Accede con usuario y contraseña, o usa Google Sign-In para entrar rápido."
              />
            </div>
          </div>
        ) : (
          <AnimatePresence mode="wait">
            <motion.div
              key={user.role}
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.98 }}
              transition={{ duration: 0.4 }}
              className="space-y-16"
            >
              {user.role === 'admin' && (
                <section className="space-y-6">
                  <div className="flex items-end justify-between gap-4 flex-wrap">
                    <div>
                      <h2 className="text-3xl md:text-4xl font-black tracking-tight">Panel y alertas</h2>
                      <p className="text-muted-foreground font-medium">
                        Métricas y riesgo en una sola vista con scroll.
                      </p>
                    </div>
                    <Badge className="bg-primary/10 text-primary border-primary/20 px-4 py-1.5 rounded-full font-bold">
                      {appointments.length} citas
                    </Badge>
                  </div>
                  <Dashboard appointments={appointments} />
                  {riskAlerts.length > 0 && (
                    <Card className="p-6 rounded-[28px] border border-border/60">
                      <h3 className="text-xl font-black tracking-tight mb-4">Alertas predictivas (API)</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {riskAlerts.map((a) => (
                          <div key={a.appointment_id} className="p-4 rounded-2xl bg-muted/40 border border-border/50">
                            <p className="font-bold">{a.patient_name || 'Paciente'}</p>
                            <p className="text-xs text-muted-foreground">
                              {a.specialty} • {format(new Date(a.start_at), 'PPp', { locale: es })}
                            </p>
                            <p className="text-sm mt-2">{a.suggested_action}</p>
                            <Badge className="mt-2" variant="outline">
                              {(a.no_show_risk * 100).toFixed(0)}% riesgo
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </Card>
                  )}
                </section>
              )}

              <section className="space-y-6">
                <div className="flex items-end justify-between gap-4 flex-wrap">
                  <div>
                    <h2 className="text-3xl md:text-4xl font-black tracking-tight">
                      {user.role === 'admin' ? 'Agenda inteligente' : 'Tu cita en una sola vista'}
                    </h2>
                    <p className="text-muted-foreground font-medium">
                      {user.role === 'admin'
                        ? 'Listado completo y eliminación de citas con análisis predictivo.'
                        : 'Describe tus síntomas, revisa especialidad sugerida y elige el mejor horario.'}
                    </p>
                  </div>
                </div>

                {user.role === 'admin' ? (
                  <div className="max-w-5xl mx-auto space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {appointments.map((apt) => (
                        <motion.div
                          key={apt.id}
                          whileHover={{ scale: 1.01 }}
                          className="bg-card p-6 rounded-[24px] border border-border shadow-sm flex justify-between items-center group transition-all hover:border-primary/30"
                        >
                          <div className="flex gap-4 items-center">
                            <div
                              className={`w-12 h-12 rounded-2xl flex items-center justify-center ${
                                apt.urgency === 'high' ? 'bg-destructive/10 text-destructive' : 'bg-primary/10 text-primary'
                              }`}
                            >
                              <UserIcon className="h-6 w-6" />
                            </div>
                            <div>
                              <p className="font-bold text-foreground text-lg">{apt.patientName}</p>
                              <p className="text-sm text-muted-foreground font-medium">
                                {apt.specialty} • {format(apt.date, 'PPP', { locale: es })}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="flex flex-col items-end gap-2">
                              <Badge
                                className={`text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-widest ${
                                  apt.urgency === 'high' ? 'bg-destructive text-white' : 'bg-primary text-white'
                                }`}
                              >
                                {apt.urgency}
                              </Badge>
                              <span className="text-[10px] font-bold text-muted-foreground">
                                Riesgo: {(apt.noShowRisk * 100).toFixed(0)}%
                              </span>
                            </div>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => deleteAppointment(apt.id)}
                              className="rounded-xl hover:bg-destructive/10 hover:text-destructive opacity-0 group-hover:opacity-100 transition-all"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                    {appointments.length === 0 && (
                      <div className="text-center py-24 bg-muted/30 rounded-[32px] border-2 border-dashed border-border">
                        <p className="text-muted-foreground font-bold">No hay citas registradas en el sistema.</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-12">
                    <TriageForm onSchedule={handleSchedule} isSubmitting={isScheduling} />
                    <AssistantPanel />
                    <section className="space-y-6">
                      <div className="flex items-center justify-between gap-4">
                        <div>
                          <h3 className="text-2xl font-black tracking-tight">Historial de citas</h3>
                          <p className="text-sm text-muted-foreground">Aquí verás tus citas confirmadas y su estado.</p>
                        </div>
                        <Badge className="bg-primary/10 text-primary border-primary/20 px-4 py-1.5 rounded-full font-bold text-xs uppercase tracking-widest">
                          {appointments.length} registros
                        </Badge>
                      </div>
                      {appointments.length === 0 ? (
                        <Card className="p-8 rounded-[32px] border border-dashed border-border bg-muted/40 text-center">
                          <p className="font-bold text-muted-foreground">Aún no tienes citas agendadas.</p>
                          <p className="text-sm text-muted-foreground mt-2">Confirma una cita para verla aquí en tu historial.</p>
                        </Card>
                      ) : (
                        <div className="grid gap-4">
                          {appointments.map((apt) => {
                            const expanded = expandedAppointmentId === apt.id;
                            return (
                              <Card key={apt.id} className="p-6 rounded-[32px] border border-border shadow-sm bg-white">
                                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                                  <div>
                                    <p className="text-sm text-muted-foreground">{format(apt.date, 'PPP', { locale: es })}</p>
                                    <h4 className="text-xl font-black tracking-tight mt-2">{apt.specialty}</h4>
                                    <p className="text-sm text-muted-foreground mt-1">Urgencia: {apt.urgency}</p>
                                  </div>
                                  <div className="flex items-center gap-3">
                                    <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200 uppercase text-[10px] font-bold px-3 py-1 rounded-full">
                                      {appointmentStatusLabels[apt.status] || apt.status}
                                    </Badge>
                                    <span className="text-xs text-muted-foreground font-medium">{format(apt.date, 'p', { locale: es })}</span>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => setExpandedAppointmentId(expanded ? null : apt.id)}
                                      className="rounded-full text-[11px] font-bold px-3 py-2"
                                    >
                                      {expanded ? 'Ocultar detalles' : 'Ver detalles'}
                                    </Button>
                                  </div>
                                </div>
                                {expanded && (
                                  <div className="mt-4 rounded-3xl bg-muted/60 p-4 border border-border/50">
                                    <p className="text-sm font-bold text-muted-foreground uppercase tracking-[0.2em] mb-2">
                                      Detalles de la cita
                                    </p>
                                    {apt.description ? (
                                      <p className="text-sm text-foreground mb-2">
                                        <span className="font-semibold">Descripción:</span> {apt.description}
                                      </p>
                                    ) : null}
                                    {apt.triageReasoning ? (
                                      <p className="text-sm text-foreground mb-2">
                                        <span className="font-semibold">Razonamiento IA:</span> {apt.triageReasoning}
                                      </p>
                                    ) : null}
                                    <p className="text-sm text-muted-foreground">
                                      No-show riesgo: {(apt.noShowRisk * 100).toFixed(0)}%
                                    </p>
                                  </div>
                                )}
                              </Card>
                            );
                          })}
                        </div>
                      )}
                    </section>
                  </div>
                )}
              </section>

              <section>
                <div className="max-w-xl mx-auto bg-card p-10 rounded-[40px] border border-border shadow-2xl text-center space-y-6">
                  <div className="relative">
                    <img
                      src={user.photo_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.display_name || user.email)}`}
                      alt="Perfil"
                      className="w-28 h-28 rounded-[32px] mx-auto border-4 border-background shadow-xl object-cover"
                    />
                  </div>
                  <div className="space-y-2">
                    <h2 className="text-3xl font-black tracking-tight">{user.display_name || 'Usuario'}</h2>
                    <p className="text-muted-foreground font-medium">{user.email}</p>
                    <Badge className="mt-2 bg-secondary text-primary px-6 py-1.5 rounded-full font-bold text-xs uppercase tracking-widest border border-primary/10">
                      {user.role}
                    </Badge>
                  </div>
                  <div className="pt-6 border-t border-border/50 grid grid-cols-2 gap-4 text-left">
                    <div className="p-4 bg-muted/50 rounded-2xl">
                      <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1">
                        Miembro desde
                      </p>
                      <p className="font-bold text-sm">{format(new Date(user.created_at), 'MMM yyyy', { locale: es })}</p>
                    </div>
                    <div className="p-4 bg-muted/50 rounded-2xl">
                      <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1">Estado</p>
                      <p className="font-bold text-sm text-green-600">Activa</p>
                    </div>
                  </div>
                </div>
              </section>
            </motion.div>
          </AnimatePresence>
        )}
      </main>

      <footer className="mt-32 py-16 border-t border-border/50 bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-primary rounded-full" />
            <span className="text-sm font-black tracking-tighter uppercase italic">
              MediFlow <span className="text-primary not-italic">Medical</span>
            </span>
          </div>
          <p className="text-muted-foreground text-xs font-medium">© 2026 MediFlow AI. Todos los derechos reservados.</p>
          <div className="flex gap-6">
            <span className="text-xs font-bold text-muted-foreground">FastAPI · PostgreSQL · React</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
