package ru.apklife.app

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class UpdateCheckerTest {

    @Test
    fun testIsNewerVersion() {
        val checker = UpdateChecker(null as android.content.Context?) // Context is not used in isNewerVersion
        
        // Simple cases
        assertTrue(checker.isNewerVersion("0.0.1", "0.0.2"))
        assertFalse(checker.isNewerVersion("0.0.2", "0.0.1"))
        assertFalse(checker.isNewerVersion("0.0.1", "0.0.1"))
        
        // Multiple digits
        assertTrue(checker.isNewerVersion("1.0.9", "1.1.0"))
        assertTrue(checker.isNewerVersion("1.9.9", "2.0.0"))
        
        // Missing parts
        assertTrue(checker.isNewerVersion("1.0", "1.0.1"))
        assertFalse(checker.isNewerVersion("1.0.1", "1.0"))
        
        // Different lengths
        assertTrue(checker.isNewerVersion("1", "1.1"))
        assertFalse(checker.isNewerVersion("1.1", "1"))
    }
}
