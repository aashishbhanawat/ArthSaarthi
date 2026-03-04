# ArthSaarthi: AI Development Workflow (Token-Safe SOP)

This document outlines the strict, step-by-step lifecycle for developing features or fixing bugs using the Antigravity AI Agent. 

**GOAL:** Prevent API exhaustion (429/503 errors), prevent context bloat, and maintain a clean project state.

---

## Phase 1: Session Initialization (Clean Slate)
*Always start a new task in a brand-new chat window.*
1. **Model:** `Gemini Flash` (or `Gemini 3.1 Pro`)
2. **Action:** Load the current project context without reading the whole codebase.
3. **Prompt to AI:** > "Read `docs/project_handoff_summary.md` and `docs/AI_WORKFLOW.md`. We are starting a new session. Acknowledge the current state of the project and wait for my instructions."

## Phase 2: Planning & Architecture (The Implementation Plan)
*Never ask for code in this phase. Demand a comprehensive plan first.*
1. **Model:** `Claude Opus` (For complex logic) or `Gemini 3.1 Pro`.
2. **Action:** Define the feature or bug. Ask the AI to act as the Solution Architect/Backend Dev.
3. **Prompt to AI:** > "We are working on [Feature/Bug Name]. Read the relevant section in `docs/requirements.md` (or the bug report). 
   > **OUTPUT REQUIREMENT:** Before writing any code, you MUST provide a detailed 'Implementation Plan'. This plan must include:
   > - Architectural approach & reasoning.
   > - New or updated API endpoints.
   > - Database schema changes.
   > - A bulleted list of all files that will be created or modified.
   > Wait for my explicit approval of this plan before writing code."

## Phase 3: Iterative Execution (The Token Saver)
*Execute the plan strictly one file at a time.*
1. **Model:** `Gemini 3.1 Pro` (or `Claude Opus` if highly complex).
2. **Action:** Instruct the AI to generate code for a single step or file.
3. **Prompt to AI:** > "The plan is approved. Execute Step 1 only. Provide the code for [filename]."
4. **Repeat:** Apply the code, review it, and then ask for Step 2.

## Phase 4: Testing & Verification
*The AI MUST NOT run test suites autonomously to prevent infinite debugging loops.*
1. **Model:** `Gemini Flash` (Cheap/Fast).
2. **Action:** The HUMAN runs the tests in the terminal using the Docker commands in `GEMINI.md`.
3. **Handling Failures:** If a test fails, the human pastes ONLY the specific error snippet and the relevant 3-4 lines of code into the chat.
4. **Prompt to AI:** > "The test failed with this output: [Paste Error]. Analyze this stack trace snippet and provide the exact fix. Do not guess."

## Phase 5: Handoff, Walkthrough & Teardown
*Provide a high-level summary of what was built before closing the context.*
1. **Model:** `Gemini Flash` or `Gemini 3.1 Pro`.
2. **Action:** Once the feature/fix works and tests pass, instruct the AI to explain what it did and update the documentation.
3. **Prompt to AI:** > "The task is complete and tests are passing. 
   > **OUTPUT REQUIREMENT 1:** Provide a brief 'Feature Walkthrough' explaining how the new code flows together end-to-end for my understanding.
   > **OUTPUT REQUIREMENT 2:** > 1. Update `docs/workflow_history.md`.
   > 2. Update `docs/project_handoff_summary.md` with the new state.
   > 3. Verify the Pre-Commit Checklist in `GEMINI.md`.
   > 4. Generate the final Git commit message."
4. **Final Step:** Commit the code, close the IDE Chat panel, and delete the thread.
