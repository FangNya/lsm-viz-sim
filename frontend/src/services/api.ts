import type {
  LSMConfig,
  RunWorkloadResponse,
  SimulatorState,
  StepResponse,
  WorkloadOperation
} from "../types/sim";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(path, {
    headers: {
      "Content-Type": "application/json"
    },
    ...init
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`HTTP ${resp.status}: ${text}`);
  }

  return (await resp.json()) as T;
}

export const simApi = {
  getState(): Promise<SimulatorState> {
    return request<SimulatorState>("/sim/state");
  },

  applyConfig(config: LSMConfig): Promise<{ status: string; config: LSMConfig }> {
    return request("/sim/config", {
      method: "POST",
      body: JSON.stringify(config)
    });
  },

  reset(): Promise<{ status: string }> {
    return request("/sim/reset", { method: "POST" });
  },

  runWorkload(operations: WorkloadOperation[]): Promise<RunWorkloadResponse> {
    return request("/sim/run_workload", {
      method: "POST",
      body: JSON.stringify({ operations })
    });
  },

  step(operation: WorkloadOperation): Promise<StepResponse> {
    return request("/sim/step", {
      method: "POST",
      body: JSON.stringify({ operation })
    });
  },

  exportTrace(format: "json" | "csv"): Promise<{ format: string; content: string }> {
    return request(`/sim/export/trace?format=${format}`);
  }
};
