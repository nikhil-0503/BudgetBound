import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { 
  FileText, 
  Upload, 
  Download, 
  Trash2, 
  Edit3, 
  Loader, 
  Eye, 
  FolderOpen,
  Calendar,
  Layers,
  X,
  File
} from 'lucide-react';

interface Document {
  id: number;
  trip_id: number;
  category: string;
  filename: string;
  filepath: string;
  filesize: number;
  uploaded_at: string;
}

interface DocumentManagerProps {
  tripId: number;
}

export const DocumentManager: React.FC<DocumentManagerProps> = ({ tripId }) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [category, setCategory] = useState('Hotel Booking');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewDoc, setPreviewDoc] = useState<Document | null>(null);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/trips/${tripId}/documents`);
      setDocuments(response.data);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [tripId]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('category', category);

      const response = await api.post(`/api/trips/${tripId}/documents`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setDocuments(prev => [...prev, response.data]);
      setSelectedFile(null);
      
      // Reset input element
      const fileInput = document.getElementById('document-file-input') as HTMLInputElement;
      if (fileInput) fileInput.value = '';

    } catch (err) {
      console.error('Failed to upload file:', err);
      alert('Error uploading document. Check size and parameters.');
    } finally {
      setUploading(false);
    }
  };

  const handleRename = async (doc: Document) => {
    const nextName = prompt('Enter a new filename:', doc.filename);
    if (!nextName || !nextName.trim() || nextName === doc.filename) return;

    try {
      const response = await api.put(`/api/trips/${tripId}/documents/${doc.id}`, {
        filename: nextName.trim()
      });
      setDocuments(prev => prev.map(d => d.id === doc.id ? response.data : d));
    } catch (err) {
      console.error(err);
      alert('Failed to rename document.');
    }
  };

  const handleDelete = async (docId: number) => {
    if (!confirm('Are you sure you want to delete this document? This cannot be undone.')) return;

    try {
      await api.delete(`/api/trips/${tripId}/documents/${docId}`);
      setDocuments(prev => prev.filter(d => d.id !== docId));
      if (previewDoc?.id === docId) setPreviewDoc(null);
    } catch (err) {
      console.error(err);
      alert('Failed to delete document.');
    }
  };

  const handleDownload = (doc: Document) => {
    // Open FastAPI FileResponse in a new window/tab to trigger immediate browser save
    const downloadUrl = `${api.defaults.baseURL || ''}/api/trips/${tripId}/documents/${doc.id}`;
    
    // Append Authorization token manually if standard GET requires headers
    const token = localStorage.getItem('token');
    if (token) {
      window.open(`${downloadUrl}?token=${token}`, '_blank');
    } else {
      window.open(downloadUrl, '_blank');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes >= 1048576) {
      return `${(bytes / 1048576).toFixed(1)} MB`;
    }
    return `${(bytes / 1024).toFixed(0)} KB`;
  };

  const getCategoryColor = (cat: string) => {
    switch (cat) {
      case 'Hotel Booking': return 'bg-sky-100 text-sky-900 dark:bg-sky-950/40 dark:text-sky-400 border-sky-200';
      case 'Flight Ticket': return 'bg-marigold-100 text-marigold-900 dark:bg-marigold-950/40 dark:text-marigold-400 border-marigold-200';
      case 'Train Ticket': return 'bg-emerald-100 text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-400 border-emerald-200';
      case 'Passport': return 'bg-amber-100 text-amber-900 dark:bg-amber-950/40 dark:text-amber-400 border-amber-200';
      case 'Visa': return 'bg-rose-100 text-rose-900 dark:bg-rose-950/40 dark:text-rose-400 border-rose-200';
      case 'Insurance': return 'bg-petrol-100 text-petrol-900 dark:bg-petrol-950/40 dark:text-petrol-400 border-petrol-200';
      default: return 'bg-paper-100 text-paper-700 dark:bg-paper-800 dark:text-paper-300 border-paper-200';
    }
  };

  return (
    <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-extrabold text-paper-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
          <FolderOpen size={16} className="text-marigold-500" />
          Trip Document Manager
        </h3>
        <span className="text-[10px] font-bold text-paper-400 uppercase">
          {documents.length} Attachments
        </span>
      </div>

      {/* Upload Box */}
      <form onSubmit={handleUploadSubmit} className="p-4 bg-paper-50 dark:bg-paper-900 border border-dashed border-paper-200 dark:border-paper-800 rounded-xl space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="space-y-1">
            <label className="block text-paper-400 font-bold uppercase tracking-wide text-[9px]">Document Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 border border-paper-200 dark:border-paper-700 rounded-lg bg-paper-50 dark:bg-paper-800 dark:text-white focus:outline-none"
            >
              {["Hotel Booking", "Train Ticket", "Flight Ticket", "Bus Ticket", "Passport", "Visa", "Insurance", "Other"].map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label className="block text-paper-400 font-bold uppercase tracking-wide text-[9px]">Upload File Attachment</label>
            <input
              type="file"
              id="document-file-input"
              onChange={handleFileChange}
              className="w-full text-xs text-paper-500 dark:text-paper-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-[10px] file:font-bold file:uppercase file:bg-marigold-50 file:text-marigold-600 dark:file:bg-marigold-950/40 dark:file:text-marigold-400 hover:file:bg-marigold-100"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={uploading || !selectedFile}
          className="w-full bg-marigold-600 hover:bg-marigold-500 text-white font-extrabold text-[10px] uppercase py-2.5 rounded-xl transition-all shadow-md flex items-center justify-center gap-1.5 disabled:opacity-50"
        >
          {uploading ? <Loader size={12} className="animate-spin" /> : <Upload size={12} />}
          {uploading ? 'Uploading File...' : 'Upload Document'}
        </button>
      </form>

      {/* Attachments list */}
      {loading && documents.length === 0 ? (
        <div className="flex items-center justify-center py-6 text-paper-400 gap-2 text-xs">
          <Loader size={14} className="animate-spin text-marigold-500" />
          <span>Syncing files...</span>
        </div>
      ) : documents.length === 0 ? (
        <div className="text-center py-8 text-paper-400 text-xs italic">
          No files attached to this trip yet.
        </div>
      ) : (
        <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
          {documents.map((doc) => (
            <div 
              key={doc.id}
              className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border border-paper-100 dark:border-paper-700/60 p-3 rounded-xl hover:border-paper-200 dark:hover:border-paper-600 transition-all text-xs"
            >
              <div className="flex items-start gap-3 min-w-0">
                <div className="h-8 w-8 rounded-lg bg-marigold-50 dark:bg-marigold-950/40 flex items-center justify-center text-marigold-500 shrink-0 mt-0.5">
                  <FileText size={16} />
                </div>
                <div className="min-w-0">
                  <span className="font-bold text-paper-800 dark:text-paper-200 block truncate" title={doc.filename}>
                    {doc.filename}
                  </span>
                  <div className="flex flex-wrap gap-2 items-center mt-1 text-[10px] text-paper-400 font-semibold">
                    <span className={`px-1.5 py-0.5 rounded border text-[8px] font-extrabold uppercase shrink-0 ${getCategoryColor(doc.category)}`}>
                      {doc.category}
                    </span>
                    <span className="flex items-center gap-0.5 shrink-0"><Calendar size={10} /> {new Date(doc.uploaded_at).toLocaleDateString()}</span>
                    <span className="shrink-0">• {formatFileSize(doc.filesize)}</span>
                  </div>
                </div>
              </div>

              {/* Actions row */}
              <div className="flex items-center gap-1.5 shrink-0 justify-end sm:border-0 border-t border-paper-50 dark:border-paper-800 pt-2 sm:pt-0">
                <button
                  onClick={() => handleRename(doc)}
                  className="p-1.5 bg-paper-50 dark:bg-paper-700 rounded-lg hover:bg-paper-100 text-paper-500 dark:text-paper-400 transition-colors"
                  title="Rename File"
                >
                  <Edit3 size={13} />
                </button>
                <button
                  onClick={() => handleDownload(doc)}
                  className="p-1.5 bg-paper-50 dark:bg-paper-700 rounded-lg hover:bg-paper-100 text-paper-600 dark:text-paper-400 transition-colors"
                  title="Download / View"
                >
                  <Download size={13} />
                </button>
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="p-1.5 bg-rose-50 dark:bg-rose-950/20 rounded-lg text-rose-600 hover:bg-rose-100 transition-colors"
                  title="Delete Document"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};



