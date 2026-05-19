# Proguard rules for APKLife Android release build.
# Keep Chaquopy and Flask-related Python code intact.
-keep class com.chaquo.** { *; }
-dontwarn com.chaquo.**
-keepattributes *Annotation*
