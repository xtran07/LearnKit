import { useEffect, useState } from "react";
import { getProgress } from "../api/client.js";

const statusStyles = {
  active: "bg-green-100 text-green-700",
  excluded: "bg-gray-200 text-gray-600",
  mastered: "bg-blue-100 text-blue-700",
};

export default function ProgressPage() {
  const [progress, setProgress] = useState([]);

  useEffect(() => {
    getProgress().then((res) => setProgress(res.data));
  }, []);

  return (
    <section className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold mb-4">Progress by Topic</h2>
      {progress.length === 0 && <p className="text-sm text-gray-500">No topics yet.</p>}
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-gray-500 border-b">
            <th className="py-2">Topic</th>
            <th className="py-2">Status</th>
            <th className="py-2">Questions</th>
            <th className="py-2">Attempted</th>
            <th className="py-2">Avg Score</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {progress.map((p) => (
            <tr key={p.topic_id}>
              <td className="py-2 font-medium">{p.topic_name}</td>
              <td className="py-2">
                <span className={`px-2 py-1 rounded-full text-xs ${statusStyles[p.status]}`}>{p.status}</span>
              </td>
              <td className="py-2">{p.total_questions}</td>
              <td className="py-2">{p.attempted_questions}</td>
              <td className="py-2">{p.average_score !== null ? p.average_score.toFixed(1) : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
