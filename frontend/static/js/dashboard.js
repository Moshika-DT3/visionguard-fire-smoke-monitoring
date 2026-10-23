/**
 * Adds an active navigation hint without affecting initial server-rendered content.
 */
document.addEventListener("DOMContentLoaded", () => {
  const currentPath = window.location.pathname;
  document.querySelectorAll(".site-header nav a").forEach((link) => {
    const isDashboard = currentPath === "/" && link.getAttribute("href") === "/";
    if (isDashboard || link.getAttribute("href") === currentPath) {
      link.setAttribute("aria-current", "page");
    }
  });
});
