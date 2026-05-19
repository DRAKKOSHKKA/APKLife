package ru.apklife.app

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class UpdateCheckerTest {

    @Test
    fun testIsNewerVersion() {
        // Simple cases
        assertTrue(UpdateChecker.isNewerVersion("0.0.1", "0.0.2"))
        assertFalse(UpdateChecker.isNewerVersion("0.0.2", "0.0.1"))
        assertFalse(UpdateChecker.isNewerVersion("0.0.1", "0.0.1"))
        
        // Multiple digits
        assertTrue(UpdateChecker.isNewerVersion("1.0.9", "1.1.0"))
        assertTrue(UpdateChecker.isNewerVersion("1.9.9", "2.0.0"))
        
        // Missing parts
        assertTrue(UpdateChecker.isNewerVersion("1.0", "1.0.1"))
        assertFalse(UpdateChecker.isNewerVersion("1.0.1", "1.0"))
        
        // Different lengths
        assertTrue(UpdateChecker.isNewerVersion("1", "1.1"))
        assertFalse(UpdateChecker.isNewerVersion("1.1", "1"))
    }
}
