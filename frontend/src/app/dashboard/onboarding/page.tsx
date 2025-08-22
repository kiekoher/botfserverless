"use client";

import React, { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import QRCode from 'qrcode.react';
import Link from 'next/link';

// --- Types ---
interface OnboardingStatus {
  status: 'disconnected' | 'connected' | 'loading';
}

interface QrCodeResponse {
  qr_code: string;
}

// --- API Fetching Functions ---
const fetchQrCode = async (): Promise<QrCodeResponse | null> => {
  const res = await fetch('/api/v1/onboarding/whatsapp-qr');
  if (res.status === 204) {
    return null; // No QR code available yet
  }
  if (!res.ok) {
    throw new Error('Failed to fetch QR code');
  }
  return res.json();
};

const fetchOnboardingStatus = async (): Promise<OnboardingStatus> => {
  const res = await fetch('/api/v1/onboarding/status');
  if (!res.ok) {
    throw new Error('Failed to fetch onboarding status');
  }
  return res.json();
};

// --- Child Components ---
const StepButton = ({ step, currentStep, setStep, disabled }) => (
  <button
    onClick={() => setStep(step.id)}
    disabled={disabled}
    className={`text-left p-3 rounded-md transition-colors w-full ${
      currentStep === step.id
        ? 'bg-blue-600 text-white font-semibold shadow-md'
        : 'hover:bg-gray-100 text-gray-500'
    } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
  >
    <div className="font-bold text-sm">STEP {step.id}</div>
    <div className="text-sm">{step.name}</div>
  </button>
);

const StepContent = ({ step, children }) => (
  <div>
    <h2 className="text-2xl font-semibold text-gray-800">{step.name}</h2>
    <p className="text-gray-500 mb-6">{step.description}</p>
    <div className="p-6 bg-gray-50 rounded-lg min-h-[250px] flex flex-col items-center justify-center">
      {children}
    </div>
  </div>
);

// --- Main Onboarding Page ---
const OnboardingPage = () => {
  const queryClient = useQueryClient();
  const [currentStep, setCurrentStep] = useState(1);

  // Query for WhatsApp connection status
  const { data: statusData, error: statusError } = useQuery<OnboardingStatus>({
    queryKey: ['onboardingStatus'],
    queryFn: fetchOnboardingStatus,
    refetchInterval: data => (data?.status === 'connected' ? false : 2000), // Poll every 2s until connected
  });

  const isConnected = statusData?.status === 'connected';

  // Query for QR Code, only enabled if not connected
  const { data: qrData, isLoading: isQrLoading } = useQuery<QrCodeResponse | null>({
    queryKey: ['qrCode'],
    queryFn: fetchQrCode,
    refetchInterval: data => (data?.qr_code || isConnected ? false : 3000), // Poll every 3s if no QR code and not connected
    enabled: !isConnected,
  });

  // Mutation for activating the agent
  const activateMutation = useMutation({
    mutationFn: () => fetch('/api/v1/agent/activate', { method: 'POST' }),
    onSuccess: () => {
      alert('Agent activated successfully! You can now test it.');
      // In a real app, you'd likely redirect or update UI state
    },
    onError: () => {
      alert('Failed to activate agent. Please try again.');
    }
  });

  // --- Effects ---
  useEffect(() => {
    // Automatically advance to step 2 when connected
    if (isConnected) {
      setCurrentStep(2);
    }
  }, [isConnected]);

  // --- Steps Configuration ---
  const steps = [
    { id: 1, name: "Connect your Channel", description: "Scan the QR code with WhatsApp to connect your agent." },
    { id: 2, name: "Define Agent Personality", description: "Configure your agent&apos;s name, product, and core instructions." },
    { id: 3, name: "Provide Knowledge", description: "Upload documents to your agent&apos;s knowledge base." },
    { id: 4, name: "Activate and Test", description: "Activate your agent and start your first conversation." },
  ];

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <StepContent step={steps[0]}>
            {isQrLoading && <p className="text-gray-500">Requesting QR Code...</p>}
            {statusError && <p className="text-red-500">Error checking status. Please refresh.</p>}
            {qrData?.qr_code && !isConnected && (
              <div className="text-center">
                <QRCode value={qrData.qr_code} size={160} />
                <p className="mt-4 text-gray-600">Scan this with WhatsApp.</p>
              </div>
            )}
            {isConnected && (
              <div className="text-center text-green-600">
                <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                <p className="font-semibold mt-2">Channel Connected!</p>
              </div>
            )}
          </StepContent>
        );
      case 2:
        return (
          <StepContent step={steps[1]}>
            <p className="text-gray-700 mb-4 text-center">
              Navigate to the configuration page to set up your agent's personality.
            </p>
            <Link href="/dashboard/config" className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
                Go to Configuration
            </Link>
          </StepContent>
        );
      case 3:
        return (
          <StepContent step={steps[2]}>
            <p className="text-gray-700 mb-4 text-center">
              Upload documents that your agent will use to answer questions.
            </p>
            <Link href="/dashboard/knowledge" className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
                Go to Knowledge Base
            </Link>
          </StepContent>
        );
      case 4:
        return (
          <StepContent step={steps[3]}>
             <p className="text-gray-700 mb-4 text-center">
              Once you have configured your agent and added knowledge, you can activate it.
            </p>
            <button
              onClick={() => activateMutation.mutate()}
              disabled={activateMutation.isPending}
              className="px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:bg-gray-400"
            >
              {activateMutation.isPending ? 'Activating...' : 'Activate Agent'}
            </button>
          </StepContent>
        );
      default:
        return null;
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto bg-white rounded-2xl shadow-lg">
      <h1 className="text-3xl font-bold text-gray-800 mb-2">AI Sales Agent Setup</h1>
      <p className="text-gray-600 mb-8">Follow these steps to get your agent up and running.</p>

      <div className="flex gap-12">
        <div className="w-1/4">
          <nav className="flex flex-col space-y-2">
            {steps.map((step) => (
              <StepButton
                key={step.id}
                step={step}
                currentStep={currentStep}
                setStep={setCurrentStep}
                disabled={step.id > 1 && !isConnected}
              />
            ))}
          </nav>
        </div>

        <div className="w-3/4">
          {renderStepContent()}
        </div>
      </div>
    </div>
  );
};

export default OnboardingPage;
