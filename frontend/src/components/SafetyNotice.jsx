export function SafetyNotice({ compact = false }) {
  return (
    <p className={compact ? "notice notice-compact" : "notice"}>
      SmartMed compares scanned package information with medicines you already saved. It does not
      diagnose conditions, prescribe medicines, recommend dosages, or confirm that a medicine is
      safe to take.
    </p>
  );
}
