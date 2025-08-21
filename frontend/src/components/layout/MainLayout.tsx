import React from 'react';
import Link from 'next/link';

const MainLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Barra lateral */}
      <aside className="w-64 bg-gray-800 text-white p-4">
        <h1 className="text-2xl font-bold">EVA</h1>
        <nav className="mt-8">
          <ul>
            <li className="mb-4">
              <Link href="/dashboard" className="hover:text-gray-300">Panel de Control</Link>
            </li>
            <li className="mb-4">
              <Link href="/dashboard/agents" className="hover:text-gray-300">Agentes</Link>
            </li>
            <li className="mb-4">
              <Link href="/dashboard/settings" className="hover:text-gray-300">Configuración</Link>
            </li>
          </ul>
        </nav>
      </aside>

      {/* Contenido principal */}
      <main className="flex-1 p-8 flex flex-col">
        <header className="flex justify-end mb-4">
          <form action="/auth/signout" method="post">
            <button type="submit" className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600">
              Cerrar Sesión
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
