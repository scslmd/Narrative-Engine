export interface OrphanInfo {
  project_id: string;
  project_name: string | null;
  kind: 'orphaned_dir' | 'db_only' | 'disk_only';
  size_bytes: number;
}

export interface MaintenanceSummary {
  audit_log_lines: number;
  audit_log_retain_lines: number;
  database_size_bytes: number;
  checker_report_files: number;
  total_jobs: number;
  total_checker_runs: number;
}

export interface MaintenanceScanResult {
  orphaned_dirs: OrphanInfo[];
  db_only: OrphanInfo[];
  disk_only: OrphanInfo[];
  summary: MaintenanceSummary;
}

export interface MaintenanceCleanupResult {
  removed: number;
  errors: Array<{ project_id: string; error: string }>;
}

export interface AuditLogTruncationResult {
  truncated: number;
  retained: number;
}

export interface DatabaseCompactionResult {
  before_bytes: number;
  after_bytes: number;
}
