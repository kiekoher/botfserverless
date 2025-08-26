"use client";

import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';

// Define the structure of a DLQ message
interface DlqMessage {
  message_id: string;
  data: Record<string, any>;
}

export default function DlqManagementPage() {
  const [messages, setMessages] = useState<DlqMessage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMessages = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/admin/dlq');
      if (!response.ok) {
        throw new Error('Failed to fetch DLQ messages');
      }
      const data = await response.json();
      setMessages(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      setError(errorMessage);
      toast.error('Failed to load DLQ messages.', { description: errorMessage });
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMessages();
  }, [fetchMessages]);

  const handleReprocess = async (message: DlqMessage) => {
    try {
      const response = await fetch('/api/v1/admin/dlq/reprocess', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(message),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to reprocess message');
      }
      toast.success('Message sent for reprocessing.');
      fetchMessages(); // Refresh the list
    } catch (err) {
       const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      toast.error('Reprocessing failed.', { description: errorMessage });
    }
  };

  const handleDelete = async (message: DlqMessage) => {
    try {
      const response = await fetch('/api/v1/admin/dlq/item', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(message),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete message');
      }
      toast.success('Message deleted from DLQ.');
      fetchMessages(); // Refresh the list
    } catch (err) {
       const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      toast.error('Delete failed.', { description: errorMessage });
    }
  };

  if (isLoading) {
    return <div>Loading DLQ messages...</div>;
  }

  if (error) {
    return <div className="text-red-500">Error: {error}</div>;
  }

  return (
    <div className="p-4 md:p-6">
      <h1 className="text-2xl font-semibold mb-4">Dead Letter Queue Management</h1>
      <p className="mb-6 text-gray-600">
        These messages failed processing and have been moved to the DLQ. You can reprocess them or delete them.
      </p>
      {messages.length === 0 ? (
        <p>The Dead Letter Queue is empty.</p>
      ) : (
        <div className="space-y-4">
          {messages.map((msg, index) => (
            <div key={index} className="bg-white p-4 rounded-lg shadow border">
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-mono text-sm text-gray-500">ID: {msg.message_id}</p>
                  <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-auto">
                    {JSON.stringify(msg.data, null, 2)}
                  </pre>
                </div>
                <div className="flex space-x-2 ml-4">
                  <button
                    onClick={() => handleReprocess(msg)}
                    className="px-3 py-1 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700"
                  >
                    Reprocess
                  </button>
                  <button
                    onClick={() => handleDelete(msg)}
                    className="px-3 py-1 text-sm font-medium text-white bg-red-600 rounded hover:bg-red-700"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
