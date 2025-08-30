import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import MainLayout from '@/components/layout/MainLayout'
import Link from 'next/link';
import { revalidatePath } from 'next/cache';
import AgentList from '@/components/dashboard/AgentList'; // Import the new component

export default async function DashboardPage() {
  const supabase = createClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) {
    return redirect('/login')
  }

  // Check if the user has completed onboarding
  const { data: profile } = await supabase
    .from('user_profiles')
    .select('has_completed_onboarding')
    .eq('id', user.id)
    .single();

  // If profile doesn't exist or onboarding is not complete, redirect
  if (!profile || !profile.has_completed_onboarding) {
    return redirect('/dashboard/onboarding');
  }

  // The server action remains here for now.
  // A full refactor would move this to a dedicated API endpoint.
  async function toggleAgentStatus(formData: FormData) {
    'use server'

    const supabase = createClient();
    const agentId = formData.get('agent_id') as string;
    const currentStatus = formData.get('current_status') as string;

    const newStatus = currentStatus === 'active' ? 'paused' : 'active';

    const { error } = await supabase
      .from('agents')
      .update({ status: newStatus })
      .eq('id', agentId);

    if (error) {
      console.error("Fallo al actualizar el estado del agente:", error);
      redirect('/dashboard?error=No se pudo actualizar el estado del agente');
    }

    revalidatePath('/dashboard');
  }

  async function deleteAgent(formData: FormData) {
    'use server'

    const supabase = createClient();
    const agentId = formData.get('agent_id') as string;

    const { error } = await supabase
      .from('agents')
      .delete()
      .eq('id', agentId);

    if (error) {
      console.error("Fallo al eliminar el agente:", error);
      redirect('/dashboard?error=No se pudo eliminar el agente');
    }

    revalidatePath('/dashboard');
  }

  return (
    <MainLayout>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Mis Agentes</h1>
        <Link href="/dashboard/agents/new" className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">
          + Nuevo Agente
        </Link>
      </div>
      {/* The direct data fetching and list rendering is replaced by the client component */}
      <AgentList deleteAgent={deleteAgent} />
    </MainLayout>
  )
}
