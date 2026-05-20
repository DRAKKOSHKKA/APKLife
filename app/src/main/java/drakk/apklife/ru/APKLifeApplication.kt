package drakk.apklife.ru

import android.app.Application
import com.google.android.material.color.DynamicColors

class APKLifeApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        DynamicColors.applyToActivitiesIfAvailable(this)
    }
}
