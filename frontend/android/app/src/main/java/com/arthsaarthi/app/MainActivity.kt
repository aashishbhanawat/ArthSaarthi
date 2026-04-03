package com.arthsaarthi.app

import com.getcapacitor.BridgeActivity

class MainActivity : BridgeActivity() {
    override fun onCreate(savedInstanceState: android.os.Bundle?) {
        registerPlugin(PythonBackendPlugin::class.java)
        super.onCreate(savedInstanceState)
    }
}
