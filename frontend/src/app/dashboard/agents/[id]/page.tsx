'use client'

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import MainLayout from '@/components/layout/MainLayout';

// Define el tipo para nuestros datos de agente
type Agent = {
  id?: string;
  name: string;
  base_prompt: string;
  status: 'active' | 'paused';
  guardrails?: string;
};

export default function AgentDetailPage({ params }: { params: { id:string } }) {
  const router = useRouter();
  const supabase = createClient();
  const isNew = params.id === 'new';

  const [agent, setAgent] = useState<Agent>({ name: '', base_prompt: '', status: 'active', guardrails: '' });
  const [loading, setLoading] = useState(!isNew);

  useEffect(() => {
    if (!isNew) {
      const fetchAgent = async () => {
        const { data, error } = await supabase
          .from('agents')
          .select('*')
          .eq('id', params.id)
          .single();

        if (error || !data) {
          console.error('Error al obtener el agente:', error);
          alert('Fallo al obtener los datos del agente. Redirigiendo al panel de control.');
          router.push('/dashboard');
        } else {
          setAgent(data);
        }
        setLoading(false);
      };
      fetchAgent();
    }
  }, [params.id, isNew, router, supabase]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();

    let error;
    if (isNew) {
      // Crear nuevo agente
      ({ error } = await supabase.from('agents').insert({ ...agent }));
    } else {
      // Actualizar agente existente
      ({ error } = await supabase.from('agents').update({ ...agent }).eq('id', params.id));
    }

    if (error) {
      alert(`Error al guardar el agente: ${error.message}`);
    } else {
      alert('¡Agente guardado exitosamente!');
      router.push('/dashboard');
      router.refresh(); // Para reflejar los cambios en la lista del panel de control
    }
  };

  const handleStatusToggle = async () => {
    const newStatus = agent.status === 'active' ? 'paused' : 'active';
    const newStatusSpanish = newStatus === 'active' ? 'activo' : 'pausado';
    setAgent({ ...agent, status: newStatus });

    const { error } = await supabase
      .from('agents')
      .update({ status: newStatus })
      .eq('id', params.id);

    if (error) {
      alert(`Error al actualizar el estado: ${error.message}`);
      // Revertir el estado si la actualización falla
      setAgent({ ...agent, status: agent.status });
    } else {
      alert(`El agente ahora está ${newStatusSpanish}.`);
    }
  };

  if (loading) {
    return <MainLayout><p>Cargando agente...</p></MainLayout>;
  }

  return (
    <MainLayout>
      <h1 className="text-3xl font-bold mb-8">{isNew ? 'Crear Nuevo Agente' : `Editar Agente: ${agent.name}`}</h1>

      <form onSubmit={handleSave} className="bg-white p-8 rounded-lg shadow-md">
        {/* Pausa de Emergencia */}
        {!isNew && (
          <div className="flex items-center justify-between p-4 bg-yellow-100 border-l-4 border-yellow-500 rounded-md mb-8">
            <div>
              <h3 className="font-bold text-yellow-800">Modo de Pausa de Emergencia</h3>
              <p className="text-sm text-yellow-700">
                Pausa o reanuda instantáneamente todas las interacciones de este agente.
              </p>
            </div>
            <button
              type="button"
              onClick={handleStatusToggle}
              className={`px-6 py-2 rounded-full font-semibold text-white ${
                agent.status === 'active' ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'
              }`}
            >
              {agent.status === 'active' ? 'PAUSAR' : 'REANUDAR'}
            </button>
          </div>
        )}

        <div className="mb-6">
          <label htmlFor="name" className="block text-lg font-medium mb-2">Nombre del Agente</label>
          <input
            id="name"
            type="text"
            value={agent.name}
            onChange={(e) => setAgent({ ...agent, name: e.target.value })}
            className="w-full p-3 border rounded-md"
            placeholder="Ej: Asistente de Ventas"
            required
          />
        </div>

        <div className="mb-6">
          <label htmlFor="base_prompt" className="block text-lg font-medium mb-2">Prompt Base</label>
          <textarea
            id="base_prompt"
            value={agent.base_prompt}
            onChange={(e) => setAgent({ ...agent, base_prompt: e.target.value })}
            className="w-full p-3 border rounded-md h-48"
            placeholder="Describe la personalidad, el rol y las instrucciones del agente..."
            required
          />
        </div>

        <div className="mb-6">
          <label htmlFor="guardrails" className="block text-lg font-medium mb-2">Reglas de Comportamiento</label>
          <textarea
            id="guardrails"
            value={agent.guardrails || ''}
            onChange={(e) => setAgent({ ...agent, guardrails: e.target.value })}
            className="w-full p-3 border rounded-md h-32"
            placeholder="Define temas prohibidos o reglas para el agente. Ej: 'No discutir sobre política.'"
          />
        </div>

        {/* Carga de Documentos RAG - Placeholder */}
        <div className="mb-8">
          <label className="block text-lg font-medium mb-2">Base de Conocimiento (RAG)</label>
          <div className="p-6 border-2 border-dashed rounded-md text-center">
            <p className="text-gray-500">La funcionalidad de carga de documentos estará disponible próximamente.</p>
          </div>
        </div>

        <div className="flex justify-end">
          <button type="button" onClick={() => router.back()} className="px-6 py-2 mr-4 bg-gray-200 rounded hover:bg-gray-300">
            Cancelar
          </button>
          <button type="submit" className="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
            Guardar Agente
          </button>
        </div>
      </form>
    </MainLayout>
  );
}
