plugins {
    id("com.android.application")
    kotlin("android")
    id("com.chaquo.python")
}

android {
    namespace = "ru.apklife.nativeapp"
    compileSdk = 34

    defaultConfig {
        applicationId = "ru.apklife.nativeapp"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"

        ndk {
            abiFilters += listOf("arm64-v8a", "armeabi-v7a", "x86_64")
        }

        python {
            version = "3.10"
            pip {
                install("flask==3.1.3")
                install("requests==2.32.5")
                install("beautifulsoup4==4.14.3")
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

    sourceSets {
        getByName("main") {
            assets.srcDirs("src/main/assets")
        }
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
}

val syncPythonApp by tasks.registering(Copy::class) {
    val root = project.rootDir.parentFile
    from(root) {
        include("app.py")
        include("routes/**")
        include("services/**")
        include("templates/**")
        include("static/**")
        include("README.md")
        include("bridge.py")
        include(".gitignore")
    }
    into("src/main/python/runtime_app")
}

tasks.matching { it.name.startsWith("generate") && it.name.endsWith("PythonRequirements") }
    .configureEach {
        dependsOn(syncPythonApp)
    }
