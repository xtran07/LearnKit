import { useAuth } from "../AuthContext.jsx";
import { MODEL_OPTIONS, modelLabel, useModel } from "../ModelContext.jsx";

export default function ProfilePage() {
  const { user } = useAuth();
  const { provider, setProvider } = useModel();

  return (
    <div className="space-y-6">
      <section className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Profile</h2>
        <p className="text-sm text-gray-500">Signed in as</p>
        <p className="font-medium">{user?.email}</p>
      </section>

      <section className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-2">AI Model</h2>
        <p className="text-sm text-gray-500 mb-4">
          Choose which model is used by default for question generation, grading, and topic
          suggestions. If one provider is unavailable (e.g. rate limited), switch to the other.
        </p>

        <p className="text-sm text-gray-500 mb-1">Current active model</p>
        <p className="font-medium mb-4">{modelLabel(provider)}</p>

        <label className="block text-xs text-gray-500 mb-1">Switch model</label>
        <select
          value={provider}
          onChange={(e) => setProvider(e.target.value)}
          className="border rounded-md px-3 py-2 text-sm"
        >
          {MODEL_OPTIONS.map((m) => (
            <option key={m.value} value={m.value}>
              {m.label}
            </option>
          ))}
        </select>
      </section>
    </div>
  );
}
