import { generateText } from "ai";
import { google } from "@ai-sdk/google";

const apiKey = process.env.GOOGLE_GENERATIVE_AI_API_KEY;
console.log("API Key exists:", !!apiKey);

try {
  const result = await generateText({
    model: google("gemini-2.0-flash"),
    prompt: "Say hello",
  });
  console.log("Success:", result.text);
} catch (error) {
  console.error("Error:", error.message);
}
