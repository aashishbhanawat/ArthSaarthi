# Release Plan

This document outlines the process for releasing new versions of the application.

## 1. Versioning

We use [Semantic Versioning (SemVer)](https://semver.org/) for our releases. The version number is in the format `MAJOR.MINOR.PATCH`.

-   **MAJOR** version is incremented for incompatible API changes.
-   **MINOR** version is incremented for adding functionality in a backward-compatible manner.
-   **PATCH** version is incremented for backward-compatible bug fixes.

## 2. Git Workflow for Releases

Our release process is based on Git tags on the `main` branch.

1.  **Development:** All development work is done on feature branches, which are branched off from `main`.
2.  **Code Review:** When a feature is complete, a pull request is opened to merge the feature branch into `main`. The pull request must be reviewed and approved by at least one other team member.
3.  **Merging:** Once the pull request is approved and all automated checks (CI) have passed, it is merged into the `main` branch.
4.  **Release:** To create a new release, a new tag is pushed to the `main` branch. The tag must be named using the SemVer format, prefixed with a `v`. For example: `v1.2.3`.

    ```bash
    # Ensure you are on the main branch and have the latest changes
    git checkout main
    git pull origin main

    # Create a new tag
    git tag -a v1.2.3 -m "Release version 1.2.3"

    # Push the tag to the remote repository
    git push origin v1.2.3
    ```

5.  **Automation:** Pushing a new tag to the `main` branch will trigger the release workflow in GitHub Actions, which will build and push the Docker images to the container registry.

## 3. Testing

Before any release, the following testing must be completed:

-   **Unit Tests:** All unit tests for the `backend` and `frontend` must pass. These are run automatically by the CI pipeline on every push to `main`.
-   **Integration Tests:** Integration tests are also run automatically by the CI pipeline.
-   **End-to-End (E2E) Tests:** The E2E test suite must pass in a staging environment that mirrors production.
-   **Manual QA:** Manual quality assurance testing should be performed on the staging environment to catch any issues not covered by automated tests.

## 4. Building and Pushing Docker Images

The Docker images for the `backend` and `frontend` services are built and pushed to our Docker Hub registry (or other container registry). To support various hardware platforms (e.g., standard servers and Raspberry Pi), we will build **multi-architecture images**.

This process is automated by the GitHub Actions release workflow. The workflow uses the `build-and-push.sh` script to perform the following steps:

1.  **Setup `buildx`:** Initialize the `docker buildx` builder.
2.  **Build & Push:** Use `docker buildx build` to build and push the `backend` and `frontend` images for multiple platforms (`linux/amd64`, `linux/arm64`).
    ```bash
    # Example command for the backend
    docker buildx build \
      --platform linux/amd64,linux/arm64 \
      -t your-repo/arthsaarthi-backend:latest \
      -t your-repo/arthsaarthi-backend:v1.2.3 \
      --push .
    ```
3.  The images are tagged with the Git tag (e.g., `v1.2.3`) and `latest`.

## 5. Deployment

Deployment to production is a separate process that is initiated after the new Docker images have been successfully built and pushed to the registry.

(Note: The specifics of the deployment process will depend on the production environment, e.g., Kubernetes, AWS ECS, etc. This section can be expanded with the detailed deployment steps.)
