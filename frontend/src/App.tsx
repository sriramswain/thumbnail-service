import React, { useRef, useState } from "react";

type Thumbnail = {
  id: string;
  url: string;
  width: number;
  height: number;
  preset: string | null;
  is_preset: boolean;
};

type ImageThumbnails = {
  original_filename: string;
  content_type: string;
  thumbnails: Thumbnail[];
};

type UploadResponse = {
  items: ImageThumbnails[];
};

type FileEntry = {
  id: number;
  file: File;
  preset: string | null;
  width: string;
  height: string;
};

const API_BASE = "http://localhost:8000";

const presetOptions = [
  { id: "small", label: "Small (up to 64×64)" },
  { id: "medium", label: "Medium (up to 256×256)" },
  { id: "large", label: "Large (up to 1024×1024)" },
];

let nextId = 0;

const App: React.FC = () => {
  const [entries, setEntries] = useState<FileEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const addFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    const chosen = e.target.files;
    if (!chosen?.length) return;
    const newEntries: FileEntry[] = Array.from(chosen).map((file) => ({
      id: nextId++,
      file,
      preset: null,
      width: "",
      height: "",
    }));
    setEntries((prev) => [...prev, ...newEntries]);
    setError(null);
    e.target.value = "";
  };

  const removeEntry = (id: number) => {
    setEntries((prev) => prev.filter((e) => e.id !== id));
  };

  const updateEntry = (
    id: number,
    updates: Partial<Pick<FileEntry, "preset" | "width" | "height">>
  ) => {
    setEntries((prev) =>
      prev.map((e) => (e.id === id ? { ...e, ...updates } : e))
    );
  };

  const handleSubmit: React.FormEventHandler<HTMLFormElement> = async (e) => {
    e.preventDefault();
    setError(null);
    setResult(null);

    if (entries.length === 0) {
      setError("Please add at least one image.");
      return;
    }

    setLoading(true);
    const allItems: ImageThumbnails[] = [];

    try {
      for (const entry of entries) {
        const form = new FormData();
        form.append("files", entry.file);

        const params = new URLSearchParams();
        if (entry.preset) params.append("presets", entry.preset);
        if (entry.width) params.append("width", entry.width);
        if (entry.height) params.append("height", entry.height);

        const response = await fetch(
          `${API_BASE}/thumbnails?${params.toString()}`,
          { method: "POST", body: form }
        );

        if (!response.ok) {
          const data = await response.json().catch(() => null);
          const message =
            data?.error?.message ||
            data?.detail?.[0]?.msg ||
            `Request failed for ${entry.file.name} (${response.status})`;
          throw new Error(message);
        }

        const data = (await response.json()) as UploadResponse;
        allItems.push(...data.items);
      }

      setResult({ items: allItems });
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unexpected error occurred"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="header">
        <div>
          <h1 className="title">Thumbnail Service</h1>
          <p className="subtitle">
            Upload images, generate thumbnails with presets or custom sizes, and
            preview the results.
          </p>
        </div>
      </header>

      <main className="content">
        <section className="card">
          <h2 className="card-title">Generate Thumbnails</h2>
          <form className="form" onSubmit={handleSubmit}>
            <div className="form-row">
              <label className="label">Images</label>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                onChange={addFiles}
                className="file-input"
              />
              <p className="hint">
                Choose one or more images; you can click again to add more.
                Max 5MB per image.
              </p>
              {entries.length > 0 && (
                <ul className="file-list">
                  {entries.map((entry) => (
                    <li key={entry.id} className="file-list-item">
                      <span className="file-list-name" title={entry.file.name}>
                        {entry.file.name}
                      </span>
                      <div className="file-list-options">
                        <span className="file-list-label">Preset:</span>
                        <div className="preset-radios">
                          {presetOptions.map((preset) => (
                            <label key={preset.id} className="radio-label">
                              <input
                                type="radio"
                                name={`preset-${entry.id}`}
                                checked={entry.preset === preset.id}
                                onChange={() =>
                                  updateEntry(entry.id, { preset: preset.id })
                                }
                              />
                              <span>{preset.label}</span>
                            </label>
                          ))}
                          <label className="radio-label">
                            <input
                              type="radio"
                              name={`preset-${entry.id}`}
                              checked={entry.preset === null}
                              onChange={() =>
                                updateEntry(entry.id, { preset: null })
                              }
                            />
                            <span>Default (medium)</span>
                          </label>
                        </div>
                        <div className="file-list-custom-wrap">
                          <div className="file-list-custom">
                            <input
                              type="number"
                              min={1}
                              placeholder="Width"
                              value={entry.width}
                              onChange={(e) =>
                                updateEntry(entry.id, { width: e.target.value })
                              }
                              className="custom-input"
                            />
                            <input
                              type="number"
                              min={1}
                              placeholder="Height"
                              value={entry.height}
                              onChange={(e) =>
                                updateEntry(entry.id, { height: e.target.value })
                              }
                              className="custom-input"
                            />
                          </div>
                          <span className="custom-hint">Max size (aspect ratio kept)</span>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeEntry(entry.id)}
                        className="remove-btn"
                        title="Remove"
                      >
                        ×
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <div className="actions">
              <button type="submit" className="button" disabled={loading}>
                {loading ? "Generating..." : "Generate thumbnails"}
              </button>
            </div>
          </form>
        </section>

        {result && (
          <section className="card">
            <h2 className="card-title">Results</h2>
            {result.items.map((item) => (
              <div key={item.original_filename} className="result-group">
                <h3 className="result-title">{item.original_filename}</h3>
                <p className="hint">{item.content_type}</p>
                <div className="thumbnails-grid">
                  {item.thumbnails.map((thumb) => (
                    <div key={thumb.id} className="thumbnail-card">
                      <div className="thumbnail-image-wrapper">
                        <img
                          src={thumb.url}
                          alt={thumb.id}
                          className="thumbnail-image"
                        />
                      </div>
                      <div className="thumbnail-meta">
                        <div className="meta-row">
                          <span className="meta-label">Size</span>
                          <span className="meta-value">
                            {thumb.width} × {thumb.height}
                          </span>
                        </div>
                        <div className="meta-row">
                          <span className="meta-label">Preset</span>
                          <span className="meta-value">
                            {thumb.is_preset
                              ? thumb.preset ?? "default"
                              : "custom"}
                          </span>
                        </div>
                        <div className="meta-row">
                          <span className="meta-label">ID</span>
                          <span className="meta-value mono">{thumb.id}</span>
                        </div>
                        <a
                          href={thumb.url}
                          target="_blank"
                          rel="noreferrer"
                          className="link"
                        >
                          Open original thumbnail
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </section>
        )}
      </main>
    </div>
  );
};

export default App;
