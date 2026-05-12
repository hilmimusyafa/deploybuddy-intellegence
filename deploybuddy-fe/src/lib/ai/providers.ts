import { google } from "@ai-sdk/google";
import { customProvider } from "ai";

export const myProvider = customProvider({
  languageModels: {
    "chat-model": google("gemini-2.0-flash"),
    "title-model": google("gemini-2.0-flash"),
  },
});

export function getLanguageModel(modelId: string) {
  return myProvider.languageModel(modelId);
}

export function getTitleModel() {
  return myProvider.languageModel("title-model");
}
