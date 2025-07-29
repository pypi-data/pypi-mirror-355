"""
Tests for OpenAI-compatible provider functionality
"""

import pytest
from unittest.mock import Mock, patch
from feynman_learning.ai_explainer import OpenAICompatibleProvider, AIExplainer


class TestOpenAICompatibleProvider:
    """Test cases for OpenAI-compatible provider"""
    
    def test_init_default_values(self):
        """Test provider initialization with default values"""
        provider = OpenAICompatibleProvider(api_key="test-key")
        
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://api.openai.com/v1"
        assert provider.model == "gpt-3.5-turbo"
        assert provider.timeout is None
        assert provider.organization is None
    
    def test_init_custom_values(self):
        """Test provider initialization with custom values"""
        provider = OpenAICompatibleProvider(
            api_key="test-key",
            base_url="http://custom-endpoint.com/v1",
            model="custom-model",
            timeout=30.0,
            organization="test-org"
        )
        
        assert provider.api_key == "test-key"
        assert provider.base_url == "http://custom-endpoint.com/v1"
        assert provider.model == "custom-model"
        assert provider.timeout == 30.0
        assert provider.organization == "test-org"
    
    @patch('openai.OpenAI')
    def test_generate_response_success(self, mock_openai):
        """Test successful response generation"""
        # Mock the OpenAI client and response
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response content"
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test the provider
        provider = OpenAICompatibleProvider(
            api_key="dummy-key",
            base_url="http://test-endpoint.com/v1",
            model="test-model"
        )
        
        result = provider.generate_response("test prompt", max_tokens=100)
        
        # Verify the result
        assert result == "Test response content"
        
        # Verify the OpenAI client was called correctly
        mock_openai.assert_called_once_with(
            api_key="dummy-key",
            base_url="http://test-endpoint.com/v1",
            timeout=None,
            organization=None
        )
        
        mock_client.chat.completions.create.assert_called_once_with(
            model="test-model",
            messages=[{"role": "user", "content": "test prompt"}],
            max_tokens=100,
            temperature=0.7
        )
    
    @patch('openai.OpenAI')
    def test_generate_response_with_timeout(self, mock_openai):
        """Test response generation with custom timeout"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        provider = OpenAICompatibleProvider(
            api_key="dummy-key",
            base_url="http://test-endpoint.com/v1",
            timeout=45.0
        )
        
        provider.generate_response("test prompt")
        
        # Verify timeout was passed to OpenAI client
        mock_openai.assert_called_once_with(
            api_key="dummy-key",
            base_url="http://test-endpoint.com/v1",
            timeout=45.0,
            organization=None
        )
    
    def test_generate_response_import_error(self):
        """Test handling of OpenAI library import error"""
        with patch('openai.OpenAI', side_effect=ImportError):
            provider = OpenAICompatibleProvider(api_key="test-key")
            result = provider.generate_response("test prompt")
            
            assert result == "OpenAI library not installed. Run: pip install openai"
    
    @patch('openai.OpenAI')
    def test_generate_response_api_error(self, mock_openai):
        """Test handling of API errors"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        provider = OpenAICompatibleProvider(api_key="test-key")
        result = provider.generate_response("test prompt")
        
        assert result == "Error generating response: API Error"
    
    def test_integration_with_ai_explainer(self):
        """Test that the provider works with AIExplainer"""
        provider = OpenAICompatibleProvider(api_key="test-key")
        ai_explainer = AIExplainer(provider)
        
        # Verify the provider is properly set
        assert ai_explainer.provider == provider
        assert isinstance(ai_explainer.provider, OpenAICompatibleProvider)


class TestProviderInterface:
    """Test provider interface and functionality"""
    
    def test_openai_compatible_provider_interface(self):
        """Test that OpenAI-compatible provider has the expected interface"""
        compatible_provider = OpenAICompatibleProvider(api_key="test-key")
        
        # Should have the required interface
        assert hasattr(compatible_provider, 'generate_response')
        
        # Check method signature
        import inspect
        sig = inspect.signature(compatible_provider.generate_response)
        expected_params = {'prompt', 'max_tokens'}
        actual_params = set(sig.parameters.keys())
        
        assert expected_params.issubset(actual_params)


if __name__ == "__main__":
    pytest.main([__file__]) 