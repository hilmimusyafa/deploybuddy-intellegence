import { generateDeploymentAnalysis, generateFollowUpResponse } from "./gemini";

export async function analyzeDeployment(
  repo: string,
  service: string,
  region: string,
  budget: string,
  userMessage: string,
): Promise<string> {
  try {
    return await generateDeploymentAnalysis(repo, service, region, budget, userMessage);
  } catch (error) {
    console.error("Analysis error:", error);
    throw error;
  }
}

export async function sendFollowUp(
  userMessage: string,
  context: {
    repo: string;
    service: string;
    region: string;
    budget?: string;
    previousAnalysis?: Record<string, unknown>;
  },
): Promise<string> {
  try {
    return await generateFollowUpResponse(userMessage, context);
  } catch (error) {
    console.error("Follow-up error:", error);
    throw error;
  }
}
