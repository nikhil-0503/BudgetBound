import React from 'react';
import { MapPin, AlertTriangle } from 'lucide-react';

/**
 * NOTE FOR THE DEVELOPER:
 * The original MultiStopPlanner.tsx could not be recovered from the project
 * export — the export tool hit an encoding error reading the source file on
 * disk (a non-UTF-8 byte at position 30962) and saved its own error message
 * in place of the real file. This is a stand-in so the app keeps building.
 *
 * To restore the real page: open the original file locally, re-save it with
 * UTF-8 encoding (the stray byte is likely a curly quote or dash pasted in
 * from Word/Windows-1252), and drop its contents back in here.
 */
export const MultiStopPlanner: React.FC = () => {
  return (
    <div className="flex flex-col gap-8">
      <div>
        <p className="eyebrow-rule text-marigold-700 dark:text-marigold-400 text-xs font-semibold">Trip planning</p>
        <h1 className="font-display text-3xl font-semibold text-ink-900 dark:text-paper-50 mt-1">
          Multi-stop planner
        </h1>
      </div>

      <div className="ticket border-dashed p-12 flex flex-col items-center text-center gap-4">
        <MapPin className="h-12 w-12 text-paper-400 dark:text-paper-600" />
        <div>
          <h2 className="font-display text-lg font-semibold text-ink-900 dark:text-paper-50 mb-2">This page needs its source restored</h2>
          <p className="text-sm text-paper-600 dark:text-paper-400 max-w-md">
            The original file couldn't be read from your project export due to an encoding error. Re-save the real
            <code className="mx-1 px-1.5 py-0.5 rounded bg-paper-200 dark:bg-ink-700 font-num text-xs">MultiStopPlanner.tsx</code>
            as UTF-8 and drop it back into <code className="px-1.5 py-0.5 rounded bg-paper-200 dark:bg-ink-700 font-num text-xs">src/pages/</code> to bring back multi-stop route planning here.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/30 px-3 py-2 rounded-lg">
          <AlertTriangle size={14} />
          Placeholder page — styled to match the rest of the app
        </div>
      </div>
    </div>
  );
};
