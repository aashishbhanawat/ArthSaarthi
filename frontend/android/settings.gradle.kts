pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
        // Chaquopy Maven repository
        maven { url = uri("https://chaquo.com/maven") }
    }
}

dependencyResolution {
    repositories {
        google()
        mavenCentral()
        // Chaquopy Maven repository
        maven { url = uri("https://chaquo.com/maven") }
    }
}

rootProject.name = "ArthSaarthi"
include(":app")
