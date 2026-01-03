import { createRoot } from "react-dom/client";
import Main from "./ui/Main"; // <— IMPORTANT: default import

const rootElem = document.getElementById("root");
if (rootElem) {
  createRoot(rootElem).render(<Main />);
}
