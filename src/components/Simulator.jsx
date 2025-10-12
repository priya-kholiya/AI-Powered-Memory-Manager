import { useState } from "react";
import AlgorithmForm from "./AlgorithmForm";
import Results from "./Results";

export default function Simulator() {
  const [results, setResults] = useState(null);

  return (
    <div className="app-container">
      <h1>Page Replacement Simulator</h1>
      <AlgorithmForm setResults={setResults} />
      {results && <Results results={results} />}
    </div>
  );
}
