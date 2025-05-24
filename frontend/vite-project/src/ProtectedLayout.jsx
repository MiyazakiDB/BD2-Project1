// ProtectedLayout.jsx
import NavigationBar from './NavigationBar';
import { Outlet } from 'react-router-dom';

export default function ProtectedLayout() {
  return (
    <div className="flex">
      <NavigationBar />
      <main className="ml-64 w-full min-h-screen bg-gray-100 p-4">
        <Outlet />
      </main>
    </div>
  );
}
