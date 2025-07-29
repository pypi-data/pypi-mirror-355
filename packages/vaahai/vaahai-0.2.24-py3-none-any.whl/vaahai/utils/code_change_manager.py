"""
Code change manager for applying suggested code changes.

This module provides utilities for safely applying suggested code changes
to original files with backup and validation functionality.
"""

import os
import shutil
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
import json
import configparser


class CodeChangeManager:
    """
    Manages the application of code changes to files.
    
    This class handles the safe application of suggested code changes to original
    files, including creating backups and validating changes before applying them.
    It supports batch processing, undo operations, and configuration options.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the code change manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Set up backup directory
        self.backup_dir = self.config.get('backup_dir', os.path.expanduser("~/.vaahai/backups"))
        self.backup_history_file = os.path.join(self.backup_dir, "backup_history.json")
        
        # Initialize change tracking
        self.changes_applied = []
        self.changes_rejected = []
        self.pending_changes = []
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Load backup history if it exists
        self._load_backup_history()
        
        # For testing purposes
        self._test_mode = False
        self._test_confirm_response = 'y'
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Dictionary containing configuration options
        """
        default_config = {
            'backup_dir': os.path.expanduser("~/.vaahai/backups"),
            'max_backup_age_days': 30,
            'confirm_changes': True,
            'create_git_commits': False,
            'dry_run': False
        }
        
        if not config_path:
            return default_config
            
        if not os.path.exists(config_path):
            self.logger.warning(f"Config file not found: {config_path}, using defaults")
            return default_config
            
        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            
            if 'file_modification' in config:
                file_mod_config = config['file_modification']
                return {
                    'backup_dir': file_mod_config.get('backup_dir', default_config['backup_dir']),
                    'max_backup_age_days': file_mod_config.getint('max_backup_age_days', default_config['max_backup_age_days']),
                    'confirm_changes': file_mod_config.getboolean('confirm_changes', default_config['confirm_changes']),
                    'create_git_commits': file_mod_config.getboolean('create_git_commits', default_config['create_git_commits']),
                    'dry_run': file_mod_config.getboolean('dry_run', default_config['dry_run'])
                }
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            
        return default_config
    
    def _load_backup_history(self) -> None:
        """Load backup history from file if it exists."""
        self.backup_history = {}
        
        if os.path.exists(self.backup_history_file):
            try:
                with open(self.backup_history_file, 'r', encoding='utf-8') as f:
                    self.backup_history = json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading backup history: {str(e)}")
    
    def _save_backup_history(self) -> None:
        """Save backup history to file."""
        try:
            with open(self.backup_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.backup_history, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving backup history: {str(e)}")
    
    def backup_file(self, file_path: str) -> str:
        """
        Create a backup of the specified file.
        
        Args:
            file_path: Path to the file to back up
            
        Returns:
            Path to the backup file
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Cannot backup non-existent file: {file_path}")
            
        # Create a timestamped backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        backup_path = os.path.join(
            self.backup_dir, 
            f"{filename}.{timestamp}.bak"
        )
        
        # Create the backup
        shutil.copy2(file_path, backup_path)
        
        # Update backup history
        if file_path not in self.backup_history:
            self.backup_history[file_path] = []
        
        self.backup_history[file_path].append({
            'backup_path': backup_path,
            'timestamp': timestamp
        })
        
        self._save_backup_history()
        
        return backup_path
    
    def apply_change(self, file_path: str, line_number: int, 
                    original_code: str, suggested_code: str) -> bool:
        """
        Apply a suggested code change to a file.
        
        Args:
            file_path: Path to the file to modify
            line_number: Line number where the change starts
            original_code: Original code snippet
            suggested_code: Suggested code snippet
            
        Returns:
            True if the change was applied successfully, False otherwise
        """
        # Build basic change metadata early so we can reuse it for different paths
        change_info = {
            'file_path': file_path,
            'line_number': line_number,
            'original_code': original_code,
            'suggested_code': suggested_code,
            'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S")
        }

        # Dry-run mode – do not touch the file system but pretend success
        if self.config.get('dry_run', False):
            self.logger.info(f"DRY RUN: Would apply change to {file_path} at line {line_number}")
            # Tag with dry_run flag and store in applied list so that tests can verify bookkeeping
            self.changes_applied.append({**change_info, 'dry_run': True})
            return True

        # Handle interactive confirmation if enabled and not in dry-run mode
        if self.config.get('confirm_changes', True) and not self.config.get('dry_run', False):
            try:
                # In test mode, use the predefined response
                if self._test_mode:
                    response = self._test_confirm_response
                    self.logger.debug(f"Using test response: {response}")
                else:
                    response = input(f"Apply change to {file_path} at line {line_number}? (y/N): ")
            except EOFError:
                response = 'n'  # In non-interactive environments default to no
            if response.lower() != 'y':
                # Record rejected change and exit early
                self.changes_rejected.append({**change_info, 'reason': 'user_rejected'})
                self.logger.info("Change rejected by user")
                return False

        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            return False
            
        try:
            # Create a backup first
            backup_path = self.backup_file(file_path)
            
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Validate that the original code matches what's in the file
            original_lines = original_code.splitlines()
            file_lines = lines[line_number-1:line_number-1+len(original_lines)]
            file_content = ''.join(file_lines)
            
            # Strip whitespace for comparison
            if file_content.strip() != original_code.strip():
                self.logger.error(f"Original code doesn't match file content in {file_path} at line {line_number}")
                return False
            
            # Replace the lines with the suggested code
            suggested_lines = suggested_code.splitlines(True)  # Keep line endings
            lines[line_number-1:line_number-1+len(original_lines)] = suggested_lines
            
            # Write the modified content back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            # Record the applied change
            change_info.update({'backup_path': backup_path, 'dry_run': False})
            self.changes_applied.append(change_info)
            
            self.logger.info(f"Successfully applied change to {file_path} at line {line_number}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying change to {file_path}: {str(e)}")
            # If anything goes wrong, try to restore from backup
            if 'backup_path' in locals() and os.path.exists(backup_path):
                self.logger.info(f"Restoring from backup: {backup_path}")
                shutil.copy2(backup_path, file_path)
            return False
    
    def add_pending_change(self, file_path: str, line_number: int,
                          original_code: str, suggested_code: str) -> None:
        """
        Add a change to the pending changes list for batch processing.
        
        Args:
            file_path: Path to the file to modify
            line_number: Line number where the change starts
            original_code: Original code snippet
            suggested_code: Suggested code snippet
        """
        self.pending_changes.append({
            'file_path': file_path,
            'line_number': line_number,
            'original_code': original_code,
            'suggested_code': suggested_code
        })
    
    def apply_pending_changes(self) -> Dict[str, Any]:
        """
        Apply all pending changes in batch.
        
        Returns:
            Dictionary with results of the batch operation
        """
        results = {
            'total': len(self.pending_changes),
            'applied': 0,
            'failed': 0,
            'details': []
        }
        
        # Group changes by file to minimize file operations
        changes_by_file = {}
        for change in self.pending_changes:
            file_path = change['file_path']
            if file_path not in changes_by_file:
                changes_by_file[file_path] = []
            changes_by_file[file_path].append(change)
        
        # Process each file's changes
        for file_path, changes in changes_by_file.items():
            # Sort changes by line number in reverse order to avoid line number shifting
            changes.sort(key=lambda x: x['line_number'], reverse=True)
            
            for change in changes:
                success = self.apply_change(
                    change['file_path'],
                    change['line_number'],
                    change['original_code'],
                    change['suggested_code']
                )
                
                if success:
                    results['applied'] += 1
                else:
                    results['failed'] += 1
                
                results['details'].append({
                    'file_path': change['file_path'],
                    'line_number': change['line_number'],
                    'success': success
                })
        
        # Clear pending changes
        self.pending_changes = []
        
        return results
    
    def reject_change(self, file_path: str, line_number: int, 
                     original_code: str = "", suggested_code: str = "") -> None:
        """
        Record a rejected code change.
        
        Args:
            file_path: Path to the file
            line_number: Line number where the change would have started
            original_code: Optional original code snippet
            suggested_code: Optional suggested code snippet
        """
        self.changes_rejected.append({
            'file_path': file_path,
            'line_number': line_number,
            'original_code': original_code,
            'suggested_code': suggested_code,
            'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S")
        })
    
    def undo_last_change(self) -> bool:
        """
        Undo the last applied change by restoring from backup.
        
        Returns:
            True if the change was undone successfully, False otherwise
        """
        if not self.changes_applied:
            self.logger.warning("No changes to undo")
            return False
        
        last_change = self.changes_applied.pop()
        file_path = last_change['file_path']
        backup_path = last_change['backup_path']
        
        try:
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, file_path)
                self.logger.info(f"Undid change to {file_path} using backup {backup_path}")
                return True
            else:
                self.logger.error(f"Backup file not found: {backup_path}")
                return False
        except Exception as e:
            self.logger.error(f"Error undoing change: {str(e)}")
            return False
    
    def get_latest_backup(self, file_path: str) -> Optional[str]:
        """
        Get the path to the latest backup of a file.
        
        Args:
            file_path: Path to the original file
            
        Returns:
            Path to the latest backup file, or None if no backups exist
        """
        if file_path not in self.backup_history or not self.backup_history[file_path]:
            return None
        
        # Sort backups by timestamp (newest first)
        backups = sorted(
            self.backup_history[file_path],
            key=lambda x: x['timestamp'],
            reverse=True
        )
        
        if backups:
            return backups[0]['backup_path']
        
        return None
    
    def restore_from_backup(self, file_path: str, backup_path: Optional[str] = None) -> bool:
        """
        Restore a file from backup.
        
        Args:
            file_path: Path to the file to restore
            backup_path: Optional specific backup to restore from.
                         If not provided, the latest backup will be used.
                         
        Returns:
            True if the file was restored successfully, False otherwise
        """
        if not backup_path:
            backup_path = self.get_latest_backup(file_path)
            
        if not backup_path or not os.path.exists(backup_path):
            self.logger.error(f"Backup not found for {file_path}")
            return False
            
        try:
            shutil.copy2(backup_path, file_path)
            self.logger.info(f"Restored {file_path} from backup {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error restoring from backup: {str(e)}")
            return False
    
    def get_summary(self) -> Dict:
        """
        Get a summary of applied and rejected changes.
        
        Returns:
            Dictionary containing summary information
        """
        return {
            'applied': len(self.changes_applied),
            'rejected': len(self.changes_rejected),
            'pending': len(self.pending_changes),
            'applied_changes': self.changes_applied,
            'rejected_changes': self.changes_rejected,
            'pending_changes': self.pending_changes
        }
    
    def cleanup_old_backups(self, max_age_days: Optional[int] = None) -> int:
        """
        Clean up backup files older than the specified age.
        
        Args:
            max_age_days: Maximum age of backups in days.
                          If not provided, the value from config will be used.
                          
        Returns:
            Number of backup files removed
        """
        if max_age_days is None:
            max_age_days = self.config.get('max_backup_age_days', 30)
            
        if max_age_days <= 0:
            return 0
            
        cutoff_date = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
        removed_count = 0
        
        # Iterate through all backup files
        for root, _, files in os.walk(self.backup_dir):
            for file in files:
                if file == "backup_history.json":
                    continue
                    
                file_path = os.path.join(root, file)
                file_mtime = os.path.getmtime(file_path)
                
                if file_mtime < cutoff_date:
                    try:
                        os.remove(file_path)
                        removed_count += 1
                    except Exception as e:
                        self.logger.error(f"Error removing old backup {file_path}: {str(e)}")
        
        # Update backup history
        self._update_backup_history_after_cleanup()
        
        return removed_count
    
    def _update_backup_history_after_cleanup(self) -> None:
        """Update backup history after cleanup to remove references to deleted files."""
        for file_path in list(self.backup_history.keys()):
            self.backup_history[file_path] = [
                backup for backup in self.backup_history[file_path]
                if os.path.exists(backup['backup_path'])
            ]
            
            if not self.backup_history[file_path]:
                del self.backup_history[file_path]
        
        self._save_backup_history()

    # For testing purposes
    def set_test_mode(self, enabled: bool = True, confirm_response: str = 'y'):
        """
        Enable or disable test mode for non-interactive testing.
        
        Args:
            enabled: Whether to enable test mode
            confirm_response: Response to use for confirmation prompts in test mode
        """
        self._test_mode = enabled
        self._test_confirm_response = confirm_response
        self.logger.debug(f"Test mode {'enabled' if enabled else 'disabled'}")
