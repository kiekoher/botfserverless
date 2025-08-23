import QualityMetrics from '@/components/dashboard/QualityMetrics';

export default function QualityPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold text-gray-900">Quality Assurance</h1>
      <QualityMetrics />
    </div>
  );
}
