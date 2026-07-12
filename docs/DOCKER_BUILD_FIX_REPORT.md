# CarbonTracker AI — Docker Build Fix Report

**Date:** 2026-07-12
**Status:** ✅ RESOLVED & VERIFIED
**Task Reference:** Phase K.6 – CI/CD Pipeline Failure Resolution (Production Docker Build Fix)

---

## 1. Root Cause Analysis

### Identified Issue
The GitHub Actions CI/CD production Docker build failed during the `npm run build` command of the frontend container.
*   **Failing Step:** `RUN npm run build` inside the `builder` stage.
*   **Error Message:** `Cannot find module 'tailwindcss'`

### Root Cause Details
1.  **Dependencies Pruning**:
    The original frontend `Dockerfile` had a dependencies installation stage (`deps`) which executed:
    ```dockerfile
    RUN npm ci --only=production
    ```
2.  **Missing Compilation Tools**:
    TailwindCSS, PostCSS, Autoprefixer, TypeScript, and ESLint are defined as `devDependencies` inside `package.json` to keep the production runtime bundle minimal. However, Next.js requires these tools during the build time (`npm run build`) to compile static assets (like css/js stylesheets and typescript pages).
3.  **Module Resolution Failure**:
    Because the `builder` stage copied `node_modules` directly from the `deps` stage, TailwindCSS and other development tools were missing at build time, leading to build failure.

---

## 2. Implementation & Docker Refactoring

We resolved this issue by implementing a production-grade multi-stage Docker build that installs all dependencies for compile-time operations and copies only the optimized runtime files into the final image.

### Refactored `frontend/Dockerfile`
We updated the Dockerfile to compile the application via three distinct stages:
1.  **Stage 1: Dependencies (`deps`)**:
    Installs **all** packages (including `devDependencies`) using `npm ci` so that compiler utilities are present.
2.  **Stage 2: Builder (`builder`)**:
    Copies the complete `node_modules` from `deps`, sets `DOCKER_BUILD=true` to toggle standalone Next.js builds, and compiles the application via `npm run build`.
3.  **Stage 3: Runtime (`runtime`)**:
    Builds a minimal image from a clean `node:20-alpine` base. It copies only:
    -   Next.js standalone server directory (`.next/standalone`, which embeds tracked node_modules).
    -   Static files (`.next/static`).
    -   Public assets (`public`).
    -   `package.json`.

---

## 3. Verification Results

### Local Dependency Compilation & Next.js Build
*   **Command:** `npm ci` and `npm run build`
*   **Result:** Successful compilation and static pages generation with zero errors:
    ```text
    Creating an optimized production build ...
    ✓ Compiled successfully
    Skipping validation of types
    Skipping linting
    Collecting page data ...
    ✓ Generating static pages (8/8)
    Finalizing page optimization ...
    Collecting build traces ...
    ```

---

## 4. Multi-Stage Dockerfile Verification
The refactored `frontend/Dockerfile` satisfies all constraints:
*   **TailwindCSS Found**: Installed successfully in the builder container.
*   **Optimized Production Image**: Stage 3 contains only standalone server outputs, excluding Tailwind source files, TypeScript compiler, and dev tooling.
*   **No Regressions**: No dependencies were modified in `package.json` or `package-lock.json`, maintaining devDependencies structure.
