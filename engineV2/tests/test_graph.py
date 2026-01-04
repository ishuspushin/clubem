"""
LangGraph workflow tests.
"""

import pytest
from unittest.mock import Mock, patch


class TestStateManager:
    """Test state manager."""
    
    @pytest.fixture
    def state_manager(self):
        """Create state manager."""
        from app.agents.state import StateManager
        return StateManager()
    
    def test_initialize_state(self, state_manager):
        """Test state initialization."""
        state = state_manager.initialize_state(
            workflow_id='test-123',
            pdf_files=['test.pdf']
        )
        
        assert state['workflow_id'] == 'test-123'
        assert len(state['pdf_files']) == 1
        assert state['retry_count'] == 0
    
    def test_update_state(self, state_manager):
        """Test state update."""
        initial_state = state_manager.initialize_state(
            workflow_id='test-123',
            pdf_files=['test.pdf']
        )
        
        updated_state = state_manager.update_state(
            initial_state,
            {'platforms': ['sharebite']}
        )
        
        assert updated_state['platforms'] == ['sharebite']
    
    def test_add_error(self, state_manager):
        """Test adding errors."""
        initial_state = state_manager.initialize_state(
            workflow_id='test-123',
            pdf_files=['test.pdf']
        )
        
        state_with_error = state_manager.add_error(
            initial_state,
            'Test error message'
        )
        
        assert len(state_with_error['errors']) == 1
        assert state_with_error['errors'][0] == 'Test error message'
    
    def test_retry_increment(self, state_manager):
        """Test retry counter increment."""
        initial_state = state_manager.initialize_state(
            workflow_id='test-123',
            pdf_files=['test.pdf']
        )
        
        state_after_retry = state_manager.increment_retry(initial_state)
        
        assert state_after_retry['retry_count'] == 1
    
    def test_should_retry(self, state_manager):
        """Test should retry logic."""
        state = state_manager.initialize_state(
            workflow_id='test-123',
            pdf_files=['test.pdf']
        )
        
        # Should retry initially
        assert state_manager.should_retry(state) is True
        
        # Max out retries
        for _ in range(3):
            state = state_manager.increment_retry(state)
        
        # Should not retry after max
        assert state_manager.should_retry(state) is False


class TestStateValidator:
    """Test state validator."""
    
    @pytest.fixture
    def validator(self):
        """Create state validator."""
        from app.agents.state import StateValidator
        return StateValidator()
    
    def test_valid_transitions(self, validator):
        """Test valid state transitions."""
        from app.agents.state import WorkflowStage
        
        # Valid transitions
        assert validator.can_transition(
            WorkflowStage.INITIALIZED,
            WorkflowStage.CLASSIFYING
        ) is True
        
        assert validator.can_transition(
            WorkflowStage.CLASSIFYING,
            WorkflowStage.EXTRACTING
        ) is True
    
    def test_invalid_transitions(self, validator):
        """Test invalid state transitions."""
        from app.agents.state import WorkflowStage
        
        # Invalid transitions
        assert validator.can_transition(
            WorkflowStage.COMPLETED,
            WorkflowStage.EXTRACTING
        ) is False
        
        assert validator.can_transition(
            WorkflowStage.INITIALIZED,
            WorkflowStage.COMPLETED
        ) is False


class TestFileHandler:
    """Test file handler utilities."""
    
    def test_ensure_directory(self, tmp_path):
        """Test directory creation."""
        from app.utils.file_handler import FileHandler
        
        test_dir = tmp_path / "test_directory"
        success = FileHandler.ensure_directory(test_dir)
        
        assert success is True
        assert test_dir.exists()
    
    def test_write_read_json(self, tmp_path):
        """Test JSON write and read."""
        from app.utils.file_handler import FileHandler
        
        test_file = tmp_path / "test.json"
        test_data = {'key': 'value', 'number': 42}
        
        # Write
        success = FileHandler.write_json(test_data, test_file)
        assert success is True
        
        # Read
        read_data = FileHandler.read_json(test_file)
        assert read_data == test_data
    
    def test_get_file_info(self, tmp_path):
        """Test file info retrieval."""
        from app.utils.file_handler import FileHandler
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        info = FileHandler.get_file_info(test_file)
        
        assert 'name' in info
        assert 'size' in info
        assert info['name'] == 'test.txt'


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
