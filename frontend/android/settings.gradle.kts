pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
        // Chaquopy Maven repository
        maven { url = uri("https://chaquo.com/maven") }
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.PREFER_SETTINGS)
    repositories {
        google()
        mavenCentral()
        // Chaquopy Maven repository
        maven { url = uri("https://chaquo.com/maven") }
    }
}

rootProject.name = "ArthSaarthi"
include(":app")
apply(from = "capacitor.settings.gradle")
