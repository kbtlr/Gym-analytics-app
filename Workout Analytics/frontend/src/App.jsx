import { useState } from "react";
import WelcomeScreen from "./components/WelcomeScreen";
import InputScreen from "./components/InputScreen";
import "./App.css";

function App() {
  const [step, setStep] = useState(1); // Step 1 = Welcome, Step 2 = Input
  const [userData, setUserData] = useState({
    height: "",
    weight: "",
    age: "",
  });

  return (
    <div className="App">
      {step === 1 && <WelcomeScreen onNext={() => setStep(2)} />}
      {step === 2 && (
        <InputScreen userData={userData} setUserData={setUserData} />
      )}
    </div>
  );
}

export default App;