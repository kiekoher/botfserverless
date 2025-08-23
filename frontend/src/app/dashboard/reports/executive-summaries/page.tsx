import ExecutiveSummaryList from '@/components/dashboard/ExecutiveSummaryList';

export default function ExecutiveSummariesPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold text-gray-900">Executive Summaries</h1>
      <ExecutiveSummaryList />
    </div>
  );
}
