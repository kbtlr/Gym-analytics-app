import { useState } from "react";
import WelcomeScreen from "./components/WelcomeScreen";
import InputScreen from "./components/InputScreen";
import SecondInput from "./components/SecondInput";
import MainPage from "./components/MainPage";
import "./App.css";

function App() {
  const [step, setStep] = useState(1);

  const [userData, setUserData] = useState({
    height: "",
    weight: "",
    age: "",
  });

  return (
    <div className="App">
      {step === 1 && <WelcomeScreen onNext={() => setStep(2)} />}

      {step === 2 && (
        <InputScreen
          userData={userData}
          setUserData={setUserData}
          onNext={() => setStep(3)}
        />
      )}

      {step === 3 && (
        <SecondInput
          userData={userData}
          setUserData={setUserData}
          onNext={() => setStep(4)}
        />
      )}

      {step === 4 && <MainPage userData={userData} />}
    </div>
  );
}