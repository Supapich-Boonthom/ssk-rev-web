# Git Workflow Rules

This document outlines the Git guidelines and workflow constraints for this repository. The agent and any collaborators must strictly follow these rules.

## 1. Branch Protection
- **DO NOT** commit or push directly to the `main` branch under any circumstances.

## 2. Branching Strategy
- Always create a new branch before starting to write code, implement new features, or fix bugs.
- Use descriptive branch naming conventions, such as:
  - `feature/<feature-name>` for new features.
  - `update/<update-description>` for modifications or updates.
  - `bugfix/<bug-description>` or `fix/<bug-description>` for resolving issues.

## 3. Pull Requests (PR)
- When work is finished on a branch:
  1. Push the branch to the remote repository (`git push origin <branch-name>`).
  2. Recommend or guide the steps to open a Pull Request (PR) to merge the branch into `main`.
  3. Wait for code review or verification before merging.

## 4. Commit Message Standard
- All commit messages must follow the **Conventional Commits** specification.
- Structure format:
  ```
  <type>[optional scope]: <description>

  [optional body]

  [optional footer(s)]
  ```
- Allowed types:
  - `feat`: A new feature
  - `fix`: A bug fix
  - `docs`: Documentation only changes
  - `style`: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
  - `refactor`: A code change that neither fixes a bug nor adds a feature
  - `perf`: A code change that improves performance
  - `test`: Adding missing tests or correcting existing tests
  - `chore`: Changes to the build process or auxiliary tools and libraries such as documentation generation
