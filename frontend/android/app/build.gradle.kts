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
        versionCode = 6
        versionName = "1.2.0"

        ndk {
            // Support ARM64 and x86_64 (for emulator)
            abiFilters += listOf("arm64-v8a", "x86_64")
        }
    }

    signingConfigs {
        create("release") {
            // These properties can be provided via gradle.properties or command line -P
            storeFile = file(project.findProperty("RELEASE_STORE_FILE") ?: "debug.keystore")
            storePassword = project.findProperty("RELEASE_STORE_PASSWORD") as String?
            keyAlias = project.findProperty("RELEASE_KEY_ALIAS") as String?
            keyPassword = project.findProperty("RELEASE_KEY_PASSWORD") as String?
        }
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
        debug {
            // For experimental builds, we can also use the release config if provided
            if (project.hasProperty("RELEASE_STORE_FILE")) {
                signingConfig = signingConfigs.getByName("release")
            }
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
        // Python 3.11 matches server/desktop environments for full compatibility
        version = "3.11"

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
            // email-validator: pin to v1.x — FastAPI 0.100.1 uses the v1 API;
            // v2.0+ changes the import structure and breaks fastapi.security at startup
            install("email-validator==1.3.1")
            install("diskcache==5.6.3")
            install("aiofiles==23.2.1")
            
            // Analytical & Data dependencies (flexible versions for Android mirror)
            install("numpy")
            install("pandas")
            install("frozendict")
            install("peewee")
            install("multitasking")
            install("yfinance==0.2.55")
            install("requests-cache==1.2.0")
            
            // Database & Auth
            install("alembic")
            install("cryptography")
            install("bcrypt")
            
            // Importers
            install("openpyxl")
            install("xlrd")
            install("beautifulsoup4")
            install("platformdirs==4.3.6")
            install("tenacity")
            install("requests")
            // PDF parsing - pdfplumber and pdfminer.six are pure Python (no native extensions)
            // Pin to 0.9.0: versions >= 0.10.0 require pypdfium2 which has no Android ARM64 wheel
            install("pdfplumber==0.9.0")
            install("pdfminer.six")
            install("Pillow")
        }
    }
}

dependencies {
    // Capacitor (aligned with package.json v6)
    implementation("com.capacitorjs:core:6.0.0")

    // AndroidX
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.webkit:webkit:1.12.1")
}
