function InputScreen({ userData, setUserData }) {
  const handleChange = (e) => {
    const { name, value } = e.target;
    setUserData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log("User Data:", userData);
    alert("Data submitted! Check console.");
  };

  return (
    <div className="input-screen">
      <h2>Enter Your Details</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Height (cm): </label>
          <input
            type="number"
            name="height"
            value={userData.height}
            onChange={handleChange}
            required
          />
        </div>
        <div>
          <label>Weight (kg): </label>
          <input
            type="number"
            name="weight"
            value={userData.weight}
            onChange={handleChange}
            required
          />
        </div>
        <div>
          <label>Age: </label>
          <input
            type="number"
            name="age"
            value={userData.age}
            onChange={handleChange}
            required
          />
        </div>
        <button type="submit">Submit</button>
      </form>
    </div>
  );
}

export default InputScreen;