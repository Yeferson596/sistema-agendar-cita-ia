import React, { useEffect, useState } from 'react';
import { Card, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Calendar } from '@/components/ui/calendar';
import { api } from '@/src/api/client';
import { Loader2, Send, Calendar as CalendarIcon, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { motion } from 'motion/react';

export type TriageResult = {
  specialty: string;
  urgency: 'low' | 'medium' | 'high';
  reasoning: string;
};

interface TriageFormProps {
  onSchedule: (triage: TriageResult, startAt: Date) => void;
  isSubmitting: boolean;
}

export default function TriageForm({ onSchedule, isSubmitting }: TriageFormProps) {
  const [description, setDescription] = useState('');
  const [triage, setTriage] = useState<TriageResult | null>(null);
  const [selectedUrgency, setSelectedUrgency] = useState<TriageResult['urgency'] | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date());
  const [selectedStart, setSelectedStart] = useState<string | null>(null);
  const [loadingTriage, setLoadingTriage] = useState(false);
  const [slots, setSlots] = useState<{ start_at: string; end_at: string; label: string | null }[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);

  const handleTriage = async () => {
    if (!description.trim()) return;
    setLoadingTriage(true);
    try {
      const result = await api.triage(description);
      setTriage({
        specialty: result.specialty,
        urgency: result.urgency,
        reasoning: result.reasoning,
      });
      setSelectedUrgency(result.urgency);
      setSelectedStart(null);
    } catch (error) {
      console.error('Triage error:', error);
    } finally {
      setLoadingTriage(false);
    }
  };

  const effectiveUrgency = selectedUrgency ?? (triage ? triage.urgency : 'medium');

  useEffect(() => {
    if (!triage || !selectedDate) {
      setSlots([]);
      return;
    }
    const dateStr = format(selectedDate, 'yyyy-MM-dd');
    let cancelled = false;
    setLoadingSlots(true);
    api
      .availability(triage.specialty, dateStr, effectiveUrgency)
      .then((list) => {
        if (!cancelled) {
          setSlots(list);
          setSelectedStart(null);
        }
      })
      .catch(() => {
        if (!cancelled) setSlots([]);
      })
      .finally(() => {
        if (!cancelled) setLoadingSlots(false);
      });
    return () => {
      cancelled = true;
    };
  }, [triage, selectedDate, effectiveUrgency]);

  const handleScheduleClick = () => {
    if (!triage || !selectedStart) return;
    const start = new Date(selectedStart);
    onSchedule({ ...triage, urgency: effectiveUrgency }, start);
  };

  const urgencyColors = {
    low: 'bg-blue-100 text-blue-800 border-blue-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    high: 'bg-red-100 text-red-800 border-red-200',
  };

  return (
    <div className="bento-grid max-w-7xl mx-auto">
      <Card className="col-span-12 lg:col-span-4 lg:row-span-2 bento-item glass-card flex flex-col">
        <div className="flex items-center gap-2 mb-6">
          <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
          <span className="text-[10px] font-black text-primary tracking-[0.2em] uppercase">Módulo de Triaje</span>
        </div>

        <div className="space-y-2 mb-8">
          <CardTitle className="text-3xl font-black tracking-tighter">Describe tus síntomas</CardTitle>
          <CardDescription className="text-muted-foreground font-medium">
            Análisis con IA médica en el servidor; la agenda solo muestra horarios libres reales.
          </CardDescription>
        </div>

        <div className="flex-1 space-y-6">
          <Textarea
            placeholder="Describe tus síntomas detalladamente..."
            className="min-h-[200px] text-lg p-6 rounded-3xl border-2 border-border/50 focus:border-primary focus:ring-0 bg-white shadow-inner transition-all placeholder:text-muted-foreground/50"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <Button
            onClick={handleTriage}
            disabled={loadingTriage || !description.trim()}
            className="w-full h-16 text-lg font-black rounded-2xl bg-primary hover:bg-primary/90 shadow-xl shadow-primary/20 transition-all active:scale-95 disabled:opacity-50"
          >
            {loadingTriage ? <Loader2 className="mr-2 h-6 w-6 animate-spin" /> : <Send className="mr-2 h-6 w-6" />}
            Analizar Prioridad
          </Button>

          {triage && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="mt-8 p-6 bg-white border-2 border-primary/10 rounded-3xl shadow-sm"
            >
              <div className="flex justify-between items-center mb-6">
                <div className="space-y-2">
                  <Badge
                    className={`text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest ${urgencyColors[effectiveUrgency]}`}
                  >
                    Urgencia {effectiveUrgency === 'high' ? 'Alta' : effectiveUrgency === 'medium' ? 'Media' : 'Baja'}
                  </Badge>
                  <p className="text-[10px] text-muted-foreground leading-tight uppercase tracking-[0.3em]">
                    Calculada automáticamente por IA al analizar prioridad
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {(['low', 'medium', 'high'] as const).map((level) => (
                      <button
                        key={level}
                        type="button"
                        onClick={() => setSelectedUrgency(level)}
                        className={`rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-widest transition-all ${
                          selectedUrgency === level
                            ? 'bg-primary text-white shadow-lg shadow-primary/20'
                            : 'bg-muted text-muted-foreground hover:bg-muted/80'
                        }`}
                      >
                        {level === 'high' ? 'Alta' : level === 'medium' ? 'Media' : 'Baja'}
                      </button>
                    ))}
                  </div>
                  <p className="text-[10px] text-muted-foreground font-medium uppercase tracking-widest mt-2">
                    La IA determinó automáticamente la urgencia cuando analizas la prioridad. Ajusta solo si necesitas un cambio manual.
                  </p>
                </div>
                <span className="text-[10px] font-bold text-muted-foreground uppercase">IA</span>
              </div>
              <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-1">Especialidad</p>
              <p className="text-2xl font-black text-primary mb-4 tracking-tight">{triage.specialty}</p>
              <div className="h-px bg-border/50 mb-4" />
              <p className="text-sm text-muted-foreground leading-relaxed font-medium italic">"{triage.reasoning}"</p>
            </motion.div>
          )}
        </div>
      </Card>

      <Card className="col-span-12 lg:col-span-8 bento-item">
        <div className="flex justify-between items-center mb-8">
          <div>
            <span className="text-[10px] font-black text-muted-foreground tracking-[0.2em] uppercase mb-1 block">
              Agenda Inteligente
            </span>
            <CardTitle className="text-3xl font-black tracking-tighter">Selecciona tu Fecha</CardTitle>
          </div>
          <div className="hidden sm:block text-right">
            <p className="text-[10px] font-bold text-green-600 uppercase tracking-widest">Disponibilidad</p>
            <p className="text-xs font-bold text-muted-foreground">Actualizado al cambiar fecha</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-start">
          <div className="glass-card p-4 rounded-[32px] border border-border/50">
            <Calendar
              mode="single"
              selected={selectedDate}
              onSelect={setSelectedDate}
              className="rounded-2xl w-full"
              locale={es}
              disabled={(date) => date < new Date(new Date().setHours(0, 0, 0, 0))}
            />
          </div>
          <div className="space-y-8">
            <div>
              <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest mb-4">
                Horarios disponibles
              </p>
              {loadingSlots ? (
                <div className="flex items-center gap-2 text-muted-foreground font-bold">
                  <Loader2 className="h-5 w-5 animate-spin" /> Cargando horarios...
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-3 max-h-[280px] overflow-y-auto pr-1">
                  {slots
                    .sort((a, b) => new Date(a.start_at).getTime() - new Date(b.start_at).getTime())
                    .map((s) => {
                      const label = format(new Date(s.start_at), 'HH:mm');
                      const active = selectedStart === s.start_at;
                      return (
                        <button
                          key={s.start_at}
                          type="button"
                          onClick={() => setSelectedStart(s.start_at)}
                          className={`p-4 border-2 rounded-2xl text-center text-sm font-black transition-all active:scale-95 ${
                            active
                              ? 'border-primary bg-primary text-white shadow-lg shadow-primary/20'
                              : 'border-border/50 text-foreground hover:border-primary/50 hover:bg-primary/5'
                          }`}
                        >
                          {label}
                          {s.label ? <span className="block text-[9px] font-bold opacity-80 mt-1">{s.label}</span> : null}
                        </button>
                      );
                    })}
                  {triage && !loadingSlots && slots.length === 0 && (
                    <p className="col-span-2 text-sm text-muted-foreground font-medium">
                      No hay cupos libres ese día para esta especialidad. Prueba otra fecha.
                    </p>
                  )}
                  {!triage && (
                    <p className="col-span-2 text-sm text-muted-foreground font-medium">
                      Primero ejecuta el triaje para ver horarios filtrados por urgencia.
                    </p>
                  )}
                </div>
              )}
            </div>

            <div className="pt-6 border-t border-border/50">
              <Button
                className="w-full h-16 text-lg font-black rounded-2xl bg-gradient-to-r from-primary to-cyan-500 text-white shadow-2xl shadow-primary/20 transition-all disabled:opacity-50 active:scale-[0.98]"
                disabled={isSubmitting || !triage || !selectedStart}
                onClick={handleScheduleClick}
              >
                {isSubmitting ? <Loader2 className="mr-2 h-6 w-6 animate-spin" /> : 'Confirmar Cita'}
              </Button>
              <p className="text-[10px] text-center text-muted-foreground mt-4 font-bold uppercase tracking-widest">
                Riesgo de inasistencia calculado en el servidor con histórico
              </p>
            </div>
          </div>
        </div>
      </Card>

      <Card className="col-span-12 md:col-span-6 lg:col-span-4 bento-item flex flex-col justify-between">
        <div>
          <span className="text-[10px] font-black text-muted-foreground tracking-[0.2em] uppercase mb-4 block">
            Recordatorios
          </span>
          <div className="space-y-6">
            <div className="flex gap-4 items-start">
              <div className="w-10 h-10 rounded-xl bg-destructive/10 text-destructive flex items-center justify-center shrink-0">
                <AlertCircle className="h-5 w-5" />
              </div>
              <div>
                <p className="font-bold text-sm">Triaje seguro</p>
                <p className="text-xs text-muted-foreground font-medium">
                  Las claves de IA no salen del backend; solo se envía tu descripción para clasificar.
                </p>
              </div>
            </div>
            <div className="flex gap-4 items-start">
              <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
                <CalendarIcon className="h-5 w-5" />
              </div>
              <div>
                <p className="font-bold text-sm">Agenda única</p>
                <p className="text-xs text-muted-foreground font-medium">
                  Vista consolidada: síntomas, prioridad y horarios en la misma pantalla.
                </p>
              </div>
            </div>
          </div>
        </div>
        <div className="mt-8 pt-6 border-t border-border/50">
          <p className="text-[10px] font-bold text-primary uppercase tracking-widest">PostgreSQL + FastAPI</p>
        </div>
      </Card>

      <Card className="col-span-12 md:col-span-6 lg:col-span-4 bento-item bg-primary text-white">
        <span className="text-[10px] font-black text-white/60 tracking-[0.2em] uppercase mb-6 block">MediFlow</span>
        <h4 className="text-2xl font-black tracking-tighter mb-4 leading-tight">
          Tu salud, optimizada con datos del consultorio.
        </h4>
        <p className="text-sm text-white/80 font-medium leading-relaxed mb-8">
          La disponibilidad se cruza en tiempo real con citas existentes; el riesgo de no-show usa historial
          estadístico.
        </p>
        <div className="flex items-center gap-2">
          <div className="flex -space-x-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="w-8 h-8 rounded-full border-2 border-primary bg-white/20" />
            ))}
          </div>
          <span className="text-[10px] font-bold text-white/60">Vista única</span>
        </div>
      </Card>
    </div>
  );
}
