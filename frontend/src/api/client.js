import axios from "axios";
import { supabase } from "../supabaseClient.js";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
});

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  if (data.session) {
    config.headers.Authorization = `Bearer ${data.session.access_token}`;
  }
  return config;
});

// ---- Resumes ----
export const uploadResume = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post("/resumes/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const listResumes = () => api.get("/resumes");

export const getResumeUrl = (resumeId, download = false) =>
  api.get(`/resumes/${resumeId}/url`, { params: { download } });

export const suggestTopics = (resumeId, provider = "gemini") =>
  api.post(`/resumes/${resumeId}/suggest-topics`, null, { params: { provider } });

// ---- Topics ----
export const listTopics = (status) => api.get("/topics", { params: status ? { status } : {} });

export const createTopic = (name) => api.post("/topics", { name });

export const updateTopic = (id, payload) => api.patch(`/topics/${id}`, payload);

export const deleteTopic = (id) => api.delete(`/topics/${id}`);

// ---- Questions ----
export const listQuestions = (topicId) => api.get("/questions", { params: { topic_id: topicId } });

export const generateQuestions = (payload) => api.post("/questions/generate", payload);

export const createQuestionManual = (payload) => api.post("/questions/manual", payload);

export const deleteQuestion = (id) => api.delete(`/questions/${id}`);

export const getExternalPrompt = (topicId, difficulty = "medium", count = 5) =>
  api.get("/questions/external-prompt", { params: { topic_id: topicId, difficulty, count } });

// ---- Progress / Attempts ----
export const submitAttempt = (payload) => api.post("/attempts", payload);

export const listAttempts = (questionId) => api.get("/attempts", { params: { question_id: questionId } });

export const getProgress = () => api.get("/progress");

// ---- Job Applications ----
export const listApplications = (status) => api.get("/applications", { params: status ? { status } : {} });

export const createApplication = (payload) => api.post("/applications", payload);

export const updateApplication = (id, payload) => api.patch(`/applications/${id}`, payload);

export const deleteApplication = (id) => api.delete(`/applications/${id}`);

export const resolveApplicationLink = (url) => api.post("/applications/resolve", { url });

// ---- Application Mock Interview Questions ----
export const listAppQuestions = (applicationId) => api.get(`/applications/${applicationId}/questions`);

export const generateAppQuestions = (applicationId, payload) =>
  api.post(`/applications/${applicationId}/questions/generate`, payload);

export const deleteAppQuestion = (id) => api.delete(`/applications/questions/${id}`);

// ---- Job Leads (Find Jobs) ----
export const listJobLeads = () => api.get("/job-leads");

export const searchJobLeads = (query, location) =>
  api.post("/job-leads/search", { query, location: location || null });

export const addJobLead = (id) => api.post(`/job-leads/${id}/add`);

export const dismissJobLead = (id) => api.delete(`/job-leads/${id}`);

export default api;
