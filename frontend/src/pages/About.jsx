export default function About() {
  return (
    <div className="narrow">
      <header className="page-head">
        <div>
          <p className="eyebrow">Project notes</p>
          <h1>About SmartMed</h1>
        </div>
      </header>
      <section className="card prose">
        <h2>What this system does</h2>
        <p>
          SmartMed is a college major-project assistant for medication <em>adherence reminders</em> and
          <em> package-label comparison</em>. You register medicines you already have, including name, strength,
          schedule, expiry date, and an optional barcode. When a scheduled time arrives, you can scan the
          package. OpenCV prepares the photo, Tesseract reads printed text, and a barcode detector is used
          when a code is visible. The detected text is compared with your saved record.
        </p>
        <h2>What this system does not do</h2>
        <ul>
          <li>It does not diagnose medical conditions.</li>
          <li>It does not prescribe medicines or recommend dosages.</li>
          <li>It does not modify a clinician’s prescription.</li>
          <li>It does not tell you that a medicine is medically safe to take.</li>
          <li>A “match” only means the scan appears similar to the record you saved.</li>
        </ul>
        <h2>If you are uncertain</h2>
        <p>
          Check the physical package and your prescription, or contact a pharmacist or healthcare
          professional. Do not take or skip a medicine based only on OCR or barcode output.
        </p>
        <h2>Technical outline</h2>
        <p>
          The React client talks to a FastAPI backend. SQLite stores users, medicines, schedules, dose
          history, and caregivers. Passwords are stored as PBKDF2 hashes. Photo verification is a replaceable
          OCR module so a later team can swap Tesseract for a stronger vision model without changing the
          reminder workflow.
        </p>
      </section>
    </div>
  );
}
