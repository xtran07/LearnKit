import { useEffect, useState } from "react";
import { getResumeUrl, listResumes, suggestTopics, uploadResume } from "../api/client.js";

export default function ResumePage() {
  const [resumes, setResumes] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [suggesting, setSuggesting] = useState(null);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);

  const loadResumes = async () => {
    const res = await listResumes();
    setResumes(res.data);
  };

  useEffect(() => {
    loadResumes();
  }, []);

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setError(null);
    try {
      await uploadResume(file);
      await loadResumes();
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleView = async (resumeId) => {
    setError(null);
    try {
      const res = await getResumeUrl(resumeId);
      window.open(res.data.url, "_blank", "noopener,noreferrer");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not open resume");
    }
  };

  const handleDownload = async (resumeId) => {
    setError(null);
    try {
      const res = await getResumeUrl(resumeId, true);
      window.open(res.data.url, "_blank", "noopener,noreferrer");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not download resume");
    }
  };

  const handleSuggestTopics = async (resumeId) => {
    setSuggesting(resumeId);
    setError(null);
    setMessage(null);
    try {
      const res = await suggestTopics(resumeId);
      setMessage(`Added ${res.data.length} new topic(s) from this resume. Check the Topics tab.`);
    } catch (err) {
      setError(err.response?.data?.detail || "Topic suggestion failed");
    } finally {
      setSuggesting(null);
    }
  };

  return (
    <div className="space-y-6">
      <section className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-2">Upload Resume</h2>
        <p className="text-sm text-gray-500 mb-4">PDF, TXT, or Markdown files are supported.</p>
        <input
          type="file"
          accept=".pdf,.txt,.md"
          onChange={handleUpload}
          disabled={uploading}
          className="block text-sm"
        />
        {uploading && <p className="text-sm text-gray-500 mt-2">Uploading…</p>}
        {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
        {message && <p className="text-sm text-green-600 mt-2">{message}</p>}
      </section>

      <section className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Your Resumes</h2>
        {resumes.length === 0 && <p className="text-sm text-gray-500">No resumes uploaded yet.</p>}
        <ul className="divide-y">
          {resumes.map((resume) => (
            <li key={resume.id} className="py-3 flex items-center justify-between">
              <div>
                <p className="font-medium">{resume.filename}</p>
                <p className="text-xs text-gray-500">
                  Uploaded {new Date(resume.created_at).toLocaleString()}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleView(resume.id)}
                  className="px-3 py-1.5 text-sm rounded-md border text-gray-600 hover:bg-gray-50"
                >
                  View
                </button>
                <button
                  onClick={() => handleDownload(resume.id)}
                  className="px-3 py-1.5 text-sm rounded-md border text-gray-600 hover:bg-gray-50"
                >
                  Download
                </button>
                <button
                  onClick={() => handleSuggestTopics(resume.id)}
                  disabled={suggesting === resume.id}
                  className="px-3 py-1.5 text-sm rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {suggesting === resume.id ? "Generating…" : "Suggest Topics"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
