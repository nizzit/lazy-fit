# ============================================================
#  LazyFit — Android build / install / run helpers
#  Requires: uv, Java JDK, Android SDK (set ANDROID_HOME)
# ============================================================

.PHONY: help dev create build run package clean logs

# ── defaults ────────────────────────────────────────────────
APP      := lazy-fit
PLATFORM := android

# ── help ────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  LazyFit — Makefile targets"
	@echo ""
	@echo "  Desktop"
	@echo "  -------"
	@echo "  make dev          Run on desktop (python main.py via uv)"
	@echo ""
	@echo "  Android"
	@echo "  -------"
	@echo "  make create       briefcase create android   (first-time setup)"
	@echo "  make build        briefcase build android    (compile APK)"
	@echo "  make run          briefcase run android      (build + install + launch)"
	@echo "  make package      briefcase package android  (release APK)"
	@echo "  make logs         adb logcat -s toga         (stream app logs)"
	@echo ""
	@echo "  Misc"
	@echo "  ----"
	@echo "  make clean        Remove Briefcase build artefacts"
	@echo ""

# ── desktop ─────────────────────────────────────────────────
dev:
	uv run python main.py

# ── android: first-time project scaffold ────────────────────
create:
	uv run briefcase create $(PLATFORM)

# ── android: compile (Gradle build) ─────────────────────────
build:
	uv run briefcase build $(PLATFORM)

# ── android: build + install + launch ───────────────────────
run:
	uv run briefcase run $(PLATFORM)

# ── android: release APK (signed, ready for distribution) ───
package:
	uv run briefcase package $(PLATFORM)

# ── stream logcat filtered to Toga / Python ─────────────────
logs:
	adb logcat -s toga python

# ── clean build artefacts ───────────────────────────────────
clean:
	rm -rf build/
	@echo "Build artefacts removed."
