import { useEffect, useRef, useState } from "react";
import api from "../services/api";
import InspectionCategorySelect from "../components/InspectionCategorySelect";
import Sidebar from "../components/Sidebar";

function Camera() {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [category, setCategory] = useState("bottle");
  const [cameraOn, setCameraOn] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const [capturing, setCapturing] = useState(false);
  const [capturedFrame, setCapturedFrame] = useState("");
  const [frameResult, setFrameResult] = useState(null);
  const [cameraInspectionIds, setCameraInspectionIds] = useState([]);
  const [clearingCameraHistory, setClearingCameraHistory] = useState(false);

  useEffect(() => () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
  }, []);

  const startCamera = async () => {
    setCameraError("");
    setCapturedFrame("");
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError(
        "Camera access is not supported in this browser or page context."
      );
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      setCameraOn(true);
      requestAnimationFrame(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      });
    } catch (error) {
      const messages = {
        NotAllowedError:
          "Camera permission was denied. Allow camera access for localhost and try again.",
        NotFoundError: "No camera was found on this device.",
        NotReadableError:
          "The camera is already being used by another application. Close it and try again.",
        SecurityError:
          "Camera access was blocked by browser security settings. Use localhost and allow camera access.",
      };
      setCameraError(
        messages[error.name] || "Camera could not be started."
      );
    }
  };

  const clearCameraHistory = async () => {
    if (!cameraInspectionIds.length) {
      setFrameResult(null);
      return;
    }

    setClearingCameraHistory(true);
    try {
      await Promise.all(
        cameraInspectionIds.map((id) => api.delete(`/inspections/${id}`))
      );
      setCameraInspectionIds([]);
      setFrameResult(null);
      setCameraError("");
    } catch (error) {
      setCameraError(
        error.response?.data?.detail ||
          "Some camera inspections could not be deleted."
      );
    } finally {
      setClearingCameraHistory(false);
    }
  };

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraOn(false);
  };

  const captureFrame = async () => {
    if (!videoRef.current?.videoWidth) return;
    setCapturing(true);
    try {
      const canvas = document.createElement("canvas");
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      canvas.getContext("2d").drawImage(videoRef.current, 0, 0);
      setCapturedFrame(canvas.toDataURL("image/jpeg", 0.92));
      const blob = await new Promise((resolve) =>
        canvas.toBlob(resolve, "image/jpeg", 0.92)
      );
      if (!blob) {
        throw new Error("The camera frame could not be encoded.");
      }
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      videoRef.current.srcObject = null;
      setCameraOn(false);
      const formData = new FormData();
      formData.append("file", blob, `camera-${Date.now()}.jpg`);
      const response = await api.post(
        `/inspections/upload?category=${encodeURIComponent(category)}`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      setFrameResult(response.data);
      setCameraInspectionIds((ids) => [...ids, response.data.inspection_id]);
    } catch (error) {
      setCameraError(
        error.response?.data?.detail || "Camera frame inspection failed."
      );
    } finally {
      setCapturing(false);
    }
  };

  return (
    <div className="dashboard-layout">
      <Sidebar />
      <main className="dashboard-main camera-batch-main">
        <header className="dashboard-header">
          <div>
            <span className="eyebrow">AUTOMATION WORKSPACE</span>
            <h1>Camera Inspection</h1>
            <p>Inspect live frames from a connected camera.</p>
          </div>
        </header>
        <div className="camera-batch-toolbar">
          <InspectionCategorySelect value={category} onChange={setCategory} />
        </div>
        <section className="camera-card">
          <div className="card-heading">
            <span className="eyebrow">CAMERA INTEGRATION SIMULATION</span>
            <h2>Live inspection station</h2>
            <p>
              Use your webcam as a simulated production camera. Captured
              frames use the same AI pipeline as normal uploads.
            </p>
          </div>
          <div className="camera-preview">
            {capturedFrame && (
              <img src={capturedFrame} alt="Captured camera frame" />
            )}
            <video
              ref={videoRef}
              autoPlay
              muted
              playsInline
              style={{ display: cameraOn && !capturedFrame ? "block" : "none" }}
            />
            {!cameraOn && !capturedFrame && (
              <div className="camera-placeholder">Camera feed is stopped</div>
            )}
          </div>
          {cameraError && <div className="camera-error">{cameraError}</div>}
          <div className="camera-actions">
            {!cameraOn ? (
              <button onClick={startCamera}>Start camera</button>
            ) : (
              <button onClick={stopCamera}>Stop camera</button>
            )}
            <button
              onClick={captureFrame}
              disabled={!cameraOn || capturing}
            >
              {capturing ? "Inspecting frame..." : "Capture & inspect"}
            </button>
            <button
              className="camera-clear-button"
              onClick={clearCameraHistory}
              disabled={!cameraInspectionIds.length || clearingCameraHistory}
            >
              {clearingCameraHistory ? "Clearing..." : "Clear camera history"}
            </button>
          </div>
          {cameraInspectionIds.length > 0 && (
            <div className="camera-session-note">
              This session has {cameraInspectionIds.length} saved frame
              inspection(s). Clear camera history removes only these records.
            </div>
          )}
          {frameResult && (
            <div
              className={`camera-result ${
                frameResult.result?.status === "DEFECT" ? "defect" : "good"
              }`}
            >
              <strong>{frameResult.result?.status || "COMPLETED"}</strong>
              <span>
                {frameResult.result?.defects?.length || 0} localized defects
              </span>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default Camera;
