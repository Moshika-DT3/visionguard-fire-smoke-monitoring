/**
 * Handles the localized Video Testing upload, browser preview, and result flow.
 * The server remains authoritative for MP4 validation and mock analysis.
 */
document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#video-upload-form");
  if (!form) {
    return;
  }

  const fileInput = document.querySelector("#video-file");
  const uploadButton = document.querySelector("#upload-button");
  const analyzeButton = document.querySelector("#analyze-button");
  const errorMessage = document.querySelector("#upload-error");
  const selectedFilename = document.querySelector("#selected-filename");
  const previewContainer = document.querySelector("#preview-container");
  const videoPreview = document.querySelector("#video-preview");
  const uploadedFilename = document.querySelector("#uploaded-filename");
  const emptyResult = document.querySelector("#analysis-empty");
  const result = document.querySelector("#analysis-result");
  const outcomeBadge = document.querySelector("#outcome-badge");
  const confidenceRow = document.querySelector("#confidence-row");
  const fields = {
    filename: document.querySelector("#result-filename"),
    outcome: document.querySelector("#result-outcome"),
    confidence: document.querySelector("#result-confidence"),
    status: document.querySelector("#result-status"),
    provider: document.querySelector("#result-provider"),
    incident: document.querySelector("#result-incident"),
    note: document.querySelector("#result-note"),
  };

  let uploadedVideo = null;

  const showError = (message) => {
    errorMessage.textContent = message;
    errorMessage.hidden = false;
  };

  const clearError = () => {
    errorMessage.textContent = "";
    errorMessage.hidden = true;
  };

  fileInput.addEventListener("change", () => {
    const selectedFile = fileInput.files[0];
    selectedFilename.textContent = selectedFile
      ? `Selected: ${selectedFile.name}`
      : "No file selected.";
    clearError();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const selectedFile = fileInput.files[0];

    if (!selectedFile) {
      showError("Please select an MP4 video file.");
      return;
    }
    if (!selectedFile.name.toLowerCase().endsWith(".mp4")) {
      showError("Only MP4 video files are supported.");
      return;
    }

    clearError();
    uploadButton.disabled = true;
    uploadButton.textContent = "Uploading…";

    try {
      const payload = new FormData();
      payload.append("file", selectedFile);
      const response = await fetch("/api/video-tests/upload", {
        method: "POST",
        body: payload,
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "The video could not be uploaded.");
      }

      uploadedVideo = data;
      videoPreview.src = data.preview_url;
      uploadedFilename.textContent = `Uploaded filename: ${data.filename}`;
      previewContainer.hidden = false;
      emptyResult.hidden = false;
      result.hidden = true;
      analyzeButton.disabled = false;
    } catch (error) {
      showError(error.message || "The video could not be uploaded.");
    } finally {
      uploadButton.disabled = false;
      uploadButton.textContent = "Upload video";
    }
  });

  analyzeButton.addEventListener("click", async () => {
    if (!uploadedVideo) {
      showError("Upload an MP4 video before running analysis.");
      return;
    }

    clearError();
    analyzeButton.disabled = true;
    analyzeButton.textContent = "Analyzing…";

    try {
      const response = await fetch(
        `/api/video-tests/${encodeURIComponent(uploadedVideo.video_id)}/analyze?filename=${encodeURIComponent(uploadedVideo.filename)}`,
        { method: "POST" },
      );
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Analysis could not be completed.");
      }

      const outcomeLabels = {
        fire: "Fire",
        smoke: "Smoke",
        no_detection: "No Detection",
      };
      const isPositive = data.outcome !== "no_detection";

      outcomeBadge.className = `badge ${data.outcome === "no_detection" ? "no-detection" : data.outcome}`;
      outcomeBadge.textContent = outcomeLabels[data.outcome];
      fields.filename.textContent = data.filename;
      fields.outcome.textContent = outcomeLabels[data.outcome];
      fields.confidence.textContent = data.confidence === null
        ? "Not applicable"
        : `${Math.round(data.confidence * 100)}%`;
      fields.status.textContent = data.status;
      fields.provider.textContent = data.provider;
      fields.incident.textContent = data.incident_created
        ? "Created and visible in Dashboard / Incident History"
        : (isPositive ? "Already created for this video this session" : "No incident created");
      confidenceRow.hidden = data.confidence === null;
      fields.note.className = `result-note ${isPositive ? "positive" : "clear"}`;
      fields.note.textContent = isPositive
        ? "Positive result generated by filename-only Mock Video Analysis; no ML inference was performed."
        : "Analysis completed successfully. No incident was created.";
      emptyResult.hidden = true;
      result.hidden = false;
    } catch (error) {
      showError(error.message || "Analysis could not be completed.");
    } finally {
      analyzeButton.disabled = false;
      analyzeButton.textContent = "Run Mock Analysis";
    }
  });
});
