"use client";

import { useQuery } from '@tanstack/react-query';
import { getAgents } from '@/services/api';
import Link from 'next/link';

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
