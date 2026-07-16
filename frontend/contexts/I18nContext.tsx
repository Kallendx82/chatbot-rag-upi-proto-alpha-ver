"use client";

import { createContext, useContext, useEffect, useState } from "react";
import en from "@/locales/en.json";
import id from "@/locales/id.json";

type Language = "en" | "id";

interface I18nContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (path: string) => string;
  translations: Record<string, any>;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

const translations = { en, id };

function getNestedValue(obj: any, path: string): string {
  return path.split(".").reduce((current, key) => current?.[key], obj) || path;
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("language") as Language | null;
      if (stored && ["en", "id"].includes(stored)) {
        return stored;
      }
    }
    return "id";
  });

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    if (typeof window !== "undefined") {
      localStorage.setItem("language", lang);
    }
  };

  const t = (path: string): string => {
    return getNestedValue(translations[language], path);
  };

  return (
    <I18nContext.Provider
      value={{
        language,
        setLanguage,
        t,
        translations: translations[language],
      }}
    >
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n(): I18nContextType {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error("useI18n must be used within I18nProvider");
  }
  return context;
}
