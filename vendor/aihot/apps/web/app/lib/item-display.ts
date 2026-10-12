// Upstream-reviewed items （二次加工） carry an AI-rewritten headline in `title`; reading surfaces
// lead with the original headline and treat the rewrite as secondary. Detection follows the tag
// the review pipeline stamps on these items (the same signal the workbench badge uses).
export function isReviewedItem(item: { tags: string[] }): boolean {
  return item.tags.includes("二次加工");
}

export function displayTitle(item: { title: string; originalTitle?: string | null; tags: string[] }): string {
  return isReviewedItem(item) && item.originalTitle ? item.originalTitle : item.title;
}
