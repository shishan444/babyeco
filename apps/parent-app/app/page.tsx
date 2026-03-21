export default function HomePage() {
  return (
    <main className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-parent-primary mb-4">
          Welcome to BabyEco
        </h1>
        <p className="text-gray-600 mb-8">
          Parent Application
        </p>
        <div className="flex gap-4 justify-center">
          <button className="px-6 py-3 bg-parent-primary text-white rounded-lg hover:bg-opacity-90">
            Create My Family
          </button>
          <button className="px-6 py-3 border border-parent-primary text-parent-primary rounded-lg hover:bg-opacity-10">
            Join Existing
          </button>
        </div>
      </div>
    </main>
  );
}
