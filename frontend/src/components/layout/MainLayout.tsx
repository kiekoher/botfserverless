import React from 'react';

const MainLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-800 text-white p-4">
        <h1 className="text-2xl font-bold">EVA</h1>
        <nav className="mt-8">
          <ul>
            <li className="mb-4">
              <a href="/dashboard" className="hover:text-gray-300">Dashboard</a>
            </li>
            <li className="mb-4">
              <a href="/dashboard/agents" className="hover:text-gray-300">Agents</a>
            </li>
            <li className="mb-4">
              <a href="/dashboard/settings" className="hover:text-gray-300">Settings</a>
            </li>
          </ul>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-8 flex flex-col">
        <header className="flex justify-end mb-4">
          <form action="/auth/signout" method="post">
            <button type="submit" className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600">
              Logout
            </button>
          </form>
        </header>
        <div className="flex-1">
          {children}
        </div>
      </main>
    </div>
  );
};

export default MainLayout;
