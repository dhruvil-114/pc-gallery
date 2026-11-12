import React, { useEffect, useRef } from 'react';
import ImageCard from './ImageCard';
import { Image as ImageIcon, FolderPlus, Loader2 } from 'lucide-react';

export default function ImageGrid({
  images,
  total,
  loading,
  hasMore,
  onLoadMore,
  onImageClick,
  onOpenScanModal,
}) {
  const loadMoreRef = useRef(null);

  useEffect(() => {
    if (!hasMore || loading) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          onLoadMore();
        }
      },
      { rootMargin: '400px' }
    );

    if (loadMoreRef.current) {
      observer.observe(loadMoreRef.current);
    }

    return () => observer.disconnect();
  }, [hasMore, loading, onLoadMore]);

  if (!loading && images.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-8">
        <div className="w-16 h-16 rounded-2xl bg-zinc-100 flex items-center justify-center mb-4 text-zinc-400">
          <ImageIcon className="w-8 h-8" />
        </div>
        <h3 className="text-xl font-semibold text-zinc-800 mb-2">No photos indexed yet</h3>
        <p className="text-zinc-500 text-sm max-w-sm mb-6">
          Scan a folder on your computer to instantly generate thumbnails and organize your photos with local AI.
        </p>
        <button
          onClick={onOpenScanModal}
          className="inline-flex items-center gap-2 bg-zinc-900 hover:bg-zinc-800 text-white font-medium text-sm px-5 py-2.5 rounded-xl shadow-sm transition-all duration-200 cursor-pointer"
        >
          <FolderPlus className="w-4 h-4" />
          <span>Scan Folder</span>
        </button>
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* Photo Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 sm:gap-4">
        {images.map((image) => (
          <ImageCard
            key={image.id}
            image={image}
            onClick={onImageClick}
          />
        ))}
      </div>

      {/* Infinite Scroll Trigger & Spinner */}
      <div ref={loadMoreRef} className="py-10 flex justify-center items-center w-full">
        {loading && (
          <div className="flex items-center gap-2 text-zinc-400 text-sm font-medium">
            <Loader2 className="w-5 h-5 animate-spin text-zinc-600" />
            <span>Loading photos...</span>
          </div>
        )}
        {!hasMore && images.length > 0 && (
          <p className="text-zinc-400 text-xs font-medium">
            Showing all {images.length} photos
          </p>
        )}
      </div>
    </div>
  );
}
