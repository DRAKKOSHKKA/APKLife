package ru.apklife.nativeapp

import android.os.Bundle
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.PyObject
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.net.InetSocketAddress
import java.net.Socket

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webView)
        webView.settings.javaScriptEnabled = true
        webView.webViewClient = WebViewClient()

        startFlaskAndLoadWebView()
    }

    private fun startFlaskAndLoadWebView() {
        Thread {
            if (!Python.isStarted()) {
                Python.start(AndroidPlatform(this))
            }

            val py: Python = Python.getInstance()
            val module: PyObject = py.getModule("android_entry")
            module.callAttr("start_server")

            waitForServer("127.0.0.1", 5000, 60, 500)

            runOnUiThread {
                webView.loadUrl("http://127.0.0.1:5000")
            }
        }.start()
    }

    private fun waitForServer(host: String, port: Int, retries: Int, delayMs: Long) {
        repeat(retries) {
            try {
                Socket().use { socket ->
                    socket.connect(InetSocketAddress(host, port), 300)
                    return
                }
            } catch (_: Exception) {
                Thread.sleep(delayMs)
            }
        }
    }
}
