"use client";
import { useQuery } from '@tanstack/react-query';
import { getExecutiveSummaries, ExecutiveSummary } from '@/services/api';

export default function ExecutiveSummaryList() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['executiveSummaries'],
    queryFn: getExecutiveSummaries,
  });

  if (isLoading) {
    return <p>Cargando informes...</p>;
  }

  if (isError) {
    return <p>Error al cargar informes: {error.message}</p>;
  }

  if (!data || data.length === 0) {
    return <p>No hay informes disponibles.</p>;
  }

  return (
    <ul className="mt-4 space-y-2">
      {data.map((summary: ExecutiveSummary) => (
        <li key={summary.id} className="text-sm text-gray-800">
          {summary.title} - {new Date(summary.created_at).toLocaleDateString()}
        </li>
      ))}
    </ul>
  );
}
