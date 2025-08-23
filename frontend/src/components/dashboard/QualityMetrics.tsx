"use client";
import { useQuery } from '@tanstack/react-query';
import { getQualityMetrics, QualityMetric } from '@/services/api';

export default function QualityMetrics() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['qualityMetrics'],
    queryFn: getQualityMetrics,
  });

  if (isLoading) {
    return <p>Cargando métricas...</p>;
  }

  if (isError) {
    return <p>Error al cargar métricas: {error.message}</p>;
  }

  return (
    <ul className="mt-4 space-y-2">
      {data?.map((m: QualityMetric) => (
        <li key={m.id} className="text-sm text-gray-800">
          {m.name}: {m.value}
        </li>
      ))}
    </ul>
  );
}
