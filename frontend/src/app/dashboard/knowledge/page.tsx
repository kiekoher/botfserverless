"use client";

import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useDropzone } from 'react-dropzone';
import { getDocuments, uploadDocument, Document } from '@/services/api';

// Status Badge Component
const StatusBadge: React.FC<{ status: 'pending' | 'processing' | 'completed' | 'failed' }> = ({ status }) => {
  const baseClasses = "px-2 py-1 text-xs font-semibold rounded-full";
  const statusMap = {
    pending: { text: 'Pending', classes: 'bg-yellow-100 text-yellow-800' },
    processing: { text: 'Processing', classes: 'bg-blue-100 text-blue-800 animate-pulse' },
    completed: { text: 'Completed', classes: 'bg-green-100 text-green-800' },
    failed: { text: 'Failed', classes: 'bg-red-100 text-red-800' },
  };
  const { text, classes } = statusMap[status] || { text: 'Unknown', classes: 'bg-gray-100 text-gray-800' };
  return <span className={`${baseClasses} ${classes}`}>{text}</span>;
};

// Main Page Component
export default function KnowledgePage() {
  const queryClient = useQueryClient();
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Query to fetch documents
  const { data: documents, isLoading, error } = useQuery<Document[]>({
    queryKey: ['documents'],
    queryFn: getDocuments,
  });

  // Mutation for uploading a document
  const { mutate: uploadFile, isPending: isUploading } = useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => {
      setNotification({ message: 'File uploaded successfully! It is now being processed.', type: 'success' });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setTimeout(() => setNotification(null), 4000);
    },
    onError: (error: Error) => {
      setNotification({ message: `Upload failed: ${error.message}`, type: 'error' });
      setTimeout(() => setNotification(null), 4000);
    },
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      uploadFile(acceptedFiles[0]);
    }
  }, [uploadFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'text/plain': ['.txt'], 'text/markdown': ['.md'] },
    maxFiles: 1,
  });

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Knowledge Base</h1>
      <p className="text-gray-600 mb-8">
        Upload documents (PDFs, TXT, Markdown) to provide your agent with the information it needs to answer customer questions.
      </p>

      {/* Upload Component */}
      <div
        {...getRootProps()}
        className={`p-10 border-2 border-dashed rounded-lg text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}`}
      >
        <input {...getInputProps()} />
        {isUploading ? (
          <p>Uploading...</p>
        ) : isDragActive ? (
          <p className="text-blue-600">Drop the file here ...</p>
        ) : (
          <p>Drag &apos;n&apos; drop a file here, or click to select a file</p>
        )}
         <p className="text-sm text-gray-500 mt-2">Supported formats: PDF, TXT, MD</p>
      </div>

      {notification && (
        <div className={`mt-4 p-3 rounded-lg text-center ${notification.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
          {notification.message}
        </div>
      )}

      {/* Documents List */}
      <div className="mt-12">
        <h2 className="text-2xl font-bold text-gray-700 mb-4">Uploaded Documents</h2>
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {isLoading ? (
            <p className="p-4">Loading documents...</p>
          ) : error ? (
            <p className="p-4 text-red-500">Error loading documents: {(error as Error).message}</p>
          ) : documents && documents.length > 0 ? (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">File Name</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Uploaded At</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {documents.map((doc) => (
                  <tr key={doc.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{doc.file_name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"><StatusBadge status={doc.status} /></td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(doc.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="p-4 text-center text-gray-500">No documents have been uploaded yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
