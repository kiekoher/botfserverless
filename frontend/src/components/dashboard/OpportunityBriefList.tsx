"use client";
import { useQuery } from '@tanstack/react-query';
import { getOpportunityBriefs, OpportunityBrief } from '@/services/api';

export default function OpportunityBriefList() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['opportunityBriefs'],
    queryFn: getOpportunityBriefs,
  });

  if (isLoading) {
    return <p>Cargando oportunidades...</p>;
  }

  if (isError) {
    return <p>Error al cargar oportunidades: {error.message}</p>;
  }

  if (!data || data.length === 0) {
    return <p>No hay oportunidades registradas.</p>;
  }

  return (
    <ul className="mt-4 space-y-2">
      {data.map((brief: OpportunityBrief) => (
        <li key={brief.id} className="text-sm text-gray-800">
          {brief.summary}
        </li>
      ))}
    </ul>
  );
}
