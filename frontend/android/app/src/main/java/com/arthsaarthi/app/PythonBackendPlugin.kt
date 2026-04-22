package com.arthsaarthi.app

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.os.IBinder
import android.util.Log
import com.getcapacitor.JSObject
import com.getcapacitor.Plugin
import com.getcapacitor.PluginCall
import com.getcapacitor.PluginMethod
import com.getcapacitor.annotation.CapacitorPlugin
import java.net.HttpURLConnection
import java.net.URL

/**
 * Capacitor plugin that bridges the React frontend to the Python backend.
 *
 * Provides:
 * - getApiConfig() → { host, port } — mirrors Electron's ipcMain.handle('get-api-config')
 * - startBackend() → starts the BackendService if not running
 * - getBackendStatus() → { running, port }
 *
 * The frontend calls these methods via:
 *   import { PythonBackend } from './capacitor-plugins/PythonBackend';
 *   const config = await PythonBackend.getApiConfig();
 */
@CapacitorPlugin(name = "PythonBackend")
class PythonBackendPlugin : Plugin() {

    companion object {
        private const val TAG = "PythonBackendPlugin"
        private const val HEALTH_CHECK_INTERVAL_MS = 500L
        private const val HEALTH_CHECK_MAX_RETRIES = 60 // 30 seconds max wait
    }

    private var backendService: BackendService? = null
    private var isServiceBound = false

    private val serviceConnection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, service: IBinder?) {
            val binder = service as BackendService.BackendBinder
            backendService = binder.getService()
            isServiceBound = true
            Log.i(TAG, "BackendService connected")
        }

        override fun onServiceDisconnected(name: ComponentName?) {
            backendService = null
            isServiceBound = false
            Log.w(TAG, "BackendService disconnected")
        }
    }

    override fun load() {
        super.load()
        // Start and bind to the BackendService when the plugin loads
        val intent = Intent(context, BackendService::class.java)
        context.startService(intent)
        context.bindService(intent, serviceConnection, Context.BIND_AUTO_CREATE)
        Log.i(TAG, "PythonBackendPlugin loaded — starting BackendService")
    }

    /**
     * Returns the API configuration (host and port) for the frontend.
     * Waits until the backend is fully ready (health check passes).
     */
    @PluginMethod
    fun getApiConfig(call: PluginCall) {
        Thread {
            try {
                // Wait for the backend to start
                val port = waitForBackendReady()
                if (port > 0) {
                    val result = JSObject()
                    result.put("host", "127.0.0.1")
                    result.put("port", port)
                    call.resolve(result)
                } else {
                    call.reject("Backend failed to start within timeout")
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error getting API config", e)
                call.reject("Backend error: ${e.message}")
            }
        }.start()
    }

    /**
     * Returns the current backend status.
     */
    @PluginMethod
    fun getBackendStatus(call: PluginCall) {
        val result = JSObject()
        result.put("running", BackendService.isRunning.get())
        result.put("port", BackendService.backendPort)
        call.resolve(result)
    }

    /**
     * Waits for the backend HTTP server to be ready by polling a health endpoint.
     * Returns the port number when ready, or -1 if timeout.
     */
    private fun waitForBackendReady(): Int {
        for (i in 0 until HEALTH_CHECK_MAX_RETRIES) {
            val port = BackendService.backendPort
            if (port > 0 && BackendService.isRunning.get()) {
                try {
                    val url = URL("http://127.0.0.1:$port/api/v1/auth/status")
                    val conn = url.openConnection() as HttpURLConnection
                    conn.connectTimeout = 2000
                    conn.readTimeout = 2000
                    conn.requestMethod = "GET"
                    val responseCode = conn.responseCode
                    conn.disconnect()

                    if (responseCode in 200..299) {
                        Log.i(TAG, "Backend is ready on port $port (attempt ${i + 1})")
                        return port
                    }
                } catch (e: Exception) {
                    // Server not yet ready — keep waiting
                    Log.d(TAG, "Health check attempt ${i + 1} failed: ${e.message}")
                }
            }
            Thread.sleep(HEALTH_CHECK_INTERVAL_MS)
        }
        Log.e(TAG, "Backend health check timed out after $HEALTH_CHECK_MAX_RETRIES retries")
        return -1
    }

    override fun handleOnDestroy() {
        super.handleOnDestroy()
        if (isServiceBound) {
            context.unbindService(serviceConnection)
            isServiceBound = false
        }
    }
}
