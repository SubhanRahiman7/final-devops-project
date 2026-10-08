const STEPS = ["Commit", "CI tests", "Trivy scan", "Image to GHCR", "Helm deploy", "Monitored"];

export default function Pipeline() {
  return (
    <section className="panel">
      <h3>Delivery pipeline</h3>
      <ol className="pipeline">
        {STEPS.map((step) => (
          <li key={step}><span className="check">&#10003;</span>{step}</li>
        ))}
      </ol>
    </section>
  );
}
