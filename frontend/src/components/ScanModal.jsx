import React, { useState } from 'react';
import { X, Folder, AlertCircle, Play, StopCircle, RefreshCw, CheckCircle2 } from 'lucide-react';
import { triggerScan, cancelScan } from '../api';

export default function ScanModal({
  isOpen,
  onClose,
  scanStatus,
  onScanStarted,
}) {
  const [folderPath, setFolderPath] = useState('');
  const [forceRescan, setForceRescan] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleStartScan = async (e) => {
    e.preventDefault();
    if (!folderPath.trim()) return;
    setError(null);
    setLoading(true);
    try {
      await triggerScan(folderPath.trim(), forceRescan);
      onScanStarted();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    try {
      await cancelScan();
    } catch (err) {
      alert('Failed to cancel scan: ' + err.message);
    }
  };

  const quickFolders = [
    { label: 'Pictures', path: 'C:\\Users\\dhruvil\\Pictures' },
    { label: 'Desktop', path: 'C:\\Users\\dhruvil\\Desktop' },
    { label: 'Downloads', path: 'C:\\Users\\dhruvil\\Downloads' },
  ];

  const isScanning = scanStatus?.is_scanning;
  const progressPercent =
    scanStatus?.total_files > 0
      ? Math.round((scanStatus.processed_files / scanStatus.total_files) * 100)
      : 0;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full border border-zinc-200/80 shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-zinc-100">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-zinc-100 flex items-center justify-center text-zinc-700">
              <Folder className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-zinc-900 text-base">Scan Local Folder</h3>
              <p className="text-xs text-zinc-500">Index photos and generate instant WebP thumbnails</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-zinc-100 text-zinc-400 hover:text-zinc-600 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {error && (
            <div className="mb-5 p-3.5 rounded-xl bg-red-50 border border-red-200/80 flex items-start gap-2.5 text-xs text-red-700">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
              <span>{error}</span>
            </div>
          )}

          {isScanning ? (
            /* Active Scanning Progress */
            <div className="space-y-5">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-semibold text-zinc-700">
                  <span className="flex items-center gap-1.5">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-zinc-800" />
                    Scanning directory...
                  </span>
                  <span>{progressPercent}%</span>
                </div>
                <div className="w-full bg-zinc-100 rounded-full h-2.5 overflow-hidden">
                  <div
                    className="bg-zinc-900 h-2.5 rounded-full transition-all duration-300"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>

              <div className="bg-zinc-50 rounded-xl p-4 border border-zinc-200/60 space-y-2 text-xs">
                <div className="flex justify-between text-zinc-600">
                  <span className="text-zinc-400">Total discovered:</span>
                  <span className="font-medium text-zinc-800">{scanStatus.total_files} files</span>
                </div>
                <div className="flex justify-between text-zinc-600">
                  <span className="text-zinc-400">Indexed & thumbnails:</span>
                  <span className="font-medium text-zinc-800">{scanStatus.indexed_count}</span>
                </div>
                <div className="flex justify-between text-zinc-600">
                  <span className="text-zinc-400">Skipped (cached):</span>
                  <span className="font-medium text-zinc-800">{scanStatus.skipped_count}</span>
                </div>
                {scanStatus.current_file && (
                  <div className="pt-2 border-t border-zinc-200/60 text-zinc-500 truncate">
                    <span className="text-zinc-400">Current: </span>
                    <span className="font-mono text-[11px] text-zinc-700">{scanStatus.current_file}</span>
                  </div>
                )}
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="button"
                  onClick={handleCancel}
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-xl transition-colors cursor-pointer"
                >
                  <StopCircle className="w-4 h-4" />
                  <span>Stop Scan</span>
                </button>
              </div>
            </div>
          ) : (
            /* Input Form */
            <form onSubmit={handleStartScan} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-700 mb-1.5">
                  Folder Directory Path
                </label>
                <input
                  type="text"
                  placeholder="e.g. C:\Users\dhruvil\Pictures"
                  value={folderPath}
                  onChange={(e) => setFolderPath(e.target.value)}
                  className="w-full text-sm px-3.5 py-2.5 border border-zinc-200 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-900 bg-zinc-50/50"
                  required
                />
              </div>

              {/* Quick Pick Shortcuts */}
              <div>
                <span className="block text-[11px] font-medium text-zinc-400 mb-1.5">Quick presets:</span>
                <div className="flex flex-wrap gap-2">
                  {quickFolders.map((f) => (
                    <button
                      key={f.label}
                      type="button"
                      onClick={() => setFolderPath(f.path)}
                      className="text-xs px-2.5 py-1 bg-zinc-100 hover:bg-zinc-200 text-zinc-600 rounded-lg transition-colors cursor-pointer"
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Force Rescan Checkbox */}
              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="forceRescan"
                  checked={forceRescan}
                  onChange={(e) => setForceRescan(e.target.checked)}
                  className="rounded text-zinc-900 focus:ring-0 cursor-pointer"
                />
                <label htmlFor="forceRescan" className="text-xs text-zinc-600 cursor-pointer select-none">
                  Force re-generation of existing thumbnails
                </label>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end gap-3 pt-3 border-t border-zinc-100">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-100 rounded-xl transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || !folderPath.trim()}
                  className="inline-flex items-center gap-1.5 px-5 py-2 text-sm font-medium text-white bg-zinc-900 hover:bg-zinc-800 disabled:opacity-50 rounded-xl shadow-xs transition-colors cursor-pointer"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span>{loading ? 'Starting...' : 'Start Scan'}</span>
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
