import React, { useState } from 'react';
import { Calendar, User, Eye } from 'lucide-react';

export default function ImageCard({ image, onClick }) {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);

  const thumbUrl = `/thumbnail/${image.id}`;

  const formattedDate = image.date_taken
    ? new Date(image.date_taken).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : null;

  return (
    <div
      onClick={() => onClick(image)}
      className="group relative cursor-pointer overflow-hidden rounded-xl bg-zinc-100 border border-zinc-200/70 shadow-xs hover:shadow-md transition-all duration-300 transform hover:-translate-y-0.5 aspect-square"
    >
      {/* Loading Skeleton */}
      {!loaded && !error && (
        <div className="absolute inset-0 bg-zinc-200/80 animate-pulse" />
      )}

      {/* Image Thumbnail */}
      <img
        src={thumbUrl}
        alt={image.original_path.split('/').pop()}
        loading="lazy"
        onLoad={() => setLoaded(true)}
        onError={() => {
          setLoaded(true);
          setError(true);
        }}
        className={`w-full h-full object-cover transition-all duration-500 group-hover:scale-105 ${
          loaded ? 'opacity-100' : 'opacity-0'
        }`}
      />

      {/* Error fallback */}
      {error && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-zinc-100 text-zinc-400 p-2 text-center text-xs">
          <span>Failed to load thumbnail</span>
        </div>
      )}

      {/* Subtle overlay on hover */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex flex-col justify-end p-3">
        <div className="flex items-center justify-between text-white text-xs font-medium">
          <span className="truncate max-w-[80%] drop-shadow-sm">
            {image.original_path.split('/').pop() || image.original_path.split('\\').pop()}
          </span>
          <span className="p-1 rounded-full bg-white/20 backdrop-blur-xs">
            <Eye className="w-3.5 h-3.5" />
          </span>
        </div>
      </div>

      {/* Capture Date Badge */}
      {formattedDate && (
        <div className="absolute top-2 left-2 bg-black/40 backdrop-blur-md text-white text-[10px] font-medium px-2 py-0.5 rounded-full flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <Calendar className="w-2.5 h-2.5" />
          <span>{formattedDate}</span>
        </div>
      )}
    </div>
  );
}
