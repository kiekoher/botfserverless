import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import MainLayout from '@/components/layout/MainLayout'
import Link from 'next/link'

export default function NewAgentPage() {

  async function createAgent(formData: FormData) {
    'use server'

    const supabase = createClient()
    const { data: { user } } = await supabase.auth.getUser()

    if (!user) {
      return redirect('/login')
    }

    const newAgent = {
      user_id: user.id,
      name: formData.get('name') as string,
      base_prompt: formData.get('base_prompt') as string,
      guardrails: formData.get('guardrails') as string,
      status: 'active', // Estado por defecto
    }

    const { error } = await supabase.from('agents').insert(newAgent)

    if (error) {
      console.error('Error al crear el agente:', error)
      // Podríamos añadir una redirección a una página de error o mostrar una notificación
      redirect('/dashboard?error=No se pudo crear el agente')
    } else {
      redirect('/dashboard')
    }
  }

  return (
    <MainLayout>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Crear Nuevo Agente</h1>
        <Link href="/dashboard" className="px-4 py-2 bg-gray-200 text-black rounded hover:bg-gray-300">
          Cancelar
        </Link>
      </div>
      <div className="bg-white p-8 rounded-lg shadow-md">
        <form action={createAgent}>
          <div className="mb-4">
            <label htmlFor="name" className="block text-gray-700 font-bold mb-2">Nombre del Agente</label>
            <input
              type="text"
              id="name"
              name="name"
              className="w-full px-3 py-2 border rounded-lg"
              placeholder="Ej: Bot de Soporte al Cliente"
              required
            />
          </div>
          <div className="mb-4">
            <label htmlFor="base_prompt" className="block text-gray-700 font-bold mb-2">Prompt Base (Personalidad)</label>
            <textarea
              id="base_prompt"
              name="base_prompt"
              rows={6}
              className="w-full px-3 py-2 border rounded-lg"
              placeholder="Eres un asistente servicial y amigable..."
            />
          </div>
          <div className="mb-6">
            <label htmlFor="guardrails" className="block text-gray-700 font-bold mb-2">Reglas de Comportamiento</label>
            <textarea
              id="guardrails"
              name="guardrails"
              rows={4}
              className="w-full px-3 py-2 border rounded-lg"
              placeholder="Ej: No discutir sobre política. Nunca usar lenguaje ofensivo."
            />
          </div>
          <div className="flex justify-end">
            <button type="submit" className="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
              Guardar Agente
            </button>
          </div>
        </form>
      </div>
    </MainLayout>
  )
}
