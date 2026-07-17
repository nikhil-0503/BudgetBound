import React, { useEffect, useRef, useState } from 'react';
import QRCode from 'qrcode';
import { 
  X, 
  Globe, 
  Lock, 
  Copy, 
  Check, 
  Download, 
  QrCode, 
  Link2,
  Loader
} from 'lucide-react';
import api from '../services/api';

interface ShareModalProps {
  tripId: number;
  isPublic: boolean;
  shareToken: string | null;
  onClose: () => void;
  onUpdate: (updatedTrip: any) => void;
}

export const ShareModal: React.FC<ShareModalProps> = ({
  tripId,
  isPublic: initialIsPublic,
  shareToken: initialShareToken,
  onClose,
  onUpdate
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isPublic, setIsPublic] = useState(initialIsPublic);
  const [shareToken, setShareToken] = useState(initialShareToken);
  const [toggling, setToggling] = useState(false);
  const [copied, setCopied] = useState(false);

  const shareUrl = shareToken 
    ? `${window.location.origin}/share/${shareToken}`
    : '';

  useEffect(() => {
    setIsPublic(initialIsPublic);
    setShareToken(initialShareToken);
  }, [initialIsPublic, initialShareToken]);

  // Generate QR Code locally when isPublic and shareUrl are active
  useEffect(() => {
    if (isPublic && shareUrl && canvasRef.current) {
      QRCode.toCanvas(
        canvasRef.current,
        shareUrl,
        {
          width: 180,
          margin: 1.5,
          color: {
            dark: '#1e1b4b', // Deep indigo
            light: '#ffffff'
          }
        },
        (error) => {
          if (error) console.error('Error drawing local QR code:', error);
        }
      );
    }
  }, [isPublic, shareUrl]);

  const handleToggleShare = async () => {
    try {
      setToggling(true);
      const response = await api.post(`/api/trips/${tripId}/share/toggle`);
      setIsPublic(response.data.is_public);
      setShareToken(response.data.share_token);
      onUpdate(response.data);
    } catch (err) {
      console.error(err);
      alert('Failed to update trip visibility settings.');
    } finally {
      setToggling(false);
    }
  };

  const handleCopyLink = () => {
    if (!shareUrl) return;
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadQR = () => {
    if (!canvasRef.current) return;
    const dataUrl = canvasRef.current.toDataURL('image/png');
    const a = document.createElement('a');
    a.download = `budgetbound_trip_share_${tripId}.png`;
    a.href = dataUrl;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-6 z-50 animate-fade-in">
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl w-full max-w-md p-6 shadow-2xl relative">
        {/* Close Button */}
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-650 dark:hover:text-white transition-colors"
        >
          <X size={18} />
        </button>

        {/* Modal Header */}
        <div className="mb-6">
          <h3 className="font-extrabold text-base text-slate-900 dark:text-white flex items-center gap-2">
            <QrCode className="text-violet-500" size={18} />
            Share Travel Plan
          </h3>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Generate read-only shared links and QR codes to share with friends.
          </p>
        </div>

        {/* Sharing Settings Toggle Panel */}
        <div className="space-y-6">
          {/* Status Row */}
          <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-900/40 border border-slate-150 dark:border-slate-750 rounded-xl">
            <div className="flex items-center gap-3">
              <div className={`h-9 w-9 rounded-lg flex items-center justify-center ${isPublic ? 'bg-emerald-105 text-emerald-600 dark:bg-emerald-950/20' : 'bg-slate-100 text-slate-500 dark:bg-slate-900'}`}>
                {isPublic ? <Globe size={18} /> : <Lock size={18} />}
              </div>
              <div className="text-xs">
                <span className="font-bold text-slate-800 dark:text-white block">
                  {isPublic ? 'Public View Enabled' : 'Private Travel Plan'}
                </span>
                <span className="text-[10px] text-slate-400">
                  {isPublic ? 'Accessible by anyone with the link' : 'Owner authentication required'}
                </span>
              </div>
            </div>
            
            <button
              onClick={handleToggleShare}
              disabled={toggling}
              className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase transition-all shadow-sm ${
                isPublic 
                  ? 'bg-rose-50 hover:bg-rose-100 text-rose-600 dark:bg-rose-950/20 dark:hover:bg-rose-900/30' 
                  : 'bg-violet-600 hover:bg-violet-500 text-white'
              }`}
            >
              {toggling ? <Loader size={12} className="animate-spin" /> : (isPublic ? 'Make Private' : 'Publish')}
            </button>
          </div>

          {/* Public Sharing Elements */}
          {isPublic && shareToken ? (
            <div className="space-y-5 animate-fade-in text-xs">
              
              {/* Copy URL Row */}
              <div className="space-y-1.5">
                <label className="block text-slate-400 font-bold uppercase tracking-wide text-[10px]">Public Sharing Link</label>
                <div className="flex gap-2">
                  <div className="flex-1 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 px-3.5 py-2.5 rounded-xl text-[11px] font-bold text-slate-700 dark:text-slate-300 truncate select-all flex items-center gap-1.5">
                    <Link2 size={12} className="text-slate-400 shrink-0" />
                    {shareUrl}
                  </div>
                  <button
                    onClick={handleCopyLink}
                    className="bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-white p-2.5 rounded-xl transition-all shadow-sm border border-slate-200 dark:border-slate-600 shrink-0"
                    title="Copy Link"
                  >
                    {copied ? <Check size={16} className="text-emerald-500" /> : <Copy size={16} />}
                  </button>
                </div>
              </div>

              {/* QR Code Canvas Card */}
              <div className="flex flex-col items-center justify-center p-5 border border-slate-150 dark:border-slate-750 bg-slate-50/50 dark:bg-slate-900/10 rounded-2xl gap-4">
                <div className="bg-white p-2 rounded-xl border border-slate-200 shadow-sm">
                  <canvas ref={canvasRef} />
                </div>
                <button
                  onClick={handleDownloadQR}
                  className="inline-flex items-center gap-1.5 bg-violet-600 hover:bg-violet-500 text-white font-extrabold text-[10px] px-4 py-2 rounded-xl uppercase transition-all shadow-md shadow-violet-600/10"
                >
                  <Download size={12} />
                  Download QR Code
                </button>
              </div>

            </div>
          ) : (
            <div className="text-center py-6 text-slate-400 dark:text-slate-550 text-xs italic flex flex-col items-center gap-2">
              <Lock size={20} className="text-slate-350" />
              <span>Enable public sharing mode to generate QR codes and reader links.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
