plugins {
    id("com.android.application")
    kotlin("android")
    id("com.chaquo.python")
}

android {
    namespace = "drakk.apklife.ru"
    compileSdk = 34

    buildFeatures {
        buildConfig = true
    }

    defaultConfig {
        applicationId = "drakk.apklife.ru"
        minSdk = 24
        targetSdk = 34
        versionCode = 2
        versionName = "0.1.4"

        // Поддерживаемые архитектуры процессоров Android-устройств
        ndk {
            abiFilters += listOf("arm64-v8a", "x86_64")
        }

        // Конфигурация Chaquopy — встроенный Python-интерпретатор
        // Все Python-зависимости Flask-приложения устанавливаются здесь
        chaquopy {
            defaultConfig {
                version = "3.12"
                buildPython("python")
                pip {
                    install("flask==3.1.3")
                    install("requests==2.32.5")
                    install("beautifulsoup4==4.14.3")
                }
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
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
    // Jetpack Core & UI
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.swiperefreshlayout:swiperefreshlayout:1.1.0")
    implementation("androidx.core:core-splashscreen:1.0.1")
    implementation("androidx.webkit:webkit:1.11.0")
    implementation("androidx.dynamicanimation:dynamicanimation-ktx:1.0.0-alpha03")

    testImplementation("junit:junit:4.13.2")
}

// Задача: копирование Python-кода Flask-приложения в assets Chaquopy
// При каждой сборке свежий код из корня проекта попадает в APK
val syncPythonApp by tasks.registering(Copy::class) {
    val root = project.rootDir.parentFile
    from(root) {
        include("app.py")
        include("config.py")
        include("bridge.py")
        include("routes/**")
        include("services/**")
        include("templates/**")
        include("static/**")
    }
    into("src/main/python/runtime_app")
}

tasks.matching { it.name.startsWith("generate") && it.name.endsWith("PythonRequirements") }
    .configureEach {
        dependsOn(syncPythonApp)
    }
