/**
 * Safely extracts and sanitizes a category string.
 * Returns 'general' if the category is falsy, empty, or not a string.
 */
export const getSafeCategory = (category?: string | null): string => {
  if (!category || typeof category !== "string") {
    return "general";
  }
  const trimmed = category.trim().toLowerCase();
  return trimmed || "general";
};
