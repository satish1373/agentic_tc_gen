
#!/usr/bin/env python3
"""
Git Sync Configuration for Replit
"""

import os
import json

class GitSyncConfig:
    """Configuration for git sync service"""
    
    def __init__(self):
        self.config_file = "git_sync_config.json"
        self.default_config = {
            "enabled": True,
            "sync_interval": 60,  # 1 minute
            "auto_commit": True,
            "auto_push": True,
            "auto_pull": True,
            "conflict_resolution": "prefer_remote",  # or "prefer_local"
            "commit_message_prefix": "Auto-sync",
            "ignore_patterns": [
                "*.log",
                "*.tmp",
                "__pycache__/",
                ".env",
                "git_sync.log"
            ]
        }
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged_config = self.default_config.copy()
                merged_config.update(config)
                return merged_config
            else:
                self.save_config(self.default_config)
                return self.default_config.copy()
        except Exception as e:
            print(f"⚠️ Error loading git sync config: {e}")
            return self.default_config.copy()
    
    def save_config(self, config=None):
        """Save configuration to file"""
        try:
            config = config or self.config
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving git sync config: {e}")
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
        self.save_config()
    
    def update(self, updates):
        """Update multiple configuration values"""
        self.config.update(updates)
        self.save_config()
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config = self.default_config.copy()
        self.save_config()

# Global config instance
git_sync_config = GitSyncConfig()

def get_config():
    """Get git sync configuration"""
    return git_sync_config

if __name__ == "__main__":
    # Display current configuration
    config = get_config()
    print("🔧 Current Git Sync Configuration:")
    for key, value in config.config.items():
        print(f"   {key}: {value}")
