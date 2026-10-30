import "@testing-library/jest-dom/vitest";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";
import { clearCache } from "./api";

afterEach(() => {
  cleanup();
  clearCache();
  vi.restoreAllMocks();
});
