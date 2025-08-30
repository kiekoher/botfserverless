"use client";

import { useQuery } from '@tanstack/react-query';
import { getAgents, Agent } from '@/services/api';
import Link from 'next/link';
import { Skeleton } from '@/components/ui/skeleton';

const statusTranslations: { [key: string]: string } = {
    active: 'activo',
    paused: 'pausado',
};

interface AgentListProps {
    deleteAgent: (formData: FormData) => Promise<void>;
}

const AgentListSkeleton = () => (
    <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
                <div key={i} className="flex justify-between items-center py-3 border-b last:border-b-0">
                    <Skeleton className="h-5 w-1/3" />
                    <div className="flex items-center space-x-4">
                        <Skeleton className="h-7 w-20 rounded-full" />
                        <Skeleton className="h-5 w-16" />
                        <Skeleton className="h-5 w-20" />
                    </div>
                </div>
            ))}
        </div>
    </div>
);

export default function AgentList({ deleteAgent }: AgentListProps) {
    const { data: agents, isLoading, isError, error } = useQuery({
        queryKey: ['agents'],
        queryFn: getAgents
    });

    if (isLoading) {
        return <AgentListSkeleton />;
    }

    if (isError) {
        return <p>Error al cargar los agentes: {error.message}</p>;
    }

    return (
        <div className="bg-white p-6 rounded-lg shadow-md">
            {agents && agents.length > 0 ? (
                <ul>
                    {agents.map((agent: Agent) => (
                        <li key={agent.id} className="flex justify-between items-center py-3 border-b last:border-b-0">
                            <span className="font-medium">{agent.name}</span>
                            <div className="flex items-center space-x-4">
                                <span className={`px-3 py-1 text-sm rounded-full ${
                                    agent.status === 'active' ? 'bg-green-200 text-green-800' : 'bg-yellow-200 text-yellow-800'
                                }`}>
                                    {statusTranslations[agent.status] || agent.status}
                                </span>
                                <Link href={`/dashboard/agents/${agent.id}`} className="text-blue-500 hover:underline">
                                    Editar
                                </Link>
                                <form action={deleteAgent}>
                                    <input type="hidden" name="agent_id" value={agent.id} />
                                    <button type="submit" className="text-red-500 hover:underline">
                                        Eliminar
                                    </button>
                                </form>
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
