package drakk.apklife.ru

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.util.Log
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import org.json.JSONArray
import java.net.HttpURLConnection
import java.net.URL
import java.util.Scanner

class UpdateChecker(private val context: Context) {

    companion object {
        private const val TAG = "UpdateChecker"
        private const val REPO_URL = "https://api.github.com/repos/DRAKKOSHKKA/APKLife/releases"
        private const val DOWNLOAD_URL = "https://github.com/DRAKKOSHKKA/APKLife/releases"

        internal fun isNewerVersion(current: String, latest: String): Boolean {
            val currentParts = current.split(".").map { it.toIntOrNull() ?: 0 }
            val latestParts = latest.split(".").map { it.toIntOrNull() ?: 0 }
            
            val length = maxOf(currentParts.size, latestParts.size)
            for (i in 0 until length) {
                val curr = if (i < currentParts.size) currentParts[i] else 0
                val lat = if (i < latestParts.size) latestParts[i] else 0
                if (lat > curr) return true
                if (lat < curr) return false
            }
            return false
        }
    }

    interface UpdateCallback {
        fun onUpdateAvailable(latestVersion: String, downloadUrl: String)
        fun onNoUpdate()
        fun onError(e: Exception)
    }

    fun checkForUpdates(currentVersion: String, callback: UpdateCallback) {
        Thread {
            try {
                val url = URL(REPO_URL)
                val connection = url.openConnection() as HttpURLConnection
                connection.requestMethod = "GET"
                connection.connectTimeout = 5000
                connection.readTimeout = 5000

                if (connection.responseCode == 200) {
                    val scanner = Scanner(connection.inputStream)
                    val response = StringBuilder()
                    while (scanner.hasNextLine()) {
                        response.append(scanner.nextLine())
                    }
                    scanner.close()

                    val releases = JSONArray(response.toString())
                    if (releases.length() > 0) {
                        val latestRelease = releases.getJSONObject(0)
                        val latestVersion = latestRelease.getString("tag_name").replace("v", "")
                        
                        if (UpdateChecker.isNewerVersion(currentVersion, latestVersion)) {
                            callback.onUpdateAvailable(latestVersion, DOWNLOAD_URL)
                        } else {
                            callback.onNoUpdate()
                        }
                    } else {
                        callback.onNoUpdate()
                    }
                } else {
                    callback.onError(Exception("HTTP error: ${connection.responseCode}"))
                }
            } catch (e: Exception) {
                Log.e(TAG, "Update check failed", e)
                callback.onError(e)
            }
        }.start()
    }

    fun showUpdateDialog(latestVersion: String, downloadUrl: String) {
        MaterialAlertDialogBuilder(context)
            .setTitle("Обновление доступно")
            .setMessage("Доступна новая версия $latestVersion. Хотите обновить приложение?")
            .setPositiveButton("Обновить") { _, _ ->
                val intent = Intent(Intent.ACTION_VIEW, Uri.parse(downloadUrl))
                context.startActivity(intent)
            }
            .setNegativeButton("Позже", null)
            .show()
    }
}
