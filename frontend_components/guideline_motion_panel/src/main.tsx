import React from "react";
import ReactDOM from "react-dom/client";
import StreamlitBridge from "./StreamlitBridge";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <StreamlitBridge />
  </React.StrictMode>
);
