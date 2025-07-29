"""Tests for Repository class GitHub token environment variable pickup."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kit.repository import Repository


class TestRepositoryGitHubTokenPickup:
    """Test Repository class automatic GitHub token pickup from environment."""

    @patch.dict(os.environ, {"KIT_GITHUB_TOKEN": "test_kit_token", "GITHUB_TOKEN": "test_github_token"})
    def test_repository_picks_up_kit_github_token(self):
        """Test that Repository picks up KIT_GITHUB_TOKEN when no token provided."""
        with patch.object(Repository, "_clone_github_repo") as mock_clone:
            mock_clone.return_value = Path("/tmp/test")
            
            repo = Repository("https://github.com/test/repo")
            
            # Should have called _clone_github_repo with KIT_GITHUB_TOKEN
            mock_clone.assert_called_once_with(
                "https://github.com/test/repo", 
                "test_kit_token",  # KIT_GITHUB_TOKEN should be used
                None, 
                None
            )

    @patch.dict(os.environ, {"GITHUB_TOKEN": "test_github_token"}, clear=True)
    def test_repository_picks_up_github_token_fallback(self):
        """Test that Repository falls back to GITHUB_TOKEN when KIT_GITHUB_TOKEN not set."""
        with patch.object(Repository, "_clone_github_repo") as mock_clone:
            mock_clone.return_value = Path("/tmp/test")
            
            repo = Repository("https://github.com/test/repo")
            
            # Should have called _clone_github_repo with GITHUB_TOKEN
            mock_clone.assert_called_once_with(
                "https://github.com/test/repo", 
                "test_github_token",  # GITHUB_TOKEN should be used as fallback
                None, 
                None
            )

    @patch.dict(os.environ, {}, clear=True)
    def test_repository_no_token_when_env_empty(self):
        """Test that Repository passes None when no environment tokens are set."""
        with patch.object(Repository, "_clone_github_repo") as mock_clone:
            mock_clone.return_value = Path("/tmp/test")
            
            repo = Repository("https://github.com/test/repo")
            
            # Should have called _clone_github_repo with None
            mock_clone.assert_called_once_with(
                "https://github.com/test/repo", 
                None,  # No token should be passed
                None, 
                None
            )

    @patch.dict(os.environ, {"KIT_GITHUB_TOKEN": "env_token"})
    def test_repository_explicit_token_overrides_env(self):
        """Test that explicitly provided token overrides environment variables."""
        with patch.object(Repository, "_clone_github_repo") as mock_clone:
            mock_clone.return_value = Path("/tmp/test")
            
            repo = Repository("https://github.com/test/repo", github_token="explicit_token")
            
            # Should have called _clone_github_repo with explicit token
            mock_clone.assert_called_once_with(
                "https://github.com/test/repo", 
                "explicit_token",  # Explicit token should override environment
                None, 
                None
            )

    def test_repository_local_path_ignores_token(self):
        """Test that local paths don't use GitHub tokens."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"KIT_GITHUB_TOKEN": "test_token"}):
                # Local paths should work fine even with tokens in env
                repo = Repository(tmpdir)
                assert str(repo.local_path) == str(Path(tmpdir).absolute())

    @patch.dict(os.environ, {"KIT_GITHUB_TOKEN": "test_token"})
    def test_repository_with_ref_passes_token(self):
        """Test that Repository passes environment token even when ref is specified."""
        with patch.object(Repository, "_clone_github_repo") as mock_clone:
            mock_clone.return_value = Path("/tmp/test")
            
            repo = Repository("https://github.com/test/repo", ref="main")
            
            # Should have called _clone_github_repo with environment token and ref
            mock_clone.assert_called_once_with(
                "https://github.com/test/repo", 
                "test_token",  # Environment token should be used
                None, 
                "main"
            ) 