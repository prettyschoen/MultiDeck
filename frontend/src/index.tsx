import { createRoot } from "react-dom/client";
import { Main } from "./ui/Main";

const rootElem = document.getElementById("root");
if (rootElem) {
  const root = createRoot(rootElem);
  root.render(<Main />);
}