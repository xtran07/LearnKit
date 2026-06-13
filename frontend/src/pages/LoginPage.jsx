import { useAuth } from "../AuthContext.jsx";

export default function LoginPage() {
  const { signInWithGoogle } = useAuth();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-lg shadow p-8 text-center space-y-4 max-w-sm">
        <h1 className="text-xl font-semibold">Interview Prep Tracker</h1>
        <p className="text-sm text-gray-500">Sign in to track your resume, topics, and progress.</p>
        <button
          onClick={signInWithGoogle}
          className="w-full px-4 py-2 rounded-md bg-indigo-600 text-white hover:bg-indigo-700 text-sm font-medium"
        >
          Sign in with Google
        </button>
      </div>
    </div>
  );
}
