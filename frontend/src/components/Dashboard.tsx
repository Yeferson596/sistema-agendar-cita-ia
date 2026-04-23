import React from 'react';
import { Card, CardTitle } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, Users, Calendar, TrendingUp } from 'lucide-react';
import { format } from 'date-fns';
import { motion } from 'motion/react';

export type AppointmentVM = {
  id: string;
  patientName: string;
  specialty: string;
  urgency: string;
  status: string;
  description?: string | null;
  triageReasoning?: string | null;
  noShowRisk: number;
  date: Date;
};

interface DashboardProps {
  appointments: AppointmentVM[];
}

export default function Dashboard({ appointments }: DashboardProps) {
  const stats = {
    total: appointments.length,
    highRisk: appointments.filter((a) => a.noShowRisk > 0.7).length,
    today: appointments.filter((a) => format(a.date, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd')).length,
    avgRisk:
      appointments.length > 0
        ? (appointments.reduce((acc, curr) => acc + (curr.noShowRisk || 0), 0) / appointments.length).toFixed(2)
        : 0,
  };

  const chartData = appointments.slice(0, 10).map((a) => ({
    name: a.patientName || 'Paciente',
    risk: (a.noShowRisk * 100).toFixed(0),
    urgency: a.urgency,
  }));

  return (
    <div className="bento-grid max-w-7xl mx-auto">
      <div className="col-span-12 md:col-span-6 lg:col-span-3">
        <StatCard title="Total Citas" value={stats.total} icon={<Calendar className="h-6 w-6" />} color="blue" />
      </div>
      <div className="col-span-12 md:col-span-6 lg:col-span-3">
        <StatCard title="Citas Hoy" value={stats.today} icon={<Users className="h-6 w-6" />} color="green" />
      </div>
      <div className="col-span-12 md:col-span-6 lg:col-span-3">
        <StatCard title="Alto Riesgo" value={stats.highRisk} icon={<AlertTriangle className="h-6 w-6" />} color="red" />
      </div>
      <div className="col-span-12 md:col-span-6 lg:col-span-3">
        <StatCard
          title="Riesgo Promedio"
          value={`${(Number(stats.avgRisk) * 100).toFixed(0)}%`}
          icon={<TrendingUp className="h-6 w-6" />}
          color="orange"
        />
      </div>

      <Card className="col-span-12 lg:col-span-8 bento-item min-h-[450px] glass-card overflow-hidden shadow-[0_30px_70px_-40px_rgba(15,23,42,0.7)]">
        <div className="p-8 bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 text-white rounded-[32px] shadow-xl shadow-slate-900/10 mb-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <span className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400 block mb-2">
                Métrica predictiva
              </span>
              <CardTitle className="text-3xl md:text-4xl font-black tracking-tighter">Riesgo de inasistencia</CardTitle>
            </div>
            <div className="flex flex-wrap gap-2 items-center">
              <Badge className="rounded-full bg-white/10 text-white border border-white/10 font-bold text-[10px] uppercase px-3 py-2">
                Histórico
              </Badge>
              <Badge className="rounded-full bg-slate-800/90 text-slate-200 font-bold text-[10px] uppercase px-3 py-2">
                {appointments.length ? `${appointments.length} citas analizadas` : 'Sin datos disponibles'}
              </Badge>
            </div>
          </div>
          <p className="mt-6 max-w-2xl text-sm text-slate-300 leading-7">
            Visualiza los principales riesgos de no asistencia y prioriza acciones para los pacientes con mayor probabilidad de no presentarse.
          </p>
        </div>

        <div className="h-[320px] w-full rounded-[32px] bg-white p-6 shadow-inner shadow-slate-200/50">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ left: 0, right: 0, top: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis
                dataKey="name"
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 11, fill: '#64748b', fontWeight: 700 }}
              />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#64748b', fontWeight: 700 }} />
              <Tooltip
                wrapperStyle={{ outline: 'none' }}
                contentStyle={{
                  borderRadius: '24px',
                  border: 'none',
                  boxShadow: '0 20px 35px -15px rgba(15,23,42,0.15)',
                  padding: '18px',
                }}
                cursor={{ fill: '#f8fafc' }}
              />
              <Bar dataKey="risk" radius={[16, 16, 0, 0]} barSize={44}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={Number(entry.risk) > 70 ? '#ef4444' : '#2563eb'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card className="col-span-12 lg:col-span-4 bento-item flex flex-col rounded-[32px] border border-border/70 bg-white shadow-xl">
        <div className="p-8 border-b border-border/70">
          <span className="text-[10px] font-black text-primary tracking-[0.2em] uppercase mb-2 block">
            Alertas críticas
          </span>
          <CardTitle className="text-3xl font-black tracking-tighter">Acciones sugeridas</CardTitle>
          <p className="mt-3 text-sm text-muted-foreground leading-6">
            Prioriza estas citas con riesgo alto de inasistencia usando recordatorios, confirmaciones y liberación rápida de cupos.
          </p>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto p-6 custom-scrollbar">
          {appointments
            .filter((a) => a.noShowRisk > 0.6)
            .map((a, i) => (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.08 }}
                key={a.id}
                className="rounded-[28px] border border-slate-200 bg-slate-50 p-5 shadow-sm"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="font-bold text-slate-900">{a.patientName}</p>
                    <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mt-1">{a.specialty}</p>
                  </div>
                  <Badge className="rounded-full bg-rose-500/10 text-rose-600 text-[10px] font-black uppercase px-3 py-1">
                    {(a.noShowRisk * 100).toFixed(0)}%
                  </Badge>
                </div>
                <p className="mt-4 text-sm text-slate-700 leading-6">
                  Este paciente tiene alto riesgo de no presentarse; considera enviar un recordatorio y verificar si puede reagendar.
                </p>
              </motion.div>
            ))}
          {appointments.filter((a) => a.noShowRisk > 0.6).length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center gap-4 rounded-[28px] border border-dashed border-slate-200 bg-slate-50">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
                <Users className="h-6 w-6" />
              </div>
              <p className="text-sm font-semibold text-slate-700">Sin alertas críticas por ahora.</p>
              <p className="text-xs text-muted-foreground max-w-[18rem]">
                Las citas con riesgo alto aparecerán aquí para que puedas tomar acción rápidamente.
              </p>
            </div>
          )}
        </div>

        <div className="mt-4 px-8 py-5 border-t border-border/70 flex items-center justify-between">
          <span className="text-[10px] font-black text-slate-500 uppercase tracking-[0.25em]">Monitoreo activo</span>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs text-slate-500">En línea</span>
          </div>
        </div>
      </Card>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon,
  color,
}: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}) {
  const colors: Record<string, string> = {
    blue: 'bg-gradient-to-br from-primary to-sky-600 text-white shadow-primary/30',
    green: 'bg-gradient-to-br from-emerald-500 to-cyan-500 text-white shadow-emerald-300/30',
    red: 'bg-gradient-to-br from-destructive to-orange-500 text-white shadow-destructive/30',
    orange: 'bg-gradient-to-br from-orange-500 to-amber-500 text-white shadow-orange-300/30',
  };
  return (
    <Card className="bento-item border-none shadow-sm hover:shadow-xl transition-all duration-500 overflow-hidden group">
      <div className="flex flex-col gap-6">
        <div
          className={`w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg transition-transform duration-500 group-hover:scale-110 ${colors[color]}`}
        >
          {icon}
        </div>
        <div>
          <p className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] mb-1">{title}</p>
          <p className="text-4xl font-black text-foreground tracking-tighter">{value}</p>
        </div>
      </div>
    </Card>
  );
}
