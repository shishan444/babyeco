"use client";

import { useAuthStore } from "@/stores/authStore";
import { Button } from "@/components/ui/Button";

export default function DashboardPage() {
  const { user, family, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
  };

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Dashboard
            </h1>
            <p className="text-gray-600">
              Welcome back, {user?.name}!
            </p>
          </div>
          <Button variant="ghost" onClick={handleLogout}>
            Logout
          </Button>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-2">Family Information</h2>
          <p className="text-gray-600">
            Family: {family?.name}
          </p>
          <p className="text-sm text-gray-500">
            Email: {user?.email}
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 gap-4">
            <button className="p-4 border rounded-lg hover:bg-gray-50 text-left">
              <div className="font-medium">Manage Children</div>
              <div className="text-sm text-gray-500">Add or edit child profiles</div>
            </button>
            <button className="p-4 border rounded-lg hover:bg-gray-50 text-left">
              <div className="font-medium">Create Tasks</div>
              <div className="text-sm text-gray-500">Set up tasks and rewards</div>
            </button>
            <button className="p-4 border rounded-lg hover:bg-gray-50 text-left">
              <div className="font-medium">View Reports</div>
              <div className="text-sm text-gray-500">Progress and analytics</div>
            </button>
            <button className="p-4 border rounded-lg hover:bg-gray-50 text-left">
              <div className="font-medium">Settings</div>
              <div className="text-sm text-gray-500">Account preferences</div>
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
