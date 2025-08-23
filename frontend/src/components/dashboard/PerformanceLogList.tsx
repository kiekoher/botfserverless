"use client";
import { useQuery } from '@tanstack/react-query';
import { getPerformanceLog, PerformanceLogEntry } from '@/services/api';

export default function PerformanceLogList() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['performanceLog'],
    queryFn: getPerformanceLog,
  });

  if (isLoading) {
    return <p>Cargando registros...</p>;
  }

  if (isError) {
    return <p>Error al cargar registros: {error.message}</p>;
  }

  if (!data || data.length === 0) {
    return <p>No hay registros de rendimiento.</p>;
  }

  return (
    <ul className="mt-4 space-y-2">
      {data.map((entry: PerformanceLogEntry) => (
        <li key={entry.id} className="text-sm text-gray-800">
          {entry.event} - {new Date(entry.created_at).toLocaleString()}
        </li>
      ))}
    </ul>
  );
}
