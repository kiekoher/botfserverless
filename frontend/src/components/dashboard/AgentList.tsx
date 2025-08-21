"use client";

import { useQuery } from '@tanstack/react-query';
import { getAgents } from '@/services/api';
import Link from 'next/link';

// This is the server action from the original page.
// For a full refactor, this would be a `useMutation` hook calling a PATCH endpoint.
// For now, we are keeping it to demonstrate the `useQuery` integration.
async function toggleAgentStatus(formData: FormData) {
    'use server'
    // This is a placeholder for the server action logic which would need to be
    // passed down or handled differently in a full client-side component architecture.
    // The original code for this exists in the page.tsx, we are focusing on fetching here.
    console.log("Toggling agent status for:", formData.get('agent_id'));
    // In a real scenario, you'd call the server action and revalidate.
}

const statusTranslations: { [key: string]: string } = {
    active: 'activo',
    paused: 'pausado',
};

export default function AgentList() {
    const { data: agents, isLoading, isError, error } = useQuery({
        queryKey: ['agents'],
        queryFn: getAgents
    });

    if (isLoading) {
        return <p>Cargando agentes...</p>;
    }

    if (isError) {
        return <p>Error al cargar los agentes: {error.message}</p>;
    }

    return (
        <div className="bg-white p-6 rounded-lg shadow-md">
            {agents && agents.length > 0 ? (
                <ul>
                    {agents.map((agent: any) => (
                        <li key={agent.id} className="flex justify-between items-center py-3 border-b last:border-b-0">
                            <span className="font-medium">{agent.name}</span>
                            <div className="flex items-center space-x-4">
                                <span className={`px-3 py-1 text-sm rounded-full ${
                                    agent.status === 'active' ? 'bg-green-200 text-green-800' : 'bg-yellow-200 text-yellow-800'
                                }`}>
                                    {statusTranslations[agent.status] || agent.status}
                                </span>
                                {/* The form action would need to be handled properly.
                                    This example focuses on displaying the data fetched via React Query. */}
                                <form action={toggleAgentStatus}>
                                    <input type="hidden" name="agent_id" value={agent.id} />
                                    <input type="hidden" name="current_status" value={agent.status} />
                                    <button type="submit" disabled className="px-3 py-1 text-sm text-white rounded bg-gray-400">
                                        Toggle
                                    </button>
                                </form>
                                <Link href={`/dashboard/agents/${agent.id}`} className="text-blue-500 hover:underline">
                                    Editar
                                </Link>
                            </div>
                        </li>
                    ))}
                </ul>
            ) : (
                <p>Aún no has creado ningún agente.</p>
            )}
        </div>
    );
}
