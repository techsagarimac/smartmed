import { useEffect, useRef, useState } from "react";

export function CameraCapture({ onCapture, disabled }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [error, setError] = useState("");
  const [ready, setReady] = useState(false);
  const [usingUserFacing, setUsingUserFacing] = useState(false);

  async function start(facingMode) {
    stop();
    setError("");
    setReady(false);
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("This browser does not support camera access. Upload a photo of the package instead.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: facingMode || (usingUserFacing ? "user" : "environment"), width: { ideal: 1280 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        try {
          await videoRef.current.play();
        } catch (playError) {
          if (playError.name !== "AbortError") {
            throw playError;
          }
        }
        if (streamRef.current === stream) {
          setReady(true);
        }
      }
    } catch (err) {
      if (err.name === "AbortError") {
        return;
      }
      if (err.name === "NotAllowedError") {
        setError("Camera permission was denied. Allow camera access, or upload a photo instead.");
      } else if (err.name === "NotFoundError") {
        setError("No camera was found on this device. Upload a photo of the medicine package instead.");
      } else {
        setError(err.message || "Camera is unavailable. Upload a photo instead.");
      }
    }
  }

  function stop() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setReady(false);
  }

  useEffect(() => {
    start("environment");
    return stop;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function capture() {
    const video = videoRef.current;
    if (!video || !ready) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          setError("Could not capture a frame from the camera. Try again or upload a photo.");
          return;
        }
        onCapture(blob);
      },
      "image/jpeg",
      0.92,
    );
  }

  return (
    <div className="camera-wrap">
      <video ref={videoRef} className="camera-video" playsInline muted autoPlay />
      {!ready && !error ? <div className="camera-overlay">Starting camera…</div> : null}
      {error ? (
        <div className="banner banner-danger camera-error" role="alert">
          {error}
        </div>
      ) : null}
      <div className="camera-actions">
        <button type="button" className="btn btn-primary" onClick={capture} disabled={disabled || !ready}>
          Capture package
        </button>
        <button
          type="button"
          className="btn btn-ghost"
          onClick={() => {
            const next = !usingUserFacing;
            setUsingUserFacing(next);
            start(next ? "user" : "environment");
          }}
        >
          Flip camera
        </button>
      </div>
    </div>
  );
}
