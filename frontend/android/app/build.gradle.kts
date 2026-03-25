plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.chaquo.python")
}

android {
    namespace = "com.arthsaarthi.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.arthsaarthi.app"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.1.0"

        ndk {
            // Support ARM64 and x86_64 (for emulator)
            abiFilters += listOf("arm64-v8a", "x86_64")
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

// Chaquopy configuration (must be a top-level block in .kts files, Chaquopy 15+)
chaquopy {
    defaultConfig {
        // Python 3.13 required: enables sysconfig for Rust cross-compilation
        // (needed to build pydantic-core from source for Android)
        version = "3.13"

        // Use the python binary path passed via command line property (-PbuildPython)
        if (project.hasProperty("buildPython")) {
            buildPython(project.property("buildPython") as String)
        }

        // Backend Python dependencies
        pip {
            install("pydantic-core==2.23.4")
            install("fastapi==0.115.0")
            install("uvicorn==0.30.6")
            install("sqlalchemy==2.0.35")
            // pydantic will use the already-installed pydantic-core
            install("pydantic==2.9.2")
            install("pydantic-settings==2.5.2")
            install("python-jose==3.4.0")
            install("passlib==1.7.4")
            install("python-multipart==0.0.12")
            install("httpx==0.27.2")
            install("typer==0.12.5")
            install("email-validator==2.2.0")
            install("diskcache==5.6.3")
            install("aiofiles==24.1.0")
        }
    }
}

dependencies {
    // Capacitor
    implementation("com.capacitorjs:core:7.2.0")

    // AndroidX
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.webkit:webkit:1.12.1")
}
