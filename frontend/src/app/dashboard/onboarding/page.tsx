"use client";

import React, { useState } from 'react';

// Define the steps based on AGENT.md
const steps = [
  {
    id: 1,
    name: "Connect your Channel",
    description: "Scan the QR code with WhatsApp to connect your agent.",
    details: "To get started, link your WhatsApp account. Your agent will operate through this number. This is the most critical step – without a channel, your agent can't talk to customers!",
  },
  {
    id: 2,
    name: "Define Agent Personality",
    description: "Configure your agent's name, product, and core instructions.",
    details: "Head to the /config page to give your agent a name, describe the product or service it will be selling, and provide a detailed system prompt defining its tone, style, and objectives.",
  },
  {
    id: 3,
    name: "Provide Knowledge",
    description: "Upload documents to your agent's knowledge base.",
    details: "Go to the /knowledge page to upload PDFs, TXT files, or other documents. Your agent will use this information to answer customer questions accurately. We recommend uploading at least one document.",
  },
  {
    id: 4,
    name: "Activate and Test",
    description: "Activate your agent and start your first conversation.",
    details: "Once the first three steps are complete, you can activate your agent. After activation, send a message to your connected WhatsApp number to test it out!",
  },
];

const OnboardingPage = () => {
  const [currentStep, setCurrentStep] = useState(1);

  return (
    <div className="p-8 max-w-4xl mx-auto bg-white rounded-lg shadow-md">
      <h1 className="text-3xl font-bold text-gray-800 mb-2">Welcome to Your AI Sales Agent Setup</h1>
      <p className="text-gray-600 mb-8">Follow these steps to get your agent up and running.</p>

      <div className="flex">
        {/* Step indicators */}
        <div className="w-1/4 pr-8">
          <nav className="flex flex-col">
            {steps.map((step) => (
              <button
                key={step.id}
                onClick={() => setCurrentStep(step.id)}
                className={`text-left p-3 rounded-md transition-colors ${
                  currentStep === step.id
                    ? 'bg-blue-500 text-white font-semibold'
                    : 'hover:bg-gray-100 text-gray-500'
                }`}
              >
                <div className="font-bold text-sm">STEP {step.id}</div>
                <div className="text-sm">{step.name}</div>
              </button>
            ))}
          </nav>
        </div>

        {/* Step content */}
        <div className="w-3/4 pl-8 border-l border-gray-200">
          <div className="mb-4">
            <h2 className="text-2xl font-semibold text-gray-800">{steps[currentStep - 1].name}</h2>
            <p className="text-gray-500">{steps[currentStep - 1].description}</p>
          </div>

          <div className="p-6 bg-gray-50 rounded-lg min-h-[200px]">
            <p className="text-gray-700 mb-4">{steps[currentStep - 1].details}</p>

            {/* Mock UI for each step */}
            {currentStep === 1 && (
              <div className="flex flex-col items-center justify-center p-4 bg-gray-100 rounded-md">
                <div className="w-32 h-32 bg-gray-300 flex items-center justify-center">
                  <p className="text-gray-500 text-sm">[QR Code Placeholder]</p>
                </div>
                <button className="mt-4 px-4 py-2 bg-gray-300 text-gray-600 rounded-md cursor-not-allowed">
                  Verify Connection
                </button>
              </div>
            )}
            {currentStep === 2 && (
              <div className="flex items-center justify-center">
                <button className="px-6 py-3 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors">
                  Go to Configuration
                </button>
              </div>
            )}
            {currentStep === 3 && (
              <div className="flex items-center justify-center">
                <button className="px-6 py-3 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors">
                  Go to Knowledge Base
                </button>
              </div>
            )}
            {currentStep === 4 && (
              <div className="flex items-center justify-center">
                <button className="px-6 py-3 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors">
                  Activate Agent
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnboardingPage;
