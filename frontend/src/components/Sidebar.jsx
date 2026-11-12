import React from 'react';
import {
  Images,
  Users,
  FolderPlus,
  Sparkles,
  RefreshCw,
  HardDrive,
} from 'lucide-react';

export default function Sidebar({
  activeTab,
  setActiveTab,
  totalImages,
  totalPeople,
  onOpenScanModal,
  onTriggerFaceProcessing,
  faceStatus,
  scanStatus,
  onRefresh,
}) {
  return (
    <aside className="w-64 bg-white border-r border-zinc-200/80 flex flex-col justify-between shrink-0 h-screen sticky top-0">
      {/* Brand & Title */}
      <div>
        <div className="p-6 border-b border-zinc-100 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-zinc-900 text-white flex items-center justify-center shadow-xs">
              <Images className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-base text-zinc-900 leading-tight">PC Gallery</h1>
              <span className="text-[11px] font-medium text-zinc-400">Local AI Photo Engine</span>
            </div>
          </div>
          <button
            onClick={onRefresh}
            className="p-2 rounded-xl text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 transition-colors cursor-pointer"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <nav className="p-4 space-y-1.5">
          <button
            onClick={() => setActiveTab('photos')}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all cursor-pointer ${
              activeTab === 'photos'
                ? 'bg-zinc-900 text-white shadow-xs'
                : 'text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900'
            }`}
          >
            <div className="flex items-center gap-3">
              <Images className="w-4 h-4" />
              <span>All Photos</span>
            </div>
            {totalImages > 0 && (
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                  activeTab === 'photos'
                    ? 'bg-zinc-800 text-zinc-300'
                    : 'bg-zinc-100 text-zinc-500'
                }`}
              >
                {totalImages}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('people')}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all cursor-pointer ${
              activeTab === 'people'
                ? 'bg-zinc-900 text-white shadow-xs'
                : 'text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900'
            }`}
          >
            <div className="flex items-center gap-3">
              <Users className="w-4 h-4" />
              <span>People</span>
            </div>
            {totalPeople > 0 && (
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                  activeTab === 'people'
                    ? 'bg-zinc-800 text-zinc-300'
                    : 'bg-zinc-100 text-zinc-500'
                }`}
              >
                {totalPeople}
              </span>
            )}
          </button>
        </nav>
      </div>

      {/* Bottom Actions & Status Card */}
      <div className="p-4 space-y-3 border-t border-zinc-100 bg-zinc-50/50">
        {/* Scan Status Pill */}
        {scanStatus?.is_scanning && (
          <div className="bg-zinc-900 text-white p-3 rounded-xl text-xs space-y-1 animate-pulse">
            <div className="flex justify-between font-medium">
              <span>Scanning Folder...</span>
              <span>
                {Math.round((scanStatus.processed_files / (scanStatus.total_files || 1)) * 100)}%
              </span>
            </div>
            <p className="text-[11px] text-zinc-400 truncate">{scanStatus.current_file}</p>
          </div>
        )}

        {/* Face Status Pill */}
        {faceStatus?.is_processing && (
          <div className="bg-indigo-600 text-white p-3 rounded-xl text-xs space-y-1 animate-pulse">
            <div className="flex items-center justify-between font-medium">
              <span className="flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" />
                AI Grouping...
              </span>
              <span>
                {faceStatus.processed_count}/{faceStatus.total_unprocessed}
              </span>
            </div>
          </div>
        )}

        <button
          onClick={onOpenScanModal}
          className="w-full flex items-center justify-center gap-2 bg-white hover:bg-zinc-100 text-zinc-800 border border-zinc-200/90 font-medium text-xs py-2.5 rounded-xl shadow-2xs transition-colors cursor-pointer"
        >
          <FolderPlus className="w-4 h-4 text-zinc-600" />
          <span>Scan Local Folder</span>
        </button>

        <button
          onClick={onTriggerFaceProcessing}
          disabled={faceStatus?.is_processing}
          className="w-full flex items-center justify-center gap-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200/70 font-medium text-xs py-2.5 rounded-xl transition-colors cursor-pointer disabled:opacity-60"
        >
          <Sparkles className="w-4 h-4 text-indigo-600" />
          <span>{faceStatus?.is_processing ? 'AI Grouping Active...' : 'AI Face Grouping'}</span>
        </button>
      </div>
    </aside>
  );
}
