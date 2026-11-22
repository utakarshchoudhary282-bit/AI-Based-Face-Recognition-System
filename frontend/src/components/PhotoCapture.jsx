import { useEffect, useRef, useState } from "react";

/** Choose a photo from disk or take one with the webcam. Calls onChange(File | null). */
export default function PhotoCapture({ file, onChange, faceBox }) {
  const [mode, setMode] = useState("upload");
  const [preview, setPreview] = useState(null);
  const [camError, setCamError] = useState("");
  const [natural, setNatural] = useState(null);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    if (!file) {
      setPreview(null);
      return undefined;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  useEffect(() => {
    if (mode !== "camera" || file) return undefined;
    let cancelled = false;
    setCamError("");
    navigator.mediaDevices?.getUserMedia({ video: { facingMode: "user", width: 640, height: 480 } })
      .then((stream) => {
        if (cancelled) return stream.getTracks().forEach((t) => t.stop());
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
      })
      .catch(() => setCamError("Camera not available. Allow camera access or upload a photo instead."));
    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    };
  }, [mode, file]);

  function capture() {
    const v = videoRef.current;
    if (!v?.videoWidth) return;
    const canvas = document.createElement("canvas");
    canvas.width = v.videoWidth;
    canvas.height = v.videoHeight;
    canvas.getContext("2d").drawImage(v, 0, 0);
    canvas.toBlob((blob) => onChange(new File([blob], "webcam.jpg", { type: "image/jpeg" })), "image/jpeg", 0.92);
  }

  // The backend shrinks big images to 1280px on the long side before detecting the face.
  let box = null;
  if (faceBox && natural) {
    const scale = Math.min(1, 1280 / Math.max(natural.w, natural.h));
    const [x, y, w, h] = faceBox;
    const sw = natural.w * scale, sh = natural.h * scale;
    box = { left: `${(x / sw) * 100}%`, top: `${(y / sh) * 100}%`, width: `${(w / sw) * 100}%`, height: `${(h / sh) * 100}%` };
  }

  return (
    <div className="capture">
      <div className="tabs" role="tablist">
        {["upload", "camera"].map((m) => (
          <button key={m} role="tab" aria-selected={mode === m} className={mode === m ? "tab active" : "tab"}
            onClick={() => { setMode(m); onChange(null); }}>
            {m === "upload" ? "Upload photo" : "Use webcam"}
          </button>
        ))}
      </div>
      <div className="stage">
        {preview ? (
          <div className="preview-wrap">
            <img src={preview} alt="Photo to verify" onLoad={(e) => setNatural({ w: e.target.naturalWidth, h: e.target.naturalHeight })} />
            {box && <div className="face-box" style={box} />}
          </div>
        ) : mode === "upload" ? (
          <label className="dropzone"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => { e.preventDefault(); const f = e.dataTransfer.files?.[0]; if (f) onChange(f); }}>
            <input type="file" accept="image/*" hidden onChange={(e) => onChange(e.target.files?.[0] || null)} />
            <strong>Drop a photo here or click to choose</strong>
            <span className="muted">JPG or PNG, one person facing the camera</span>
          </label>
        ) : camError ? (
          <div className="dropzone"><span className="muted">{camError}</span></div>
        ) : (
          <video ref={videoRef} autoPlay playsInline muted className="video" />
        )}
      </div>
      <div className="capture-actions">
        {mode === "camera" && !file && !camError && <button className="btn" onClick={capture}>Capture</button>}
        {file && <button className="btn ghost" onClick={() => onChange(null)}>Retake / change photo</button>}
      </div>
    </div>
  );
}
