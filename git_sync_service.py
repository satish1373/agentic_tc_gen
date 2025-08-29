
#!/usr/bin/env python3
"""
Background Git Sync Service for Replit
Runs git sync as a background service alongside your main application
"""

import threading
import time
import logging
import os
import sys
from auto_git_sync import AutoGitSync

logger = logging.getLogger(__name__)

class GitSyncService:
    """Background service for git synchronization"""
    
    def __init__(self, sync_interval=60):
        self.sync_interval = sync_interval
        self.sync_thread = None
        self.sync_instance = None
        self.running = False
    
    def start_background_sync(self):
        """Start git sync in background thread"""
        if self.running:
            logger.warning("⚠️ Git sync service already running")
            return
        
        logger.info("🚀 Starting background git sync service...")
        
        self.sync_instance = AutoGitSync(
            sync_interval=self.sync_interval,
            auto_commit=True
        )
        
        self.running = True
        self.sync_thread = threading.Thread(
            target=self._sync_worker,
            daemon=True,
            name="GitSyncService"
        )
        self.sync_thread.start()
        
        logger.info("✅ Background git sync service started")
    
    def _sync_worker(self):
        """Worker function for sync thread"""
        try:
            while self.running:
                if self.sync_instance:
                    self.sync_instance.sync_cycle()
                
                # Wait for next cycle
                time.sleep(self.sync_interval)
                
        except Exception as e:
            logger.error(f"❌ Git sync service error: {str(e)}")
        finally:
            logger.info("🏁 Git sync service worker stopped")
    
    def stop_background_sync(self):
        """Stop background git sync service"""
        if not self.running:
            logger.warning("⚠️ Git sync service not running")
            return
        
        logger.info("🛑 Stopping background git sync service...")
        self.running = False
        
        if self.sync_instance:
            self.sync_instance.stop_sync()
        
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5)
        
        logger.info("✅ Background git sync service stopped")
    
    def is_running(self):
        """Check if service is running"""
        return self.running and self.sync_thread and self.sync_thread.is_alive()
    
    def get_status(self):
        """Get service status"""
        return {
            "running": self.is_running(),
            "sync_interval": self.sync_interval,
            "thread_alive": self.sync_thread.is_alive() if self.sync_thread else False
        }

# Global service instance
git_sync_service = GitSyncService()

def start_git_sync_service(interval=60):
    """Start the git sync service"""
    git_sync_service.sync_interval = interval
    git_sync_service.start_background_sync()

def stop_git_sync_service():
    """Stop the git sync service"""
    git_sync_service.stop_background_sync()

def get_sync_status():
    """Get sync service status"""
    return git_sync_service.get_status()

if __name__ == "__main__":
    # Test the service
    print("🧪 Testing Git Sync Service...")
    
    start_git_sync_service(30)  # 30 second intervals for testing
    
    try:
        print("Service running... Press Ctrl+C to stop")
        while True:
            time.sleep(10)
            status = get_sync_status()
            print(f"Status: {status}")
    except KeyboardInterrupt:
        print("\n🛑 Stopping service...")
        stop_git_sync_service()
