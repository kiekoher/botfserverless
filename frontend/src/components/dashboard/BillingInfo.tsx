"use client";
import { useQuery } from '@tanstack/react-query';
import { getBillingInfo, BillingInfo as BillingInfoType } from '@/services/api';

export default function BillingInfo() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['billingInfo'],
    queryFn: getBillingInfo,
  });

  if (isLoading) {
    return <p>Cargando información de facturación...</p>;
  }

  if (isError) {
    return <p>Error al cargar facturación: {error.message}</p>;
  }

  if (!data) {
    return <p>No hay información de facturación disponible.</p>;
  }

  return (
    <div className="mt-4 text-sm text-gray-800">
      <p>Plan: {data.plan}</p>
      <p>Estado: {data.status}</p>
    </div>
  );
}
