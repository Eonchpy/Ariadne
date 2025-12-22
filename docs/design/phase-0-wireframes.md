# Ariadne Frontend: Phase 0 UI Wireframes

**Document Version**: v1.0
**Date**: 2025-12-21
**Author**: Frontend Agent (Gemini)

## 1. Overview

This document provides wireframes for the core UI elements required for Phase 0 of the Ariadne project. These wireframes are described in a text-based format and focus on structure, layout, and key components.

**Phase 0 UI Goals**:
-   Establish the basic application layout.
-   Implement the user authentication flow.
-   Ensure a clean, professional appearance consistent with Ant Design's aesthetic.

---

## 2. Authentication Layout & Login Page

**Route**: `/login`
**Layout**: `AuthLayout`

### 2.1. Layout Description

The `AuthLayout` is a centered, simple layout used for all authentication-related pages. It ensures that forms for logging in, signing up, or recovering passwords are the focus of the user's attention.

-   **Structure**: A single-column layout, centered vertically and horizontally on the page.
-   **Background**: A subtle gradient or a neutral, light-gray background to keep the focus on the content.
-   **Content Area**: A container with a fixed width (e.g., 400px) that houses the form.

### 2.2. Login Page Wireframe

The login page allows users to enter their credentials to access the system.

```
+---------------------------------------------------+
|                                                   |
|                [Ariadne Project Logo]             |
|                                                   |
|           Enterprise Metadata Management          |
|                                                   |
+---------------------------------------------------+
|                                                   |
|   +-------------------------------------------+   |
|   |                                           |   |
|   |  Sign in to your account                  |   |
|   |                                           |   |
|   |  +-------------------------------------+  |   |
|   |  | Email Address                       |  |   |
|   |  | [icon] [_________________________]   |  |   |
|   |  +-------------------------------------+  |   |
|   |                                           |   |
|   |  +-------------------------------------+  |   |
|   |  | Password                            |  |   |
|   |  | [icon] [_________________________]   |  |   |
|   |  +-------------------------------------+  |   |
|   |                                           |   |
|   |  [ ] Remember me      Forgot password?    |   |
|   |                                           |   |
|   |  +-------------------------------------+  |   |
|   |  |           Sign In                   |  |   |
|   |  +-------------------------------------+  |   |
|   |                                           |   |
|   +-------------------------------------------+   |
|                                                   |
+---------------------------------------------------+
```

### 2.3. Component Breakdown

-   **Logo & Title**: The project logo and a clear title for brand identity.
-   **Form Title**: A clear heading like "Sign in to your account".
-   **Email Input**: An Ant Design `Input` component with a prefix icon (e.g., `UserOutlined`).
    -   Includes a `label`.
    -   HTML5 type `email` for basic validation.
-   **Password Input**: An Ant Design `Input.Password` component with a prefix icon (e.g., `LockOutlined`).
    -   Includes a `label`.
-   **Remember Me**: An Ant Design `Checkbox`.
-   **Forgot Password**: A link to a password recovery page (to be implemented in a later phase).
-   **Sign In Button**: An Ant Design `Button` of type `primary` that spans the full width of the form.
    -   Should show a loading spinner when the login request is in progress.

### 2.4. Interaction & Error Handling

-   **Validation**:
    -   Both fields are required.
    -   Email field should have a basic format check.
    -   Error messages appear below the respective fields.
-   **Submission**:
    -   Clicking "Sign In" disables the button and shows a loading state.
    -   On successful login, the user is redirected to the main application dashboard (e.g., `/`).
    -   On failure (e.g., invalid credentials), an Ant Design `Alert` component appears at the top of the form with a clear error message (e.g., "Invalid email or password.").

---

## 3. Main Application Layout

**Routes**: All protected routes (e.g., `/`, `/metadata/*`, `/lineage/*`)
**Layout**: `MainLayout`

### 3.1. Layout Description

The `MainLayout` is the standard interface for the entire application after a user has logged in. It follows a classic dashboard structure.

-   **Structure**: A three-part layout consisting of a header, a collapsible sidebar for navigation, and a main content area.
-   **Technology**: Implemented using Ant Design's `Layout` component (`Layout.Header`, `Layout.Sider`, `Layout.Content`).

### 3.2. Main Layout Wireframe

```
+--------------------------------------------------------------------------+
| [Logo] Ariadne | [Global Search Bar]              | [Notifications] [User] |
+--------------------------------------------------------------------------+
|                |                                                          |
|  Navigation    |                                                          |
| +------------+ |  +----------------------------------------------------+  |
| | Dashboard  | |  |                                                    |  |
| +------------+ |  |  <Breadcrumb: Home / Metadata / Tables>              |  |
| | Data Srcs  | |  |                                                    |  |
| +------------+ |  |  +------------------------------------------------+  |  |
| | Metadata   | |  |  | Page Title                                     |  |  |
| |  - Tables  | |  |  +------------------------------------------------+  |  |
| |  - Fields  | |  |                                                    |  |
| +------------+ |  |  |                                                |  |  |
| | Lineage    | |  |  |                                                |  |  |
| +------------+ |  |  |        Main Page Content                       |  |  |
| | Bulk Import| |  |  |        (e.g., a table, a graph, a form)        |  |  |
| +------------+ |  |  |                                                |  |  |
| | AI Assistant| |  |  |                                                |  |  |
| +------------+ |  |  |                                                |  |  |
|                |  |  +------------------------------------------------+  |  |
| [Collapse]     |  |                                                    |  |
|                |  |  <Footer: Ariadne ©2025>                           |  |  |
|                |                                                          |
+----------------+---------------------------------------------------------+
```

### 3.3. Component Breakdown

-   **Header (`Layout.Header`)**:
    -   **Logo & Title**: Positioned on the left.
    -   **Global Search Bar**: A prominent search input in the center for future AI/semantic search functionality. (Placeholder for now).
    -   **Right-side Controls**:
        -   **Notifications**: An icon button (e.g., `BellOutlined`) with a badge for notifications. (Placeholder for now).
        -   **User Menu**: An Ant Design `Avatar` with the user's initials, which opens a `Dropdown` menu on click.
            -   **Menu Items**: "Profile", "Settings", and "Logout".
            -   The "Logout" option will clear the user's session and redirect to the `/login` page.

-   **Sidebar (`Layout.Sider`)**:
    -   **Navigation**: An Ant Design `Menu` component with icons for each top-level item.
    -   **Menu Structure**:
        -   Dashboard
        -   Data Sources
        -   Metadata (with sub-items: Tables, Fields)
        -   Lineage
        -   Bulk Import
        -   AI Assistant
    -   **Collapsible**: The sidebar can be collapsed to an icon-only view to maximize content space. An Ant Design `Button` at the bottom of the sider will control this.

-   **Content Area (`Layout.Content`)**:
    -   **Breadcrumbs**: An Ant Design `Breadcrumb` component to show the user's current location in the application hierarchy.
    -   **Page Header**: An Ant Design `PageHeader` component that contains the main page title and can hold action buttons (e.g., "Create Table").
    -   **Main Content**: The primary area where the page-specific content is rendered. It will have appropriate padding.
    -   **Footer**: A standard footer with copyright information.

### 3.4. Behavior

-   The active navigation item in the sidebar is highlighted based on the current route.
-   The layout is responsive. On smaller screens, the sidebar may become a drawer that overlays the content.
-   Logging out from the user menu in the header will execute the `logout` action in the `authStore` and redirect the user.
