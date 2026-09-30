const SESSION_TITLE_MAX_LENGTH = 48;

export function displaySessionTitle(title: string | null | undefined): string {
  if (!title?.trim()) {
    return "New chat";
  }
  const collapsed = title.trim().replace(/\s+/g, " ");
  if (collapsed.length <= SESSION_TITLE_MAX_LENGTH) {
    return collapsed;
  }
  return `${collapsed.slice(0, SESSION_TITLE_MAX_LENGTH - 1).trimEnd()}…`;
}
