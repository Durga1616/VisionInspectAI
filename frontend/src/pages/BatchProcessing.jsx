import { useEffect, useMemo, useState } from "react";
import api from "../services/api";
import InspectionCategorySelect from "../components/InspectionCategorySelect";
import Sidebar from "../components/Sidebar";

function BatchProcessing() {
  const [category, setCategory] = useState("bottle");
  const [batchFiles, setBatchFiles] = useState([]);
  const [batchRunning, setBatchRunning] = useState(false);
  const [batchResult, setBatchResult] = useState(null);

  const processBatch = async () => {
    if (!batchFiles.length) return;
    setBatchRunning(true);
    setBatchResult(null);
    try {
      const formData = new FormData();
      batchFiles.forEach((file) => formData.append("files", file));
      const response = await api.post(
        `/inspections/batch-upload?category=${encodeURIComponent(category)}`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      setBatchResult(response.data);
    } catch (error) {
      setBatchResult({
        error: error.response?.data?.detail || "Batch processing failed.",
      });
    } finally {
      setBatchRunning(false);
    }
  };

  return (
    <div className="dashboard-layout">
      <Sidebar />
      <main className="dashboard-main camera-batch-main">
        <header className="dashboard-header">
          <div>
            <span className="eyebrow">AUTOMATION WORKSPACE</span>
            <h1>Batch Processing</h1>
            <p>Inspect multiple product images in a single run.</p>
          </div>
        </header>
        <div className="camera-batch-toolbar">
          <InspectionCategorySelect value={category} onChange={setCategory} />
        </div>
        <section className="camera-card batch-processing-card">
          <div className="card-heading">
            <span className="eyebrow">BATCH IMAGE PROCESSING</span>
            <h2>Inspect multiple images</h2>
            <p>
              Select up to 50 JPG, PNG, or WEBP images. Each image gets its own
              inspection record and result.
            </p>
          </div>
          <input
            className="batch-file-input"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            multiple
            onChange={(event) => {
              setBatchFiles(Array.from(event.target.files || []));
              setBatchResult(null);
            }}
          />
          <div className="batch-count">
            {batchFiles.length
              ? `${batchFiles.length} image(s) selected`
              : "No images selected"}
          </div>
          <button
            onClick={processBatch}
            disabled={!batchFiles.length || batchRunning}
          >
            {batchRunning ? "Processing batch..." : "Start batch inspection"}
          </button>
          {batchResult?.error && (
            <div className="camera-error">
              <strong>Batch processing failed</strong>
              <span>{batchResult.error}</span>
            </div>
          )}
          {batchResult?.results && (
            <div className="batch-output">
              <div className="batch-summary">
                <strong>
                  {batchResult.completed} completed / {batchResult.failed} failed
                </strong>
                <span className="batch-output-hint">
                  All uploaded images and YOLO localization results
                </span>
              </div>
              <div className="batch-results-grid">
                {batchResult.results.map((item) => (
                  <BatchResultCard
                    item={item}
                    file={batchFiles.find(
                      (candidate) => candidate.name === item.filename
                    )}
                    key={`${item.inspection_id || item.filename}-${item.status}`}
                  />
                ))}
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

function BatchResultCard({ item, file }) {
  const imageUrl = useMemo(
    () => (file ? URL.createObjectURL(file) : null),
    [file]
  );
  const [imageSize, setImageSize] = useState(null);
  const defects = Array.isArray(item.result?.defects) ? item.result.defects : [];

  useEffect(() => {
    return () => {
      if (imageUrl) URL.revokeObjectURL(imageUrl);
    };
  }, [imageUrl]);

  if (!file || !imageUrl) {
    return (
      <div className="batch-image-missing">
        Original image is unavailable for preview.
      </div>
    );
  }

  return (
    <article className="batch-result-card">
      <div className="batch-viewer-heading">
        <strong>{item.filename}</strong>
        <span className={item.result?.status === "DEFECT" ? "text-defect" : "text-good"}>
          {item.result?.status || item.status}
        </span>
      </div>
      <div className="batch-image-stage">
        <img
          src={imageUrl}
          alt={`Batch result ${item.filename}`}
          onLoad={(event) =>
            setImageSize({
              width: event.currentTarget.naturalWidth,
              height: event.currentTarget.naturalHeight,
            })
          }
        />
        {defects.map((defect, index) => {
          const box = defect.bbox;
          if (!box || !imageSize) return null;
          const x1 = Math.max(0, Number(box.x1) || 0);
          const y1 = Math.max(0, Number(box.y1) || 0);
          const x2 = Math.max(x1, Number(box.x2) || 0);
          const y2 = Math.max(y1, Number(box.y2) || 0);
          return (
            <div
              className="batch-image-box"
              key={`${item.inspection_id}-${index}`}
              style={{
                left: `${(x1 / imageSize.width) * 100}%`,
                top: `${(y1 / imageSize.height) * 100}%`,
                width: `${((x2 - x1) / imageSize.width) * 100}%`,
                height: `${((y2 - y1) / imageSize.height) * 100}%`,
              }}
            >
              <span>
                {defect.defect_type || "DEFECT"}{" "}
                {defect.confidence !== undefined
                  ? `${(defect.confidence * 100).toFixed(1)}%`
                  : ""}
              </span>
            </div>
          );
        })}
      </div>
      <div className="batch-card-footer">
        <span>
          {defects.length} YOLO box{defects.length === 1 ? "" : "es"}
        </span>
        {item.result?.quality_assessment?.severity?.level && (
          <span>{item.result.quality_assessment.severity.level} severity</span>
        )}
      </div>
      {item.result?.status === "DEFECT" && defects.length === 0 && (
        <div className="batch-image-missing">
          Autoencoder detected a defect, but YOLO returned no localization.
        </div>
      )}
    </article>
  );
}

export default BatchProcessing;
