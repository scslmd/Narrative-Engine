import { useState } from 'react'
import { Settings, X, Trash2, Database, FileText, Scan, Loader2, Check, HardDrive, Key } from 'lucide-react'
import { useThemeStore } from '../stores/themeStore'
import { useSettingsStore, IconMode } from '../stores/settingsStore'
import { themeMeta } from '../theme/theme'
import { useToast } from '../hooks/useToast'
import { scanOrphans, cleanupOrphans, truncateAuditLog, compactDatabase } from '../services/maintenance'
import { useBackups } from '../hooks/useBackups'
import { useAuthKeys } from '../hooks/useAuthKeys'
import type { OrphanInfo, MaintenanceScanResult } from '../types/maintenance'

interface SettingsPanelProps {
  onClose: () => void
}

const iconModes: { value: IconMode; label: string }[] = [
  { value: 'labels', label: 'Icons + Labels' },
  { value: 'icons-large', label: 'Icons Only (Large)' },
  { value: 'icons-small', label: 'Icons Only (Small)' },
]

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  const value = bytes / Math.pow(1024, i)
  return `${value.toFixed(i > 0 ? 1 : 0)} ${units[i]}`
}

function formatNumber(n: number): string {
  return n.toLocaleString()
}

function MaintenanceSection() {
  const { addToast } = useToast()
  const [scanResult, setScanResult] = useState<MaintenanceScanResult | null>(null)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [scanning, setScanning] = useState(false)
  const [cleaning, setCleaning] = useState(false)
  const [truncating, setTruncating] = useState(false)
  const [compacting, setCompacting] = useState(false)

  const allOrphans: OrphanInfo[] = [
    ...(scanResult?.orphaned_dirs ?? []),
    ...(scanResult?.db_only ?? []),
    ...(scanResult?.disk_only ?? []),
  ]

  const handleScan = async () => {
    setScanning(true)
    setSelectedIds(new Set())
    try {
      const result = await scanOrphans()
      setScanResult(result)
      addToast(`Scan complete: ${result.orphaned_dirs.length + result.db_only.length + result.disk_only.length} orphans found`, 'success')
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Scan failed', 'error')
    } finally {
      setScanning(false)
    }
  }

  const toggleItem = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const selectAll = () => setSelectedIds(new Set(allOrphans.map(o => o.project_id)))
  const deselectAll = () => setSelectedIds(new Set())

  const handleCleanup = async () => {
    const ids = Array.from(selectedIds)
    if (ids.length === 0) return
    if (!window.confirm(`Remove ${ids.length} orphaned project(s)? This cannot be undone.`)) return
    setCleaning(true)
    try {
      const result = await cleanupOrphans(ids)
      addToast(`Removed ${result.removed} orphan(s)${result.errors.length > 0 ? `, ${result.errors.length} error(s)` : ''}`, result.errors.length > 0 ? 'info' : 'success')
      setSelectedIds(new Set())
      setScanResult(null)
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Cleanup failed', 'error')
    } finally {
      setCleaning(false)
    }
  }

  const handleTruncate = async () => {
    if (!window.confirm('Truncate old audit log entries? This cannot be undone.')) return
    setTruncating(true)
    try {
      const result = await truncateAuditLog()
      addToast(`Truncated ${result.truncated} lines, retained ${result.retained}`, 'success')
      setScanResult(prev => prev ? { ...prev, summary: { ...prev.summary, audit_log_lines: result.retained } } : null)
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Truncation failed', 'error')
    } finally {
      setTruncating(false)
    }
  }

  const handleCompact = async () => {
    if (!window.confirm('Compact the database? This may take a moment.')) return
    setCompacting(true)
    try {
      const result = await compactDatabase()
      const saved = result.before_bytes - result.after_bytes
      addToast(`Database compacted: ${formatBytes(result.before_bytes)} → ${formatBytes(result.after_bytes)} (saved ${formatBytes(saved)})`, 'success')
      setScanResult(prev => prev ? { ...prev, summary: { ...prev.summary, database_size_bytes: result.after_bytes } } : null)
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Compaction failed', 'error')
    } finally {
      setCompacting(false)
    }
  }

  const kindLabel = (kind: OrphanInfo['kind']) => {
    switch (kind) {
      case 'orphaned_dir': return 'Orphaned Directory'
      case 'db_only': return 'Database Only'
      case 'disk_only': return 'Disk Only'
    }
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <Scan className="w-3.5 h-3.5 text-[var(--text-secondary)]" />
        <h4 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide">Maintenance</h4>
      </div>

      <button
        onClick={handleScan}
        disabled={scanning}
        className="w-full flex items-center justify-center gap-2 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] px-4 py-2.5 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {scanning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Scan className="w-4 h-4" />}
        {scanning ? 'Scanning...' : 'Scan for Orphans'}
      </button>

      {scanResult && (
        <div className="mt-4 space-y-3">
          {/* System Summary */}
          <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] p-3 space-y-2">
            <p className="text-xs font-semibold text-[var(--text-secondary)]">System Summary</p>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
              <div className="flex items-center gap-1.5">
                <FileText className="w-3 h-3 text-[var(--text-tertiary)]" />
                <span className="text-[var(--text-secondary)]">Audit log:</span>
                <span className="text-[var(--text-primary)] font-mono">{formatNumber(scanResult.summary.audit_log_lines)} lines</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Database className="w-3 h-3 text-[var(--text-tertiary)]" />
                <span className="text-[var(--text-secondary)]">DB size:</span>
                <span className="text-[var(--text-primary)] font-mono">{formatBytes(scanResult.summary.database_size_bytes)}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-[var(--text-tertiary)]">Reports:</span>
                <span className="text-[var(--text-primary)] font-mono">{formatNumber(scanResult.summary.checker_report_files)}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-[var(--text-tertiary)]">Jobs:</span>
                <span className="text-[var(--text-primary)] font-mono">{formatNumber(scanResult.summary.total_jobs)}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-[var(--text-tertiary)]">Checker runs:</span>
                <span className="text-[var(--text-primary)] font-mono">{formatNumber(scanResult.summary.total_checker_runs)}</span>
              </div>
            </div>
          </div>

          {/* Orphaned Items */}
          {allOrphans.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-[var(--text-secondary)]">
                  {allOrphans.length} Orphaned Item{allOrphans.length !== 1 ? 's' : ''}
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={selectAll}
                    className="text-xs text-[var(--color-primary)] hover:underline"
                  >
                    Select All
                  </button>
                  <button
                    onClick={deselectAll}
                    className="text-xs text-[var(--text-tertiary)] hover:underline"
                  >
                    Deselect All
                  </button>
                </div>
              </div>

              <div className="space-y-1 max-h-48 overflow-y-auto">
                {allOrphans.map((item) => (
                  <label
                    key={item.project_id}
                    className={`
                      flex items-center gap-2 rounded-lg border px-3 py-2 cursor-pointer transition-all
                      ${selectedIds.has(item.project_id)
                        ? 'border-[var(--color-primary)] bg-[var(--color-primary-subtle)]'
                        : 'border-[var(--border-primary)] hover:bg-[var(--bg-secondary)]'
                      }
                    `}
                  >
                    <div className={`
                      w-3.5 h-3.5 rounded border flex items-center justify-center flex-shrink-0
                      ${selectedIds.has(item.project_id)
                        ? 'border-[var(--color-primary)] bg-[var(--color-primary)]'
                        : 'border-[var(--border-secondary)]'
                      }
                    `}>
                      {selectedIds.has(item.project_id) && <Check className="w-2.5 h-2.5 text-white" />}
                    </div>
                    <input
                      type="checkbox"
                      checked={selectedIds.has(item.project_id)}
                      onChange={() => toggleItem(item.project_id)}
                      className="sr-only"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm text-[var(--text-primary)] truncate">
                          {item.project_name || item.project_id}
                        </span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--bg-tertiary)] text-[var(--text-tertiary)] font-medium">
                          {kindLabel(item.kind)}
                        </span>
                      </div>
                      <div className="text-xs text-[var(--text-tertiary)] truncate">
                        {item.project_id} · {formatBytes(item.size_bytes)}
                      </div>
                    </div>
                  </label>
                ))}
              </div>

              <button
                onClick={handleCleanup}
                disabled={selectedIds.size === 0 || cleaning}
                className="w-full flex items-center justify-center gap-2 rounded-lg border border-[var(--color-destructive)] bg-[var(--color-destructive-subtle)] px-4 py-2.5 text-sm font-medium text-[var(--color-destructive)] hover:bg-[var(--color-destructive)] hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {cleaning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                {cleaning ? 'Cleaning...' : `Clean Selected (${selectedIds.size})`}
              </button>
            </div>
          )}

          {/* System Actions */}
          <div className="space-y-2 pt-2 border-t border-[var(--border-primary)]">
            <p className="text-xs font-semibold text-[var(--text-secondary)]">System Actions</p>
            <button
              onClick={handleTruncate}
              disabled={truncating}
              className="w-full flex items-center justify-center gap-2 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] px-4 py-2.5 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {truncating ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
              {truncating ? 'Truncating...' : 'Truncate Audit Log'}
            </button>
            <button
              onClick={handleCompact}
              disabled={compacting}
              className="w-full flex items-center justify-center gap-2 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] px-4 py-2.5 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {compacting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Database className="w-4 h-4" />}
              {compacting ? 'Compacting...' : 'Compact Database'}
            </button>
          </div>
        </div>
      )}

      {!scanResult && !scanning && (
        <p className="mt-2 text-xs text-[var(--text-tertiary)] text-center">
          Run a scan to check for orphaned projects and view system stats.
        </p>
      )}
    </div>
  )
}

function BackupsSection() {
  const { addToast } = useToast()
  const { backups, isLoading, createBackup, restoreBackup, deleteBackup, isCreating, isRestoring, isDeleting } = useBackups()

  const handleCreate = async () => {
    try {
      await createBackup()
      addToast('Backup created successfully', 'success')
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Backup creation failed', 'error')
    }
  }

  const handleRestore = async (backupId: string) => {
    if (!window.confirm(`Restore backup ${backupId}? This will overwrite current data.`)) return
    try {
      await restoreBackup(backupId)
      addToast('Backup restored successfully', 'success')
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Restore failed', 'error')
    }
  }

  const handleDelete = async (backupId: string) => {
    if (!window.confirm(`Delete backup ${backupId}? This cannot be undone.`)) return
    try {
      await deleteBackup(backupId)
      addToast('Backup deleted', 'success')
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Delete failed', 'error')
    }
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <HardDrive className="w-3.5 h-3.5 text-[var(--text-secondary)]" />
        <h4 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide">Backups</h4>
      </div>

      <button
        onClick={handleCreate}
        disabled={isCreating}
        className="w-full flex items-center justify-center gap-2 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] px-4 py-2.5 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isCreating ? <Loader2 className="w-4 h-4 animate-spin" /> : <HardDrive className="w-4 h-4" />}
        {isCreating ? 'Creating...' : 'Create Backup'}
      </button>

      {isLoading && (
        <p className="mt-3 text-xs text-[var(--text-tertiary)] text-center">Loading backups...</p>
      )}

      {!isLoading && backups.length === 0 && (
        <p className="mt-3 text-xs text-[var(--text-tertiary)] text-center">No backups yet.</p>
      )}

      {!isLoading && backups.length > 0 && (
        <div className="mt-3 space-y-1.5 max-h-48 overflow-y-auto">
          {backups.map((backup) => (
            <div
              key={backup.backup_id}
              className="flex items-center justify-between rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] px-3 py-2"
            >
              <div className="min-w-0 flex-1">
                <div className="text-xs font-medium text-[var(--text-primary)] truncate">{backup.backup_id}</div>
                <div className="text-[10px] text-[var(--text-tertiary)]">
                  {new Date(backup.created_at).toLocaleString()} · {backup.size_mb.toFixed(1)} MB · {backup.project_count} project{backup.project_count !== 1 ? 's' : ''}
                </div>
              </div>
              <div className="flex items-center gap-1 flex-shrink-0 ml-2">
                <button
                  onClick={() => handleRestore(backup.backup_id)}
                  disabled={isRestoring}
                  className="text-[10px] px-2 py-1 rounded border border-[var(--border-primary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] transition-colors disabled:opacity-50"
                >
                  Restore
                </button>
                <button
                  onClick={() => handleDelete(backup.backup_id)}
                  disabled={isDeleting}
                  className="text-[10px] px-2 py-1 rounded border border-[var(--color-destructive)] text-[var(--color-destructive)] hover:bg-[var(--color-destructive)] hover:text-white transition-colors disabled:opacity-50"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function AuthKeysSection() {
  const { addToast } = useToast()
  const { keys, isLoading, createKey, deleteKey, isCreating, isDeleting } = useAuthKeys()
  const [newKeyName, setNewKeyName] = useState('')

  const handleCreate = async () => {
    const name = newKeyName.trim()
    if (!name) return
    try {
      await createKey(name)
      addToast(`API key "${name}" created`, 'success')
      setNewKeyName('')
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Key creation failed', 'error')
    }
  }

  const handleDelete = async (prefix: string) => {
    if (!window.confirm(`Revoke key "${prefix}"? This cannot be undone.`)) return
    try {
      await deleteKey(prefix)
      addToast('API key revoked', 'success')
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Delete failed', 'error')
    }
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <Key className="w-3.5 h-3.5 text-[var(--text-secondary)]" />
        <h4 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide">API Keys</h4>
      </div>

      <div className="flex gap-2 mb-3">
        <input
          type="text"
          value={newKeyName}
          onChange={(e) => setNewKeyName(e.target.value)}
          placeholder="Key name"
          className="flex-1 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--color-primary)]"
        />
        <button
          onClick={handleCreate}
          disabled={isCreating || !newKeyName.trim()}
          className="flex items-center gap-1.5 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] px-3 py-2 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
        >
          {isCreating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Key className="w-3.5 h-3.5" />}
          Create
        </button>
      </div>

      {isLoading && (
        <p className="text-xs text-[var(--text-tertiary)] text-center">Loading keys...</p>
      )}

      {!isLoading && keys.length === 0 && (
        <p className="text-xs text-[var(--text-tertiary)] text-center">No API keys.</p>
      )}

      {!isLoading && keys.length > 0 && (
        <div className="space-y-1.5 max-h-48 overflow-y-auto">
          {keys.map((key) => (
            <div
              key={key.key_prefix}
              className="flex items-center justify-between rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] px-3 py-2"
            >
              <div className="min-w-0 flex-1">
                <div className="text-xs font-medium text-[var(--text-primary)] truncate">{key.name}</div>
                <div className="text-[10px] text-[var(--text-tertiary)]">
                  {key.key_prefix} · {key.permissions.join(', ')}
                </div>
                <div className="text-[10px] text-[var(--text-tertiary)]">
                  Created {new Date(key.created_at).toLocaleString()}
                  {key.expires_at ? ` · Expires ${new Date(key.expires_at).toLocaleDateString()}` : ' · No expiry'}
                </div>
              </div>
              <button
                onClick={() => handleDelete(key.key_prefix)}
                disabled={isDeleting}
                className="text-[10px] px-2 py-1 rounded border border-[var(--color-destructive)] text-[var(--color-destructive)] hover:bg-[var(--color-destructive)] hover:text-white transition-colors disabled:opacity-50 flex-shrink-0 ml-2"
              >
                Revoke
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function SettingsPanel({ onClose }: SettingsPanelProps) {
  const { mode: themeMode, setMode: setThemeMode, toggleMode } = useThemeStore()
  const { iconMode, showTooltips, setIconMode, setShowTooltips } = useSettingsStore()

  return (
    <div className="fixed inset-0 z-[600] flex items-center justify-center" onClick={onClose}>
      <div className="absolute inset-0 bg-black/40" />
      <div
        className="relative w-full max-w-md mx-4 rounded-xl border bg-[var(--bg-primary)] shadow-elevated"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b px-5 py-4">
          <div className="flex items-center gap-2">
            <Settings className="w-4 h-4" />
            <h3 className="text-sm font-semibold">Settings</h3>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-5 py-4 space-y-5">
          {/* Theme Selection */}
          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-2">
              Theme
            </label>
            <div className="grid grid-cols-5 gap-2">
              {(Object.keys(themeMeta) as Array<keyof typeof themeMeta>).map((key) => {
                const theme = themeMeta[key]
                const isActive = themeMode === key
                return (
                  <button
                    key={key}
                    onClick={() => setThemeMode(key)}
                    className={`
                      relative flex flex-col items-center gap-1 rounded-lg border px-2 py-2 text-xs transition-all
                      ${isActive
                        ? 'border-[var(--color-primary)] bg-[var(--color-primary-subtle)] text-[var(--color-primary)]'
                        : 'border-[var(--border-primary)] text-[var(--text-secondary)] hover:border-[var(--border-secondary)] hover:bg-[var(--bg-secondary)]'
                      }
                    `}
                  >
                    <span className="text-base">{theme.icon}</span>
                    <span className="truncate">{theme.label}</span>
                    {isActive && (
                      <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-[var(--color-primary)]" />
                    )}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Quick Toggle */}
          <div>
            <button
              onClick={toggleMode}
              className="w-full rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] px-4 py-2.5 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors"
            >
              Switch Theme
            </button>
          </div>

          {/* Icon Mode */}
          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-2">
              Navigation Icon Mode
            </label>
            <div className="space-y-1.5">
              {iconModes.map((mode) => (
                <button
                  key={mode.value}
                  onClick={() => setIconMode(mode.value)}
                  className={`
                    w-full flex items-center gap-3 rounded-lg border px-3 py-2.5 text-left text-sm transition-all
                    ${iconMode === mode.value
                      ? 'border-[var(--color-primary)] bg-[var(--color-primary-subtle)]'
                      : 'border-[var(--border-primary)] bg-transparent hover:bg-[var(--bg-secondary)]'
                    }
                  `}
                >
                  <div className={`
                    w-3.5 h-3.5 rounded-full border flex items-center justify-center flex-shrink-0
                    ${iconMode === mode.value
                      ? 'border-[var(--color-primary)]'
                      : 'border-[var(--border-secondary)]'
                    }
                  `}>
                    {iconMode === mode.value && (
                      <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-primary)]" />
                    )}
                  </div>
                  <span className="text-[var(--text-primary)]">{mode.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Tooltips Toggle */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-[var(--text-primary)]">Show Tooltips</p>
              <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                Hover over icons to see descriptions
              </p>
            </div>
            <button
              onClick={() => setShowTooltips(!showTooltips)}
              className={`
                relative w-11 h-6 rounded-full transition-colors
                ${showTooltips ? 'bg-[var(--color-primary)]' : 'bg-[var(--border-secondary)]'}
              `}
            >
              <div
                className={`
                  absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform
                  ${showTooltips ? 'translate-x-5' : 'translate-x-0'}
                `}
              />
            </button>
          </div>

          {/* Maintenance */}
          <div className="border-t border-[var(--border-primary)] pt-5">
            <MaintenanceSection />
          </div>

          {/* Backups */}
          <div className="border-t border-[var(--border-primary)] pt-5">
            <BackupsSection />
          </div>

          {/* API Keys */}
          <div className="border-t border-[var(--border-primary)] pt-5">
            <AuthKeysSection />
          </div>
        </div>
      </div>
    </div>
  )
}
