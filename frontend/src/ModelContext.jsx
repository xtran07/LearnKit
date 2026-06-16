import { createContext, useContext, useEffect, useState } from "react";
import { getUserSettings, updateUserSettings } from "./api/client.js";
import { useAuth } from "./AuthContext.jsx";

const ModelContext = createContext(null);

const STORAGE_KEY = "preferredProvider";

export const MODEL_OPTIONS = [
  { value: "gemini", label: "Gemini 2.5 Flash" },
  { value: "groq", label: "Llama 3.3 70B (Groq)" },
  { value: "openrouter-llama", label: "Llama 3.3 70B (OpenRouter, free)" },
  { value: "openrouter-gemma", label: "Gemma 4 31B (OpenRouter, free)" },
  { value: "openrouter-gpt", label: "GPT-OSS 120B (OpenRouter, free)" },
  { value: "openrouter-nex", label: "Nex-N2-Pro (OpenRouter, free)" },
];

export function ModelProvider({ children }) {
  const { user } = useAuth();
  const [provider, setProviderState] = useState(
    () => localStorage.getItem(STORAGE_KEY) || "gemini"
  );

  useEffect(() => {
    if (!user) return;
    getUserSettings()
      .then((res) => {
        setProviderState(res.data.preferred_provider);
        localStorage.setItem(STORAGE_KEY, res.data.preferred_provider);
      })
      .catch(() => {});
  }, [user]);

  const setProvider = (value) => {
    setProviderState(value);
    localStorage.setItem(STORAGE_KEY, value);
    updateUserSettings({ preferred_provider: value }).catch(() => {});
  };

  return (
    <ModelContext.Provider value={{ provider, setProvider }}>
      {children}
    </ModelContext.Provider>
  );
}

export const useModel = () => useContext(ModelContext);

export const modelLabel = (value) =>
  MODEL_OPTIONS.find((m) => m.value === value)?.label || value;
