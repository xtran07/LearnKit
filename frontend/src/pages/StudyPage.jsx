import { useEffect, useState } from "react";
import {
  createQuestionManual,
  deleteQuestion,
  generateQuestions,
  getExternalPrompt,
  listQuestions,
  listTopicAttempts,
  listTopics,
  submitAttempt,
  updateTopic,
} from "../api/client.js";
import { MODEL_OPTIONS, useModel } from "../ModelContext.jsx";

export default function StudyPage() {
  const { provider: defaultProvider } = useModel();
  const [topics, setTopics] = useState([]);
  const [topicId, setTopicId] = useState("");
  const [questions, setQuestions] = useState([]);
  const [provider, setProvider] = useState(defaultProvider);
  const [difficulty, setDifficulty] = useState("medium");
  const [count, setCount] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [externalPrompt, setExternalPrompt] = useState(null);
  const [answers, setAnswers] = useState({});
  const [results, setResults] = useState({});
  const [grading, setGrading] = useState(null);
  const [copiedId, setCopiedId] = useState(null);
  const [finalized, setFinalized] = useState(false);

  useEffect(() => {
    listTopics("active").then((res) => {
      setTopics(res.data);
      if (res.data.length > 0) setTopicId(String(res.data[0].id));
    });
  }, []);

  const loadQuestions = async (id) => {
    if (!id) return;
    const [qRes, aRes] = await Promise.all([listQuestions(id), listTopicAttempts(id)]);
    setQuestions(qRes.data);
    const preloaded = {};
    for (const attempt of aRes.data) preloaded[attempt.question_id] = attempt;
    setResults(preloaded);
  };

  useEffect(() => {
    loadQuestions(topicId);
    setExternalPrompt(null);
    setFinalized(false);
  }, [topicId]);

  const sectionScore = (() => {
    const scored = questions.filter((q) => results[q.id]);
    if (scored.length === 0) return null;
    const avg = scored.reduce((sum, q) => sum + results[q.id].score, 0) / scored.length;
    return { avg: Math.round(avg), answered: scored.length, total: questions.length };
  })();

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      await generateQuestions({ topic_id: Number(topicId), count: Number(count), difficulty, provider });
      await loadQuestions(topicId);
    } catch (err) {
      setError(err.response?.data?.detail || "Question generation failed");
    } finally {
      setLoading(false);
    }
  };

  const handleExternalPrompt = async () => {
    const res = await getExternalPrompt(topicId, difficulty, count);
    setExternalPrompt(res.data.prompt);
  };

  const handleSubmitAnswer = async (questionId) => {
    setGrading(questionId);
    setError(null);
    try {
      const res = await submitAttempt({
        question_id: questionId,
        user_answer: answers[questionId] || "",
        provider,
      });
      setResults((prev) => ({ ...prev, [questionId]: res.data }));
    } catch (err) {
      setError(err.response?.data?.detail || "Grading failed");
    } finally {
      setGrading(null);
    }
  };

  const handleCopyQuestion = async (q) => {
    await navigator.clipboard.writeText(q.question_text);
    setCopiedId(q.id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  const handleOpenInClaude = (q) => {
    const prompt = `Can you help me understand and learn this interview question?\n\n${q.question_text}`;
    window.open(`https://claude.ai/new?q=${encodeURIComponent(prompt)}`, "_blank", "noopener,noreferrer");
  };

  const handleFinalize = async () => {
    setFinalized(true);
    if (sectionScore && sectionScore.avg >= 80) {
      const topic = topics.find((t) => String(t.id) === String(topicId));
      if (topic && topic.status === "active") {
        await updateTopic(Number(topicId), { status: "mastered" });
        setTopics((prev) => prev.map((t) => (String(t.id) === String(topicId) ? { ...t, status: "mastered" } : t)));
      }
    }
  };

  const handleStudyAllInClaude = () => {
    const topic = topics.find((t) => String(t.id) === String(topicId));
    const topicName = topic ? topic.name : "this topic";
    const questionList = questions.map((q, i) => `${i + 1}. ${q.question_text}`).join("\n");
    const prompt = `Help me learn this topic - ${topicName} with below questions:\n\n${questionList}`;
    window.open(`https://claude.ai/new?q=${encodeURIComponent(prompt)}`, "_blank", "noopener,noreferrer");
  };

  const handleDeleteQuestion = async (id) => {
    await deleteQuestion(id);
    setQuestions((prev) => prev.filter((q) => q.id !== id));
  };

  const handleAddManual = async () => {
    const question_text = prompt("Question text:");
    if (!question_text) return;
    const ideal_answer = prompt("Ideal answer (optional):") || null;
    await createQuestionManual({ topic_id: Number(topicId), question_text, ideal_answer });
    await loadQuestions(topicId);
  };

  return (
    <div className="space-y-6">
      <section className="bg-white rounded-lg shadow p-6 space-y-4">
        <h2 className="text-lg font-semibold">Study</h2>

        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Topic</label>
            <select
              value={topicId}
              onChange={(e) => setTopicId(e.target.value)}
              className="border rounded-md px-3 py-2 text-sm"
            >
              {topics.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">Provider</label>
            <select value={provider} onChange={(e) => setProvider(e.target.value)} className="border rounded-md px-3 py-2 text-sm">
              {MODEL_OPTIONS.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">Difficulty</label>
            <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)} className="border rounded-md px-3 py-2 text-sm">
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
              value={count}
              onChange={(e) => setCount(e.target.value)}
              className="border rounded-md px-3 py-2 text-sm w-20"
            />
          </div>

          <button
            onClick={handleGenerate}
            disabled={!topicId || loading}
            className="px-4 py-2 text-sm rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? "Generating…" : "Generate Questions"}
          </button>

          <button
            onClick={handleExternalPrompt}
            disabled={!topicId}
            className="px-4 py-2 text-sm rounded-md border border-indigo-600 text-indigo-600 hover:bg-indigo-50"
          >
            Get Prompt for Other Chatbots
          </button>

          <button
            onClick={handleStudyAllInClaude}
            disabled={!topicId || questions.length === 0}
            className="px-4 py-2 text-sm rounded-md bg-orange-500 text-white hover:bg-orange-600 disabled:opacity-50"
          >
            Study all in Claude
          </button>

          <button
            onClick={handleAddManual}
            disabled={!topicId}
            className="px-4 py-2 text-sm rounded-md border text-gray-600 hover:bg-gray-50"
          >
            Add Question Manually
          </button>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        {externalPrompt && (
          <div className="bg-gray-50 border rounded-md p-3">
            <p className="text-xs text-gray-500 mb-1">
              Copy this into ChatGPT, Claude, or any other chatbot to get more/better questions:
            </p>
            <textarea readOnly value={externalPrompt} className="w-full text-sm border rounded-md p-2 h-28" />
          </div>
        )}
      </section>

      {questions.length > 0 && (
        <div className="bg-white rounded-lg shadow p-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500">Section score</span>
            {sectionScore ? (
              <>
                <span
                  className={`text-lg font-bold ${
                    sectionScore.avg >= 80 ? "text-green-600" : sectionScore.avg >= 50 ? "text-yellow-600" : "text-red-500"
                  }`}
                >
                  {sectionScore.avg}/100
                </span>
                <span className="text-xs text-gray-400">
                  {sectionScore.answered}/{sectionScore.total} answered
                </span>
              </>
            ) : (
              <span className="text-sm text-gray-400">No answers yet</span>
            )}
          </div>
          {!finalized ? (
            <button
              onClick={handleFinalize}
              disabled={!sectionScore}
              className="px-4 py-2 text-sm rounded-md bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-40"
            >
              Done with topic
            </button>
          ) : (
            <div className="text-right">
              <p className="text-sm font-semibold text-emerald-700">
                Final score: {sectionScore?.avg ?? 0}/100
                {sectionScore?.avg >= 80 && " · Marked as mastered!"}
              </p>
            </div>
          )}
        </div>
      )}

      <section className="space-y-4">
        {questions.length === 0 && (
          <p className="text-sm text-gray-500">No questions yet for this topic. Generate some above.</p>
        )}
        {questions.map((q) => {
          const result = results[q.id];
          return (
            <div key={q.id} className="bg-white rounded-lg shadow p-6 space-y-3">
              <div className="flex items-start justify-between gap-2">
                <p className="font-medium">{q.question_text}</p>
                <div className="flex items-center gap-2 shrink-0">
                  {result && (
                    <span
                      className={`text-xs font-bold px-2 py-1 rounded-full ${
                        result.score >= 80
                          ? "bg-green-100 text-green-700"
                          : result.score >= 50
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-red-100 text-red-600"
                      }`}
                    >
                      {result.score}/100
                    </span>
                  )}
                  <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-600">
                    {q.difficulty} · {q.source}
                  </span>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => handleCopyQuestion(q)}
                  className="px-3 py-1 text-xs rounded-md border text-gray-600 hover:bg-gray-50"
                >
                  {copiedId === q.id ? "Copied!" : "Copy question"}
                </button>
                <button
                  onClick={() => handleOpenInClaude(q)}
                  className="px-3 py-1 text-xs rounded-md border border-indigo-600 text-indigo-600 hover:bg-indigo-50"
                >
                  Open in Claude
                </button>
                <button
                  onClick={() => handleDeleteQuestion(q.id)}
                  className="px-3 py-1 text-xs rounded-md border border-red-300 text-red-500 hover:bg-red-50 ml-auto"
                >
                  Remove
                </button>
              </div>

              <textarea
                placeholder="Type your answer here…"
                value={answers[q.id] || ""}
                onChange={(e) => setAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))}
                className="w-full border rounded-md p-2 text-sm h-24"
              />

              <button
                onClick={() => handleSubmitAnswer(q.id)}
                disabled={grading === q.id}
                className="px-4 py-2 text-sm rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {grading === q.id ? "Grading…" : "Submit Answer"}
              </button>

              {result && (
                <div className="bg-gray-50 border rounded-md p-3 text-sm">
                  <p className="font-semibold">Score: {result.score}/100</p>
                  <p className="text-gray-600 mt-1">{result.feedback}</p>
                </div>
              )}

              {q.ideal_answer && (
                <details className="text-sm text-gray-500">
                  <summary className="cursor-pointer">Show ideal answer</summary>
                  <p className="mt-1">{q.ideal_answer}</p>
                </details>
              )}
            </div>
          );
        })}
      </section>
    </div>
  );
}
