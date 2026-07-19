import React from 'react';
import { FolderOpen, AlertCircle, RefreshCw } from 'lucide-react';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionLabel,
  onAction
}) => {
  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-10 text-center flex flex-col items-center justify-center space-y-4 max-w-md mx-auto shadow-sm">
      <div className="h-14 w-14 rounded-full bg-violet-50 dark:bg-violet-950 flex items-center justify-center text-violet-650 dark:text-violet-400">
        {icon || <FolderOpen size={24} />}
      </div>
      
      <div className="space-y-1">
        <h4 className="font-extrabold text-sm uppercase tracking-wider text-slate-800 dark:text-white">
          {title}
        </h4>
        <p className="text-xs text-slate-450 dark:text-slate-400 leading-relaxed">
          {description}
        </p>
      </div>

      {onAction && actionLabel && (
        <button
          type="button"
          onClick={onAction}
          className="inline-flex items-center gap-1.5 bg-violet-650 hover:bg-violet-500 text-white font-extrabold text-[10px] px-4.5 py-2.5 rounded-xl uppercase transition-all shadow-md"
        >
          <RefreshCw size={11} />
          {actionLabel}
        </button>
      )}
    </div>
  );
};

export const SkeletonCard: React.FC = () => {
  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-150 dark:border-slate-700 rounded-2xl p-5 space-y-4 animate-pulse">
      <div className="h-40 bg-slate-200 dark:bg-slate-700 rounded-xl w-full" />
      <div className="space-y-2">
        <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded-md w-3/4" />
        <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded-md w-1/2" />
      </div>
      <div className="flex gap-2 justify-between pt-2">
        <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded-lg w-1/3" />
        <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded-lg w-1/4" />
      </div>
    </div>
  );
};

export const SkeletonList: React.FC = () => {
  return (
    <div className="space-y-3.5 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-white dark:bg-slate-800 border border-slate-150 dark:border-slate-700 p-4 rounded-2xl flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 w-2/3">
            <div className="h-9 w-9 bg-slate-200 dark:bg-slate-700 rounded-xl shrink-0" />
            <div className="space-y-1.5 w-full">
              <div className="h-3.5 bg-slate-200 dark:bg-slate-700 rounded-md w-1/2" />
              <div className="h-2.5 bg-slate-200 dark:bg-slate-700 rounded-md w-1/3" />
            </div>
          </div>
          <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded-lg w-16" />
        </div>
      ))}
    </div>
  );
};

export const SkeletonTable: React.FC = () => {
  return (
    <div className="border border-slate-150 dark:border-slate-700 rounded-2xl overflow-hidden animate-pulse">
      <div className="bg-slate-100 dark:bg-slate-700 h-10 w-full border-b border-slate-200" />
      <div className="p-4 space-y-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex justify-between items-center gap-4">
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded-md w-1/4" />
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded-md w-1/5" />
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded-md w-1/6" />
          </div>
        ))}
      </div>
    </div>
  );
};
