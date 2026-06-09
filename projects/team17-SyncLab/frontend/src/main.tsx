import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";

async function enableMocking() {
  const shouldUseMsw =
    import.meta.env.DEV &&
    !import.meta.env.VITE_API_BASE_URL &&
    import.meta.env.VITE_ENABLE_MSW !== "false";

  if (!shouldUseMsw) {
    return;
  }

  const { worker } = await import("./mocks/browser");

  await worker.start({
    onUnhandledRequest: "bypass",
  });
}

enableMocking().then(() => {
  createRoot(document.getElementById("root")!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
});
