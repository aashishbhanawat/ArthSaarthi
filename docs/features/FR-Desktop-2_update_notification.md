# Feature Plan: Update Notification (FR-Desktop-2)

**Feature ID:** FR-Desktop-2  
**Title:** Update Notification for Desktop App  
**Priority:** P1  
**Category:** Desktop UX

---

## 1. Objective

Notify desktop users when a new version of ArthSaarthi is available on GitHub Releases, allowing them to download and update manually.

---

## 2. Design Decision

**Notify-only approach** (not auto-download):
- Simpler implementation
- User has full control
- Works without code signing on Windows
- No risk of interrupted downloads

---

## 3. User Flow

1. App starts and checks GitHub Releases API
2. Compares local version with latest release tag
3. If newer version available:
   - Show banner/notification in app
   - Display: "Version X.Y.Z is available. [Download]"
   - Download link opens GitHub Releases page in browser
4. User clicks link, downloads installer, installs manually

---

## 4. Technical Design

### 4.1 Version Check Logic

```typescript
// In Electron main or preload
async function checkForUpdates() {
  const response = await fetch(
    'https://api.github.com/repos/aashishbhanawat/ArthSaarthi/releases/latest'
  );
  const release = await response.json();
  const latestVersion = release.tag_name.replace('v', '');
  const currentVersion = app.getVersion();
  
  if (semver.gt(latestVersion, currentVersion)) {
    return {
      available: true,
      version: latestVersion,
      url: release.html_url
    };
  }
  return { available: false };
}
```

### 4.2 UI Notification

- Banner at top of dashboard (dismissible)
- Or: notification in settings/about page
- Include "Don't remind me for this version" option

---

## 5. Acceptance Criteria

- [ ] App checks for updates on startup
- [ ] Banner shown when new version available
- [ ] Download link opens GitHub Releases
- [ ] User can dismiss notification
- [ ] Current version displayed in About section

---

## 6. Dependencies

- GitHub Releases API (public, no auth needed)
- Current app version in package.json
