import { useEffect, useState } from "react";
import { createTopic, deleteTopic, getProgress, listTopics, updateTopic } from "../api/client.js";
import { PageLoader } from "../components/Spinner.jsx";

const statusStyles = {
  active: "bg-green-100 text-green-700",
  excluded: "bg-gray-200 text-gray-600",
  mastered: "bg-blue-100 text-blue-700",
};

export default function TopicsPage() {
  const [topics, setTopics] = useState([]);
  const [scores, setScores] = useState({});
  const [pageLoading, setPageLoading] = useState(true);
  const [newTopic, setNewTopic] = useState("");
  const [error, setError] = useState(null);

  const loadTopics = async () => {
    const tRes = await listTopics();
    setTopics(tRes.data);
    getProgress()
      .then((pRes) => {
        const scoreMap = {};
        for (const p of pRes.data) scoreMap[p.topic_id] = p;
        setScores(scoreMap);
      })
      .catch(() => {});
  };

  useEffect(() => {
    loadTopics().finally(() => setPageLoading(false));
  }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newTopic.trim()) return;
    try {
      await createTopic(newTopic.trim());
      setNewTopic("");
      await loadTopics();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not add topic");
    }
  };

  const cycleStatus = async (topic) => {
    const next = { active: "excluded", excluded: "mastered", mastered: "active" }[topic.status];
    await updateTopic(topic.id, { status: next });
    await loadTopics();
  };

  const handleDelete = async (id) => {
    await deleteTopic(id);
    await loadTopics();
  };

  return (
    <div className="space-y-6">
      <section className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Add a Topic</h2>
        <form onSubmit={handleAdd} className="flex gap-2">
          <input
            type="text"
            value={newTopic}
            onChange={(e) => setNewTopic(e.target.value)}
            placeholder="e.g. System Design"
            className="flex-1 border rounded-md px-3 py-2 text-sm"
          />
          <button type="submit" className="px-4 py-2 text-sm rounded-md bg-indigo-600 text-white hover:bg-indigo-700">
            Add
          </button>
        </form>
        {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
      </section>

      <section className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">All Topics</h2>
        <p className="text-xs text-gray-500 mb-3">
          Click a status badge to cycle: active → excluded → mastered → active.
        </p>
        {pageLoading && <PageLoader message="Loading topics…" />}
        {!pageLoading && topics.length === 0 && <p className="text-sm text-gray-500">No topics yet. Add one above or upload a resume.</p>}
        {!pageLoading && <ul className="divide-y">
          {topics.map((topic) => (
            <li key={topic.id} className="py-3 flex items-center justify-between gap-3">
              <div>
                <p className="font-medium">{topic.name}</p>
                <p className="text-xs text-gray-500">source: {topic.source}</p>
              </div>
              <div className="flex items-center gap-2">
                {scores[topic.id]?.average_score != null && (
                  <span
                    className={`text-xs font-semibold px-2 py-1 rounded-full ${
                      scores[topic.id].average_score >= 80
                        ? "bg-green-100 text-green-700"
                        : scores[topic.id].average_score >= 50
                        ? "bg-yellow-100 text-yellow-700"
                        : "bg-red-100 text-red-600"
                    }`}
                  >
                    {Math.round(scores[topic.id].average_score)}/100
                  </span>
                )}
                <button
                  onClick={() => cycleStatus(topic)}
                  className={`px-2 py-1 text-xs rounded-full ${statusStyles[topic.status]}`}
                >
                  {topic.status}
                </button>
                <button
                  onClick={() => handleDelete(topic.id)}
                  className="px-2 py-1 text-xs rounded-md text-red-600 hover:bg-red-50"
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>}
      </section>
    </div>
  );
}
