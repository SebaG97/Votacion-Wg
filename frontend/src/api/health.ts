import { apiGet } from "./client";

export type HealthResponse = {
  status: string;
  app_name: string;
  environment: string;
  api_prefix: string;
};

export function getHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/health");
}
