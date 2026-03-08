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

        // Chaquopy configuration
        ndk {
            // Support ARM64 and x86_64 (for emulator)
            abiFilters += listOf("arm64-v8a", "x86_64")
        }

        python {
            // Python version to embed
            version = "3.11"

            // Backend Python dependencies
            // Note: These must be available as Android wheels in Chaquopy's repo
            // See: https://chaquo.com/pypi-13.1/
            pip {
                install("fastapi==0.115.0")
                install("uvicorn==0.30.6")
                install("sqlalchemy==2.0.35")
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
                // Note: Some packages may need alternatives for Android:
                // - bcrypt may not have Android wheels → use passlib with pbkdf2
                // - pdfplumber/pdfminer may not work → PDF import disabled on Android
                // - openpyxl may work with pure Python fallback
            }
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

dependencies {
    // Capacitor
    implementation("com.capacitorjs:core:7.2.0")

    // AndroidX
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.webkit:webkit:1.12.1")
}
