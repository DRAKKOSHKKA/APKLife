// Top-level build file for APKLife Native Android application.
// This project embeds the Flask server via Chaquopy and displays it in a WebView.
plugins {
    id("com.android.application") version "8.5.2" apply false
    kotlin("android") version "1.9.24" apply false
    id("com.chaquo.python") version "17.0.0" apply false
}
