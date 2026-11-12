import React, { useState } from 'react';
import { User, Sparkles, Edit2, Check, X, ArrowLeft, Image as ImageIcon } from 'lucide-react';
import { updatePersonName } from '../api';

export default function PeopleGrid({
  people,
  loading,
  onSelectPerson,
  selectedPerson,
  onBackToPeople,
  onTriggerFaceProcessing,
  faceStatus,
  personImages,
  onImageClick,
}) {
  const [editingId, setEditingId] = useState(null);
  const [editingName, setEditingName] = useState('');
  const [saving, setSaving] = useState(false);

  const handleStartRename = (e, person) => {
    e.stopPropagation();
    setEditingId(person.id);
    setEditingName(person.name);
  };

  const handleSaveRename = async (e, personId) => {
    e.stopPropagation();
    if (!editingName.trim()) return;
    setSaving(true);
    try {
      await updatePersonName(personId, editingName.trim());
      const p = people.find((x) => x.id === personId);
      if (p) p.name = editingName.trim();
      setEditingId(null);
    } catch (err) {
      alert('Failed to rename person: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleCancelRename = (e) => {
    e.stopPropagation();
    setEditingId(null);
  };

  // If a specific person is selected, show their photos
  if (selectedPerson) {
    return (
      <div className="w-full">
        {/* Person Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8 bg-white p-6 rounded-2xl border border-zinc-200/80 shadow-xs">
          <div className="flex items-center gap-4">
            <button
              onClick={onBackToPeople}
              className="p-2.5 rounded-xl hover:bg-zinc-100 text-zinc-600 transition-colors cursor-pointer"
              title="Back to all people"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div className="w-14 h-14 rounded-full overflow-hidden bg-zinc-100 border-2 border-indigo-500/20 shrink-0">
              {selectedPerson.profile_face_path ? (
                <img
                  src={`/person-face/${selectedPerson.id}`}
                  alt={selectedPerson.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-zinc-400">
                  <User className="w-6 h-6" />
                </div>
              )}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-zinc-900">{selectedPerson.name}</h2>
              <p className="text-sm text-zinc-500 font-medium">
                {selectedPerson.image_count} {selectedPerson.image_count === 1 ? 'photo' : 'photos'} identified
              </p>
            </div>
          </div>
        </div>

        {/* Photos Grid for this person */}
        {personImages && personImages.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 sm:gap-4">
            {personImages.map((image) => (
              <div
                key={image.id}
                onClick={() => onImageClick(image)}
                className="group relative cursor-pointer overflow-hidden rounded-xl bg-zinc-100 border border-zinc-200/70 shadow-xs hover:shadow-md transition-all duration-300 transform hover:-translate-y-0.5 aspect-square"
              >
                <img
                  src={`/thumbnail/${image.id}`}
                  alt="Thumbnail"
                  loading="lazy"
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                />
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16 text-zinc-400">
            <p>No photos found for this person.</p>
          </div>
        )}
      </div>
    );
  }

  // All People Grid View
  return (
    <div className="w-full">
      {/* People Header & AI Trigger Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-xl font-bold text-zinc-900">Recognized People</h2>
          <p className="text-sm text-zinc-500">
            Automatically grouped by local facial recognition and clustering.
          </p>
        </div>
        <button
          onClick={onTriggerFaceProcessing}
          disabled={faceStatus?.is_processing}
          className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium text-sm transition-all shadow-xs cursor-pointer ${
            faceStatus?.is_processing
              ? 'bg-indigo-50 text-indigo-600 border border-indigo-200 animate-pulse'
              : 'bg-indigo-600 hover:bg-indigo-700 text-white'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>{faceStatus?.is_processing ? 'Processing Faces...' : 'Run Face Recognition'}</span>
        </button>
      </div>

      {/* Progress banner if face job running */}
      {faceStatus?.is_processing && (
        <div className="mb-6 p-4 rounded-xl bg-indigo-50/80 border border-indigo-100 flex items-center justify-between text-indigo-900 text-sm">
          <div>
            <span className="font-semibold">AI Grouping in progress:</span>{' '}
            Processed {faceStatus.processed_count} of {faceStatus.total_unprocessed} images. Detected{' '}
            {faceStatus.faces_detected_count} faces across {faceStatus.people_count} unique people.
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && people.length === 0 && (
        <div className="flex flex-col items-center justify-center min-h-[50vh] text-center p-8 bg-white rounded-2xl border border-zinc-200/80 shadow-xs">
          <div className="w-16 h-16 rounded-2xl bg-indigo-50 flex items-center justify-center mb-4 text-indigo-500">
            <User className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-semibold text-zinc-800 mb-1">No people recognized yet</h3>
          <p className="text-zinc-500 text-sm max-w-sm mb-5">
            Click "Run Face Recognition" to let local AI detect faces in your indexed photos and group them by person.
          </p>
          <button
            onClick={onTriggerFaceProcessing}
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm px-5 py-2.5 rounded-xl shadow-xs transition-colors cursor-pointer"
          >
            <Sparkles className="w-4 h-4" />
            <span>Start Face Recognition</span>
          </button>
        </div>
      )}

      {/* People Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
        {people.map((person) => (
          <div
            key={person.id}
            onClick={() => onSelectPerson(person)}
            className="group relative bg-white hover:bg-zinc-50 border border-zinc-200/80 hover:border-zinc-300 rounded-2xl p-4 flex flex-col items-center text-center transition-all duration-200 shadow-xs hover:shadow-md cursor-pointer"
          >
            {/* Avatar Circle */}
            <div className="w-20 h-20 rounded-full overflow-hidden bg-zinc-100 border-2 border-zinc-200/60 group-hover:border-indigo-400/50 mb-3 shadow-xs transition-colors">
              {person.profile_face_path ? (
                <img
                  src={`/person-face/${person.id}`}
                  alt={person.name}
                  loading="lazy"
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-zinc-400">
                  <User className="w-8 h-8" />
                </div>
              )}
            </div>

            {/* Name / Rename Input */}
            {editingId === person.id ? (
              <div className="flex items-center gap-1 w-full mt-1" onClick={(e) => e.stopPropagation()}>
                <input
                  type="text"
                  value={editingName}
                  onChange={(e) => setEditingName(e.target.value)}
                  className="w-full text-xs font-semibold px-2 py-1 border border-zinc-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-indigo-500 bg-white"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSaveRename(e, person.id);
                    if (e.key === 'Escape') handleCancelRename(e);
                  }}
                />
                <button
                  onClick={(e) => handleSaveRename(e, person.id)}
                  disabled={saving}
                  className="p-1 rounded-md bg-emerald-50 text-emerald-600 hover:bg-emerald-100"
                >
                  <Check className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={handleCancelRename}
                  className="p-1 rounded-md bg-zinc-100 text-zinc-500 hover:bg-zinc-200"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <div className="flex items-center justify-center gap-1.5 w-full mt-1">
                <span className="font-semibold text-sm text-zinc-900 truncate max-w-[120px]">
                  {person.name}
                </span>
                <button
                  onClick={(e) => handleStartRename(e, person)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-zinc-400 hover:text-zinc-700 transition-opacity rounded-md"
                  title="Rename Person"
                >
                  <Edit2 className="w-3 h-3" />
                </button>
              </div>
            )}

            {/* Photo count badge */}
            <span className="text-xs text-zinc-500 font-medium mt-0.5">
              {person.image_count} {person.image_count === 1 ? 'photo' : 'photos'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
