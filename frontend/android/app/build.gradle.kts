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

    applicationVariants.all {
        val variantName = name
        outputs.all {
            val outputImpl = this as com.android.build.gradle.internal.api.BaseVariantOutputImpl
            outputImpl.outputFileName = "ArthSaarti-${variantName}.apk"
        }
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
            // FastAPI 0.100.x is the last version with full pydantic v1 support
            install("fastapi==0.100.1")
            install("uvicorn==0.23.2")
            install("sqlalchemy==2.0.35")
            // pydantic v1 is pure Python - no pydantic-core required
            install("pydantic==1.10.13")
            // pydantic-settings is pydantic v2-only, excluded for Android
            install("python-jose==3.4.0")
            install("passlib==1.7.4")
            install("python-multipart==0.0.6")
            install("httpx==0.24.1")
            install("typer==0.9.0")
            install("email-validator==2.0.0")
            install("diskcache==5.6.3")
            install("aiofiles==23.2.1")
            
            // Analytical & Data dependencies (flexible versions for Android mirror)
            install("numpy")
            install("pandas")
            install("yfinance")
            
            // Database & Auth
            install("alembic")
            install("cryptography")
            install("bcrypt")
            
            // Importers
            install("openpyxl")
            install("xlrd")
            install("beautifulsoup4")
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
