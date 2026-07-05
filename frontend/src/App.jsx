import { useState } from "react";
import Home from "./components/Home";
import QuestionnaireForm from "./components/QuestionnaireForm";
import Dashboard from "./components/Dashboard";

function App() {
  const [view, setView] = useState("home"); // home | questionnaire
  const [result, setResult] = useState(null); // { userInput, plan }

  if (result) {
    return (
      <Dashboard
        plan={result.plan}
        userInput={result.userInput}
        onReset={() => {
          setResult(null);
          setView("home");
        }}
      />
    );
  }

  if (view === "questionnaire") {
    return (
      <QuestionnaireForm
        onGenerated={(userInput, plan) => setResult({ userInput, plan })}
      />
    );
  }

  return <Home onGenerate={() => setView("questionnaire")} />;
}

export default App;
