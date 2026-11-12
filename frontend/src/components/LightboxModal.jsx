import React, { useEffect, useState } from 'react';
import {
  X,
  ChevronLeft,
  ChevronRight,
  Calendar,
  FileText,
  HardDrive,
  Copy,
  Check,
  User,
  Trash2,
  Info,
} from 'lucide-react';
import { fetchImageFaces, deleteImage } from '../api';

export default function LightboxModal({
  image,
  onClose,
  onNext,
  onPrev,
  hasNext,
  hasPrev,
  onImageDeleted,
}) {
  const [faces, setFaces] = useState([]);
  const [copied, setCopied] = useState(false);
  const [showInfo, setShowInfo] = useState(true);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (!image) return;
    fetchImageFaces(image.id)
      .then((data) => setFaces(data || []))
      .catch(() => setFaces([]));
  }, [image?.id]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowRight' && hasNext) onNext();
      if (e.key === 'ArrowLeft' && hasPrev) onPrev();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [hasNext, hasPrev, onClose, onNext, onPrev]);

  if (!image) return null;

  const fileName =
    image.original_path.split('/').pop() || image.original_path.split('\\').pop();

  const formattedDate = image.date_taken
    ? new Date(image.date_taken).toLocaleString(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
      })
    : 'Unknown date';

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown size';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const handleCopyPath = () => {
    navigator.clipboard.writeText(image.original_path);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDelete = async () => {
    if (!window.confirm('Remove this photo from your gallery index?')) return;
    setDeleting(true);
    try {
      await deleteImage(image.id);
      onImageDeleted(image.id);
      onClose();
    } catch (err) {
      alert('Failed to delete image: ' + err.message);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex flex-col justify-between select-none">
      {/* Top Header Bar */}
      <div className="flex items-center justify-between p-4 text-white/90 z-10">
        <div className="flex items-center gap-3">
          <span className="font-medium text-sm truncate max-w-md">{fileName}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowInfo(!showInfo)}
            className={`p-2 rounded-full hover:bg-white/10 transition-colors cursor-pointer ${
              showInfo ? 'text-indigo-400' : 'text-white/80'
            }`}
            title="Toggle details"
          >
            <Info className="w-5 h-5" />
          </button>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="p-2 rounded-full hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-colors cursor-pointer"
            title="Remove from gallery"
          >
            <Trash2 className="w-5 h-5" />
          </button>
          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-white/10 text-white/80 transition-colors cursor-pointer"
            title="Close (Esc)"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
      </div>

      {/* Main Content Area: Image + Navigation Arrows */}
      <div className="relative flex-1 flex items-center justify-center p-4 min-h-0">
        {hasPrev && (
          <button
            onClick={onPrev}
            className="absolute left-6 top-1/2 -translate-y-1/2 p-3 rounded-full bg-black/50 hover:bg-black/80 text-white backdrop-blur-xs transition-all duration-200 hover:scale-110 z-20 cursor-pointer"
            title="Previous (Left arrow)"
          >
            <ChevronLeft className="w-6 h-6" />
          </button>
        )}

        {/* High-res Image */}
        <div className="relative max-w-full max-h-full flex items-center justify-center">
          <img
            src={`/image/${image.id}`}
            alt={fileName}
            className="max-h-[82vh] max-w-[85vw] object-contain rounded-lg shadow-2xl transition-all duration-300 select-none pointer-events-none"
          />
        </div>

        {hasNext && (
          <button
            onClick={onNext}
            className="absolute right-6 top-1/2 -translate-y-1/2 p-3 rounded-full bg-black/50 hover:bg-black/80 text-white backdrop-blur-xs transition-all duration-200 hover:scale-110 z-20 cursor-pointer"
            title="Next (Right arrow)"
          >
            <ChevronRight className="w-6 h-6" />
          </button>
        )}
      </div>

      {/* Slide-out Info Drawer */}
      {showInfo && (
        <div className="bg-zinc-900/90 border-t border-zinc-800 text-zinc-300 p-4 px-6 z-10 flex flex-wrap items-center justify-between gap-4 text-xs font-medium">
          <div className="flex flex-wrap items-center gap-6">
            {/* Capture Date */}
            <div className="flex items-center gap-1.5 text-zinc-400">
              <Calendar className="w-4 h-4 text-zinc-500" />
              <span>{formattedDate}</span>
            </div>

            {/* File Size */}
            <div className="flex items-center gap-1.5 text-zinc-400">
              <HardDrive className="w-4 h-4 text-zinc-500" />
              <span>{formatFileSize(image.file_size)}</span>
            </div>

            {/* Detected Faces */}
            {faces.length > 0 && (
              <div className="flex items-center gap-1.5 bg-indigo-500/10 text-indigo-300 px-2.5 py-1 rounded-full border border-indigo-500/20">
                <User className="w-3.5 h-3.5" />
                <span>
                  {faces.length} {faces.length === 1 ? 'Person tagged' : 'People tagged'}
                </span>
              </div>
            )}
          </div>

          {/* Path copy */}
          <div className="flex items-center gap-2 max-w-md">
            <span className="truncate text-zinc-500 font-mono text-[11px]" title={image.original_path}>
              {image.original_path}
            </span>
            <button
              onClick={handleCopyPath}
              className="p-1.5 rounded-md hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors cursor-pointer shrink-0"
              title="Copy path"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
