# PPSSPP nightly Android APKs

Unofficial GitHub Actions builder. It watches [`hrydgard/ppsspp`](https://github.com/hrydgard/ppsspp) `master` and publishes a **normalOptimized** Android APK as a prerelease so [Obtainium](https://github.com/ImranR98/Obtainium) can track it.

This is **not** an official PPSSPP project. The APKs are GPL-2.0-or-later PPSSPP binaries; this repo only holds the CI glue (MIT). See `NOTICE`.

## Obtainium

1. Uninstall official / Play Store / Uptodown PPSSPP first (saves stay if you use a custom memstick folder). These builds use the in-tree **debug keystore**, so Android will refuse to update over an official signature.
2. Import [`ppsspp-nightly.obtainium.json`](ppsspp-nightly.obtainium.json), or add:

   `https://github.com/WoofahRayetCode/ppsspp-nightly-apk`

   GitHub source, **include prereleases**, APK filter `^ppsspp_v.*\.apk$`.

## How it works

- Cron every 30 minutes, plus **Actions → Build PPSSPP Android APK → Run workflow**.
- If `master` has not changed since the last published release, the job exits without building.
- Otherwise it checks out that commit with submodules, runs `./gradlew assembleNormalOptimized` (same task as PPSSPP’s `manual_generate_apk.yml`), and creates a prerelease tagged with `git describe` (for example `v1.20.4-1815-g3b2f0f0c1f31`).
- Only the latest **3** prereleases are kept.

It does **not** build every intermediate commit. If several land during one build, the next run takes current `master`.

## First run

After the first push, open **Actions** and run **Build PPSSPP Android APK** once. Scheduled workflows stay idle until that has happened at least once on `main`.

A full Android NDK build can take 20–40+ minutes.

## Signing

`android/debug.keystore` from the PPSSPP tree. Not Henrik’s Play / buildbot key. Stay on this feed after the first install from it.
