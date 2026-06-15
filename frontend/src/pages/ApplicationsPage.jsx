import { useEffect, useState } from "react";
import {
  createApplication,
  deleteApplication,
  deleteAppQuestion,
  generateAppQuestions,
  listApplications,
  listAppQuestions,
  resolveApplicationLink,
  updateApplication,
} from "../api/client.js";

const statusStyles = {
  new: "bg-gray-100 text-gray-700",
  applied: "bg-blue-100 text-blue-700",
  in_progress: "bg-yellow-100 text-yellow-700",
  waiting: "bg-purple-100 text-purple-700",
  rejected: "bg-red-100 text-red-700",
  offered: "bg-green-100 text-green-700",
};

const statusOptions = ["new", "applied", "in_progress", "waiting", "rejected", "offered"];

const emptyForm = {
  name: "",
  company: "",
  role: "",
  status: "new",
  source: "",
  job_post_link: "",
  job_portal_link: "",
  poc: "",
  notes: "",
  practice_interview_done: false,
};

export default function ApplicationsPage() {
  const [applications, setApplications] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [resolveUrl, setResolveUrl] = useState("");
  const [resolving, setResolving] = useState(false);
  const [error, setError] = useState(null);

  const [expandedId, setExpandedId] = useState(null);
  const [appQuestions, setAppQuestions] = useState({});
  const [genDifficulty, setGenDifficulty] = useState("medium");
  const [genCount, setGenCount] = useState(5);
  const [genProvider, setGenProvider] = useState("gemini");
  const [generating, setGenerating] = useState(false);
  const [copiedQuestionId, setCopiedQuestionId] = useState(null);

  const loadApplications = async () => {
    const res = await listApplications();
    setApplications(res.data);
  };

  useEffect(() => {
    loadApplications();
  }, []);

  const handleResolve = async () => {
    if (!resolveUrl.trim()) return;
    setResolving(true);
    setError(null);
    try {
      const res = await resolveApplicationLink(resolveUrl.trim());
      const { name, company, role, source } = res.data;
      setForm((prev) => ({
        ...prev,
        name: name || prev.name,
        company: company || prev.company,
        role: role || prev.role,
        source: source || prev.source,
        job_post_link: resolveUrl.trim(),
      }));
    } catch (err) {
      setError(err.response?.data?.detail || "Could not resolve job posting");
    } finally {
      setResolving(false);
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!form.name.trim() || !form.company.trim() || !form.role.trim()) return;
    try {
      await createApplication(form);
      setForm(emptyForm);
      setResolveUrl("");
      await loadApplications();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not add application");
    }
  };

  const handleStatusChange = async (app, status) => {
    await updateApplication(app.id, { status });
    await loadApplications();
  };

  const handleTogglePractice = async (app) => {
    await updateApplication(app.id, { practice_interview_done: !app.practice_interview_done });
    await loadApplications();
  };

  const handleDelete = async (id) => {
    await deleteApplication(id);
    if (expandedId === id) setExpandedId(null);
    await loadApplications();
  };

  const loadAppQuestions = async (id) => {
    const res = await listAppQuestions(id);
    setAppQuestions((prev) => ({ ...prev, [id]: res.data }));
  };

  const toggleExpand = async (id) => {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(id);
    if (!appQuestions[id]) {
      await loadAppQuestions(id);
    }
  };

  const handleGenerateQuestions = async (id) => {
    setGenerating(true);
    setError(null);
    try {
      await generateAppQuestions(id, { count: Number(genCount), difficulty: genDifficulty, provider: genProvider });
      await loadAppQuestions(id);
    } catch (err) {
      setError(err.response?.data?.detail || "Question generation failed");
    } finally {
      setGenerating(false);
    }
  };

  const handleDeleteQuestion = async (appId, questionId) => {
    await deleteAppQuestion(questionId);
    await loadAppQuestions(appId);
  };

  const handleCopyQuestion = async (q) => {
    await navigator.clipboard.writeText(q.question_text);
    setCopiedQuestionId(q.id);
    setTimeout(() => setCopiedQuestionId(null), 1500);
  };

  const handleOpenInClaude = (q) => {
    const prompt = `Can you help me understand and learn this interview question?\n\n${q.question_text}`;
    window.open(`https://claude.ai/new?q=${encodeURIComponent(prompt)}`, "_blank", "noopener,noreferrer");
  };

  return (
    <div className="space-y-6">
      <section className="bg-white rounded-lg shadow p-6 space-y-4">
        <h2 className="text-lg font-semibold">Add Job Application</h2>

        <div className="flex gap-2">
          <input
            type="text"
            value={resolveUrl}
            onChange={(e) => setResolveUrl(e.target.value)}
            placeholder="Paste a job post link to auto-fill details"
            className="flex-1 border rounded-md px-3 py-2 text-sm"
          />
          <button
            onClick={handleResolve}
            disabled={resolving || !resolveUrl.trim()}
            className="px-4 py-2 text-sm rounded-md border border-indigo-600 text-indigo-600 hover:bg-indigo-50 disabled:opacity-50"
          >
            {resolving ? "Resolving…" : "Resolve from link"}
          </button>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <form onSubmit={handleAdd} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Name / shortname</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
              className="w-full border rounded-md px-3 py-2 text-sm"
              required
            />
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">Company</label>
            <input
              type="text"
              value={form.company}
              onChange={(e) => setForm((prev) => ({ ...prev, company: e.target.value }))}
              className="w-full border rounded-md px-3 py-2 text-sm"
              required
            />
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">Post / Role</label>
            <input
              type="text"
              value={form.role}
              onChange={(e) => setForm((prev) => ({ ...prev, role: e.target.value }))}
              className="w-full border rounded-md px-3 py-2 text-sm"
              required
            />
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">Status</label>
            <select
              value={form.status}
              onChange={(e) => setForm((prev) => ({ ...prev, status: e.target.value }))}
              className="w-full border rounded-md px-3 py-2 text-sm"
            >
              {statusOptions.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">Source</label>
            <input
              type="text"
              value={form.source}
              onChange={(e) => setForm((prev) => ({ ...prev, source: e.target.value }))}
              placeholder="e.g. LinkedIn, Referral"
              className="w-full border rounded-md px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">Point of Contact</label>
            <input
              type="text"
              value={form.poc}
              onChange={(e) => setForm((prev) => ({ ...prev, poc: e.target.value }))}
              className="w-full border rounded-md px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">Job post link</label>
            <input
              type="text"
              value={form.job_post_link}
              onChange={(e) => setForm((prev) => ({ ...prev, job_post_link: e.target.value }))}
              className="w-full border rounded-md px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">Job portal link</label>
            <input
              type="text"
              value={form.job_portal_link}
              onChange={(e) => setForm((prev) => ({ ...prev, job_portal_link: e.target.value }))}
              className="w-full border rounded-md px-3 py-2 text-sm"
            />
          </div>

          <div className="sm:col-span-2">
            <label className="block text-xs text-gray-500 mb-1">Notes</label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm((prev) => ({ ...prev, notes: e.target.value }))}
              className="w-full border rounded-md p-2 text-sm h-20"
            />
          </div>

          <div className="sm:col-span-2 flex items-center gap-2">
            <input
              type="checkbox"
              id="practice_interview_done"
              checked={form.practice_interview_done}
              onChange={(e) => setForm((prev) => ({ ...prev, practice_interview_done: e.target.checked }))}
            />
            <label htmlFor="practice_interview_done" className="text-sm text-gray-600">
              Practice interview done
            </label>
          </div>

          <div className="sm:col-span-2">
            <button type="submit" className="px-4 py-2 text-sm rounded-md bg-indigo-600 text-white hover:bg-indigo-700">
              Add Application
            </button>
          </div>
        </form>
      </section>

      <section className="space-y-4">
        {applications.length === 0 && (
          <p className="text-sm text-gray-500">No applications yet. Add one above.</p>
        )}

        {applications.map((app) => (
          <div key={app.id} className="bg-white rounded-lg shadow p-6 space-y-3">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="font-medium">{app.name}</p>
                <p className="text-sm text-gray-600">
                  {app.role} · {app.company}
                </p>
              </div>
              <select
                value={app.status}
                onChange={(e) => handleStatusChange(app, e.target.value)}
                className={`text-xs px-2 py-1 rounded-full border-0 ${statusStyles[app.status]}`}
              >
                {statusOptions.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-wrap gap-3 text-xs text-gray-500">
              {app.source && <span>Source: {app.source}</span>}
              {app.poc && <span>POC: {app.poc}</span>}
              {app.job_post_link && (
                <a href={app.job_post_link} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">
                  Job post
                </a>
              )}
              {app.job_portal_link && (
                <a href={app.job_portal_link} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">
                  Portal
                </a>
              )}
            </div>

            {app.notes && (
              <details className="text-sm text-gray-500">
                <summary className="cursor-pointer">Notes</summary>
                <p className="mt-1 whitespace-pre-wrap">{app.notes}</p>
              </details>
            )}

            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={app.practice_interview_done}
                  onChange={() => handleTogglePractice(app)}
                />
                Practice interview done
              </label>

              <button
                onClick={() => toggleExpand(app.id)}
                className="px-3 py-1 text-xs rounded-md border border-indigo-600 text-indigo-600 hover:bg-indigo-50"
              >
                {expandedId === app.id ? "Hide mock interview" : "Mock interview"}
              </button>

              <button
                onClick={() => handleDelete(app.id)}
                className="px-3 py-1 text-xs rounded-md text-red-600 hover:bg-red-50 ml-auto"
              >
                Delete
              </button>
            </div>

            {expandedId === app.id && (
              <div className="border-t pt-3 space-y-3">
                <div className="flex flex-wrap gap-3 items-end">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Provider</label>
                    <select value={genProvider} onChange={(e) => setGenProvider(e.target.value)} className="border rounded-md px-3 py-2 text-sm">
                      <option value="gemini">Gemini</option>
                      <option value="groq">Groq</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Difficulty</label>
                    <select value={genDifficulty} onChange={(e) => setGenDifficulty(e.target.value)} className="border rounded-md px-3 py-2 text-sm">
                      <option value="easy">Easy</option>
                      <option value="medium">Medium</option>
                      <option value="hard">Hard</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Count</label>
                    <input
                      type="number"
                      min={1}
                      max={10}
                      value={genCount}
                      onChange={(e) => setGenCount(e.target.value)}
                      className="border rounded-md px-3 py-2 text-sm w-20"
                    />
                  </div>

                  <button
                    onClick={() => handleGenerateQuestions(app.id)}
                    disabled={generating}
                    className="px-4 py-2 text-sm rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
                  >
                    {generating ? "Generating…" : "Generate Questions"}
                  </button>
                </div>

                {(appQuestions[app.id] || []).length === 0 && (
                  <p className="text-sm text-gray-500">No mock interview questions yet. Generate some above.</p>
                )}

                {(appQuestions[app.id] || []).map((q) => (
                  <div key={q.id} className="bg-gray-50 border rounded-md p-3 space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-medium">{q.question_text}</p>
                      <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-600 whitespace-nowrap">
                        {q.difficulty} · {q.source}
                      </span>
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() => handleCopyQuestion(q)}
                        className="px-3 py-1 text-xs rounded-md border text-gray-600 hover:bg-gray-50"
                      >
                        {copiedQuestionId === q.id ? "Copied!" : "Copy question"}
                      </button>
                      <button
                        onClick={() => handleOpenInClaude(q)}
                        className="px-3 py-1 text-xs rounded-md border border-indigo-600 text-indigo-600 hover:bg-indigo-50"
                      >
                        Open in Claude
                      </button>
                      <button
                        onClick={() => handleDeleteQuestion(app.id, q.id)}
                        className="px-3 py-1 text-xs rounded-md text-red-600 hover:bg-red-50 ml-auto"
                      >
                        Delete
                      </button>
                    </div>

                    {q.ideal_answer && (
                      <details className="text-sm text-gray-500">
                        <summary className="cursor-pointer">Show ideal answer</summary>
                        <p className="mt-1">{q.ideal_answer}</p>
                      </details>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </section>
    </div>
  );
}
