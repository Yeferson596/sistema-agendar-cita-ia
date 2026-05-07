import React, { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, Sparkles, BookOpen, RefreshCcw } from 'lucide-react';
import { api } from '@/src/api/client';

export default function AssistantPanel() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAsk = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setAnswer('');
    setSources([]);
    try {
      const response = await api.assistant(question.trim());
      setAnswer(response.answer);
      setSources(response.sources || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error en la consulta');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setQuestion('');
    setAnswer('');
    setSources([]);
    setError(null);
  };

  return (
    <Card className="p-6 rounded-[32px] border border-border shadow-xl bg-gradient-to-br from-slate-50 via-white to-white">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-3xl bg-primary/10 text-primary shadow-sm">
            <Sparkles className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-2xl md:text-3xl font-black tracking-tight">Asistente RAG</h3>
            <p className="text-sm text-muted-foreground max-w-2xl">
              Respuestas inteligentes con contexto de la clínica y guías médicas; ideal para aclarar dudas de triaje y agendamiento.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Badge className="bg-primary/10 text-primary px-3 py-2 rounded-full uppercase text-[10px] font-bold tracking-[0.25em]">
            RAG + GROQ
          </Badge>
          <Badge className="bg-muted/80 text-muted-foreground px-3 py-2 rounded-full uppercase text-[10px] font-bold tracking-[0.25em]">
            Consultas rápidas
          </Badge>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
        <div className="space-y-4">
          <div className="rounded-[28px] border border-border/60 bg-slate-50 p-4 shadow-sm">
            <p className="text-sm text-muted-foreground uppercase tracking-[0.2em] mb-3">Tu pregunta</p>
            <Textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="¿Qué debo considerar antes de agendar una consulta de cardiología?"
              className="min-h-[160px] text-base p-4 rounded-[24px] border-border/50 bg-white shadow-sm"
            />
            <p className="mt-3 text-xs text-muted-foreground">Usa frases claras para obtener mejores respuestas. Presiona el botón cuando estés listo.</p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <Button
              type="button"
              onClick={handleAsk}
              disabled={loading || !question.trim()}
              className="rounded-2xl bg-primary text-white h-14 font-black flex-1"
            >
              {loading ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : <Sparkles className="mr-2 h-5 w-5" />}
              {loading ? 'Generando...' : 'Consultar asistente'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={handleClear}
              disabled={loading && !question.trim()}
              className="rounded-2xl h-14 font-bold"
            >
              <RefreshCcw className="mr-2 h-5 w-5" /> Limpiar
            </Button>
          </div>

          {error ? (
            <div className="rounded-3xl border border-destructive/20 bg-destructive/10 p-4 text-sm text-destructive font-semibold">
              {error}
            </div>
          ) : null}

          <div className="rounded-[28px] border border-border/60 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between gap-3 mb-4">
              <div>
                <p className="text-sm text-muted-foreground uppercase tracking-[0.2em]">Estado</p>
                <p className="text-base font-bold text-foreground">{loading ? 'Consultando...' : 'Listo para tu pregunta'}</p>
              </div>
              <Badge className="bg-slate-100 text-slate-600 px-3 py-2 rounded-full uppercase text-[10px] font-bold tracking-[0.25em]">
                {loading ? 'Procesando' : 'Preparado'}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground leading-6">
              El asistente usa información de los documentos internos y guías externas para generar una respuesta contextualizada. Si no está disponible la clave de Gemini, se mostrará un resumen local.
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-[28px] border border-border/60 bg-slate-950/95 p-5 text-white shadow-lg shadow-slate-900/10 min-h-[260px]">
            <p className="text-sm uppercase tracking-[0.2em] text-slate-300 mb-4">Respuesta</p>
            {answer ? (
              <div className="space-y-4">
                <p className="text-sm leading-7 text-slate-100">{answer}</p>
              </div>
            ) : (
              <p className="text-sm leading-7 text-slate-400">Escribe una pregunta y pulsa el botón para recibir una respuesta del asistente.</p>
            )}
          </div>

          <div className="rounded-[28px] border border-border/60 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-3 text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">
              <BookOpen className="h-4 w-4" />
              <span>Fuentes relevantes</span>
            </div>
            {sources.length > 0 ? (
              <ul className="space-y-2 text-sm text-muted-foreground">
                {sources.map((source) => (
                  <li key={source} className="list-disc list-inside">
                    {source}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">Las fuentes aparecerán aquí cuando el asistente genere una respuesta.</p>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
