import { useEffect } from 'react';

/**
 * Custom hook to set the browser tab title for each page
 * @param title - The title to display in the browser tab
 */
export const usePageTitle = (title: string) => {
  useEffect(() => {
    // Set the document title
    document.title = title;

    // Return cleanup function
    return () => {
      // Reset to default title when component unmounts
      document.title = 'BudgetBound - Travel Budget Planner';
    };
  }, [title]);
};
