function WelcomeScreen({ onNext }) {
  return (
    <div className="welcome-screen">
      <h1>Welcome to My Gym App</h1>
      <p>Track your fitness journey easily!</p>
      <button onClick={onNext}>Get Started</button>
    </div>
  );
}

export default WelcomeScreen;