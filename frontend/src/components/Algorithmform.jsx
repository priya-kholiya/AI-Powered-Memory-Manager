import { useState } from "react";

function parsePageString(s) {
  return s.split(",").map(x => Number(x.trim()));
}

function runFIFO(pages, framesCount) { 
  let frames = [], faults = 0;
  for (let p of pages) {
    if(!frames.includes(p)){
      faults++;
      frames.push(p);
      if(frames.length > framesCount) frames.shift();
    }
  }
  const hitRatio = ((pages.length - faults)/pages.length)*100;
  return {algorithm:"FIFO", pageFaults:faults, hitRatio:hitRatio.toFixed(2)+"%"};
}

export default function Algorithmform({ setResults }) {
  const [form, setForm] = useState({
    processId: "",
    memorySize: "",
    pageRefString: "",
    frames: "",
    algorithms: []
  });

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });
  const handleCheckbox = (e) => {
    const val = e.target.value;
    setForm(prev => ({
      ...prev,
      algorithms: e.target.checked ? [...prev.algorithms,val] : prev.algorithms.filter(a=>a!==val)
    }));
  }

  const handleSubmit = (e) => {
    e.preventDefault();
    const pages = parsePageString(form.pageRefString);
    const results = form.algorithms.map(algo => algo==="FIFO"?runFIFO(pages, Number(form.frames)):{});
    setResults(results);
  }

  return (
    <form onSubmit={handleSubmit} className="form-container">
      <label>Process ID:
        <input type="text" name="processId" onChange={handleChange}/>
      </label>
      <label>Page Reference String:
        <input type="text" name="pageRefString" placeholder="e.g.1,2,3" onChange={handleChange}/>
      </label>

      <div className="row">
        <label>Memory Size:
          <input type="number" name="memorySize" onChange={handleChange}/>
        </label>
        <label>Allocated Frames:
          <input type="number" name="frames" onChange={handleChange}/>
        </label>
      </div>

      <fieldset className="algos">
        <legend>Select Algorithms:</legend>
        <label><input type="checkbox" value="FIFO" onChange={handleCheckbox}/> FIFO</label>
        <label><input type="checkbox" value="LRU" onChange={handleCheckbox}/> LRU</label>
        <label><input type="checkbox" value="Optimal" onChange={handleCheckbox}/> Optimal</label>
      </fieldset>

      <button type="submit">Submit</button>
    </form>
  );
}
