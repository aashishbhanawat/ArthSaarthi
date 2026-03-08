// Top-level build file where you can add configuration options common to all sub-projects/modules.

plugins {
    id("com.android.application") version "8.7.3" apply false
    id("org.jetbrains.kotlin.android") version "2.1.0" apply false
    // Chaquopy: embeds CPython interpreter for running the FastAPI backend
    id("com.chaquo.python") version "16.0.0" apply false
}
