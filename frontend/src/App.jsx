import { BrowserRouter, Route, Routes } from "react-router-dom";

import Home from "./pages/Home";
import Paper from "./pages/Paper";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/paper" element={<Paper />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;