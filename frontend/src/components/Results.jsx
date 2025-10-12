export default function Results({ results }) {
  return (
    <div className="results">
      <h2>Results</h2>
      <table>
        <thead>
          <tr><th>Algorithm</th><th>Page Faults</th><th>Hit Ratio</th></tr>
        </thead>
        <tbody>
          {results.map((r,i)=><tr key={i}><td>{r.algorithm}</td><td>{r.pageFaults}</td><td>{r.hitRatio}</td></tr>)}
        </tbody>
      </table>
    </div>
  );
}
