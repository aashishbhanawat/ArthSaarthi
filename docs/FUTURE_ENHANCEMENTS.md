# Future Enhancements Backlog

This document tracks features and improvements identified during v1.0.0 development that are deferred to future releases.

## v1.1.0 (Near-term)

### Desktop App Improvements
- [ ] **Splash screen during initialization** - Show splash screen with progress bar while seeding completes, then show login (instead of banner approach)
- [ ] **Windows ARM64 native builds** - Currently uses x64 via emulation; native build would be faster
- [ ] **Auto-update mechanism** - Check for updates and prompt user to download new version
- [ ] **System tray integration** - Minimize to system tray instead of taskbar

### Asset Management
- [ ] **Manual asset creation** - Allow adding custom assets not in exchange lists
- [ ] **Asset data refresh scheduling** - Schedule automatic asset sync (e.g., weekly)
- [ ] **Incremental asset updates** - Only download changed assets instead of full sync

### User Experience
- [ ] **Dark mode** - System-wide dark theme toggle
- [ ] **Customizable dashboard widgets** - Drag-and-drop dashboard layout
- [ ] **Export to PDF/Excel** - Export reports and statements
- [ ] **Keyboard shortcuts** - Power-user keyboard navigation

---

## v1.2.0 (Medium-term)

### AI-Powered Features
- [ ] **Tax-loss harvesting suggestions** - Identify losses to offset gains
- [ ] **Portfolio rebalancing recommendations** - Alert when allocation drifts
- [ ] **Personalized daily digest** - AI-generated portfolio insights email

### Advanced Analytics
- [ ] **XIRR calculations** - Time-weighted return calculations
- [ ] **Benchmark comparisons** - Compare performance against indices
- [ ] **Tax reports** - Generate capital gains reports for filing

### Multi-Device Sync
- [ ] **Cloud sync option** - Opt-in sync between devices
- [ ] **Mobile app (read-only)** - View portfolio on mobile

---

## v2.0.0 (Long-term)

### Major Features
- [ ] **Multi-currency base support** - Base currency other than INR
- [ ] **International exchanges** - US stocks, ETFs, crypto
- [ ] **Bank account linking** - Import transactions automatically
- [ ] **Budget tracking** - Track expenses alongside investments

### Enterprise Features
- [ ] **Multi-tenant SaaS deployment** - Hosted version with subscriptions
- [ ] **Team/Family portfolios** - Shared portfolio management
- [ ] **Advisor mode** - Financial advisor view for multiple clients

---

## Known Issues to Address

### Performance
- [ ] Asset seeding takes 1-2 minutes on first run (38K+ assets)
- [ ] Large portfolio (1000+ transactions) may slow down

### Compatibility
- [ ] Linux ARM64 needs GLIBC 2.35+ (Ubuntu 22.04+, Raspberry Pi OS Bookworm)
- [ ] macOS requires Gatekeeper bypass (`xattr -cr`)

### Documentation
- [ ] Add video tutorials for common workflows
- [ ] Improve in-app help with contextual tips

---

## Completed in v1.0.0

- ✅ Multi-platform desktop builds (Windows, macOS Intel/ARM, Linux x64/ARM)
- ✅ SQLite WAL mode for concurrent access
- ✅ Background asset seeding (non-blocking)
- ✅ File-based logging (~/.arthsaarthi/logs/)
- ✅ Asset loading status banner
- ✅ In-app help system with bundled user guide
- ✅ ESPP/RSU tracking with cost basis
- ✅ Tax lot selection (FIFO, LIFO, Specific)
- ✅ Dividend/DRIP tracking
- ✅ Goal planning and watchlists
- ✅ Transaction history page with CRUD
- ✅ Data import from CSV
