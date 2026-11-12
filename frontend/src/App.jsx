import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import ImageGrid from './components/ImageGrid';
import PeopleGrid from './components/PeopleGrid';
import LightboxModal from './components/LightboxModal';
import ScanModal from './components/ScanModal';
import {
  fetchImages,
  fetchPeople,
  fetchImagesByPerson,
  getScanStatus,
  getFaceStatus,
  triggerFaceProcessing,
} from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('photos'); // 'photos' | 'people'
  const [images, setImages] = useState([]);
  const [totalImages, setTotalImages] = useState(0);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);

  // People View State
  const [people, setPeople] = useState([]);
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [personImages, setPersonImages] = useState([]);
  const [loadingPeople, setLoadingPeople] = useState(false);

  // Lightbox Modal State
  const [lightboxImage, setLightboxImage] = useState(null);

  // Scan & Face Processing State
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);
  const [scanStatus, setScanStatus] = useState(null);
  const [faceStatus, setFaceStatus] = useState(null);

  // -------------------------------------------------------------
  // Data Fetching: Images
  // -------------------------------------------------------------
  const loadImages = useCallback(async (pageNum = 1, append = false) => {
    setLoading(true);
    try {
      const data = await fetchImages(pageNum, 50);
      if (append) {
        setImages((prev) => [...prev, ...data.items]);
      } else {
        setImages(data.items);
      }
      setTotalImages(data.total);
      setHasMore(data.has_next);
      setPage(pageNum);
    } catch (err) {
      console.error('Error fetching images:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // -------------------------------------------------------------
  // Data Fetching: People
  // -------------------------------------------------------------
  const loadPeople = useCallback(async () => {
    setLoadingPeople(true);
    try {
      const data = await fetchPeople(0, 100);
      setPeople(data);
    } catch (err) {
      console.error('Error fetching people:', err);
    } finally {
      setLoadingPeople(false);
    }
  }, []);

  // -------------------------------------------------------------
  // Load Person's specific photos
  // -------------------------------------------------------------
  const handleSelectPerson = async (person) => {
    setSelectedPerson(person);
    try {
      const data = await fetchImagesByPerson(person.id, 1, 100);
      setPersonImages(data.items);
    } catch (err) {
      console.error('Error fetching person photos:', err);
    }
  };

  // Initial data load
  useEffect(() => {
    loadImages(1, false);
    loadPeople();
  }, [loadImages, loadPeople]);

  // -------------------------------------------------------------
  // Background Status Polling (Scanner & AI Face Engine)
  // -------------------------------------------------------------
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const sStatus = await getScanStatus();
        setScanStatus(sStatus);
        if (sStatus.is_scanning) {
          // While scanning, silently refresh image count
          loadImages(1, false);
        }

        const fStatus = await getFaceStatus();
        setFaceStatus(fStatus);
        if (fStatus.is_processing) {
          loadPeople();
        }
      } catch (e) {
        // Ignore polling errors
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [loadImages, loadPeople]);

  // -------------------------------------------------------------
  // Face Processing Trigger
  // -------------------------------------------------------------
  const handleTriggerFaceProcessing = async () => {
    try {
      await triggerFaceProcessing();
      const status = await getFaceStatus();
      setFaceStatus(status);
    } catch (err) {
      alert('Face recognition notice: ' + err.message);
    }
  };

  // -------------------------------------------------------------
  // Lightbox Navigation
  // -------------------------------------------------------------
  const currentImagesList = selectedPerson ? personImages : images;
  const currentIndex = lightboxImage
    ? currentImagesList.findIndex((x) => x.id === lightboxImage.id)
    : -1;

  const handleNextPhoto = () => {
    if (currentIndex >= 0 && currentIndex < currentImagesList.length - 1) {
      setLightboxImage(currentImagesList[currentIndex + 1]);
    }
  };

  const handlePrevPhoto = () => {
    if (currentIndex > 0) {
      setLightboxImage(currentImagesList[currentIndex - 1]);
    }
  };

  const handleImageDeleted = (deletedId) => {
    setImages((prev) => prev.filter((img) => img.id !== deletedId));
    setPersonImages((prev) => prev.filter((img) => img.id !== deletedId));
    setTotalImages((prev) => Math.max(0, prev - 1));
  };

  return (
    <div className="flex min-h-screen bg-[#FAFAFA] text-zinc-900 selection:bg-zinc-900 selection:text-white">
      {/* Left Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setActiveTab(tab);
          if (tab === 'people') {
            setSelectedPerson(null);
            loadPeople();
          }
        }}
        totalImages={totalImages}
        totalPeople={people.length}
        onOpenScanModal={() => setIsScanModalOpen(true)}
        onTriggerFaceProcessing={handleTriggerFaceProcessing}
        faceStatus={faceStatus}
        scanStatus={scanStatus}
        onRefresh={() => {
          loadImages(1, false);
          loadPeople();
        }}
      />

      {/* Main Content Area */}
      <main className="flex-1 p-6 sm:p-10 max-w-7xl mx-auto overflow-y-auto">
        {activeTab === 'photos' && (
          <div>
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-2xl font-bold text-zinc-900">All Photos</h2>
                <p className="text-sm text-zinc-500 font-medium">
                  {totalImages} {totalImages === 1 ? 'photo' : 'photos'} indexed on local PC
                </p>
              </div>
            </div>

            <ImageGrid
              images={images}
              total={totalImages}
              loading={loading}
              hasMore={hasMore}
              onLoadMore={() => {
                if (!loading && hasMore) {
                  loadImages(page + 1, true);
                }
              }}
              onImageClick={(img) => setLightboxImage(img)}
              onOpenScanModal={() => setIsScanModalOpen(true)}
            />
          </div>
        )}

        {activeTab === 'people' && (
          <PeopleGrid
            people={people}
            loading={loadingPeople}
            onSelectPerson={handleSelectPerson}
            selectedPerson={selectedPerson}
            onBackToPeople={() => setSelectedPerson(null)}
            onTriggerFaceProcessing={handleTriggerFaceProcessing}
            faceStatus={faceStatus}
            personImages={personImages}
            onImageClick={(img) => setLightboxImage(img)}
          />
        )}
      </main>

      {/* Lightbox Fullscreen Modal */}
      {lightboxImage && (
        <LightboxModal
          image={lightboxImage}
          onClose={() => setLightboxImage(null)}
          onNext={handleNextPhoto}
          onPrev={handlePrevPhoto}
          hasNext={currentIndex < currentImagesList.length - 1}
          hasPrev={currentIndex > 0}
          onImageDeleted={handleImageDeleted}
        />
      )}

      {/* Scan Folder Modal */}
      <ScanModal
        isOpen={isScanModalOpen}
        onClose={() => setIsScanModalOpen(false)}
        scanStatus={scanStatus}
        onScanStarted={() => {
          loadImages(1, false);
        }}
      />
    </div>
  );
}
