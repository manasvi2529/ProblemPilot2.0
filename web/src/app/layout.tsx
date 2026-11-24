import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/lib/auth-context';
import { PreferencesProvider } from '@/lib/preferences-context';
import { Sidebar } from '@/components/Sidebar';
import { AuthModal } from '@/components/AuthModal';

export const metadata: Metadata = {
  title: 'ProblemPilot AI — Problem Discovery & Codebase Generation',
  description:
    'Autonomous, live-research real-world problem discovery and project-building intelligence platform.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#090d16] text-slate-100 font-sans">
        <PreferencesProvider>
          <AuthProvider>
            <Sidebar />
            <div className="md:ml-64 flex flex-col min-h-screen">
              <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {children}
              </main>
            </div>
            <AuthModal />
          </AuthProvider>
        </PreferencesProvider>
      </body>
    </html>
  );
}
