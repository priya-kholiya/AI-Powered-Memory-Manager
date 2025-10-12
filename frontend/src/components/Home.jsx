import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="home-container">
      <h1>Welcome to Page Replacement Simulator</h1>
      <p>Learn and visualize how different page replacement algorithms work!</p>
      <button onClick={() => navigate("/simulator")}>Go to Simulator</button>
    </div>
  );
}