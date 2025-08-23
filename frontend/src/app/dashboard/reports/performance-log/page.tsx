import PerformanceLogList from '@/components/dashboard/PerformanceLogList';

export default function PerformanceLogPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold text-gray-900">Agent Performance Log</h1>
      <PerformanceLogList />
    </div>
  );
}
