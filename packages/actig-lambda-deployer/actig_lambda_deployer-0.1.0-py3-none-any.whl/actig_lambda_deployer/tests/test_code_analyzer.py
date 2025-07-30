"""
Tests for the LambdaCodeAnalyzer module
"""

import pytest
import json
from unittest.mock import Mock, patch
from pathlib import Path

# Use relative imports for the module structure
from ..code_analyzer import LambdaCodeAnalyzer, PythonAnalysisVisitor
from ..utils.exceptions import CodeAnalysisError


class TestLambdaCodeAnalyzer:
    """Test cases for LambdaCodeAnalyzer"""
    
    def test_analyze_code_success(self, mock_client_manager, mock_bedrock_client, sample_lambda_project):
        """Test successful code analysis"""
        # Setup
        mock_client_manager.get_client.return_value = mock_bedrock_client
        analyzer = LambdaCodeAnalyzer(mock_client_manager)
        
        # Execute
        result = analyzer.analyze_code(sample_lambda_project)
        
        # Verify
        assert result['source_path'] == str(sample_lambda_project)
        assert 'lambda_function.py' in result['source_files']
        assert 'static_analysis' in result
        assert 'ai_analysis' in result
        assert 'recommendations' in result
        
        # Check static analysis results
        static_analysis = result['static_analysis']
        assert 'imports' in static_analysis
        assert 'handlers' in static_analysis
        assert 'dependencies' in static_analysis
        assert 'complexity_score' in static_analysis
        
        # Verify expected imports are detected
        imports = static_analysis['imports']
        assert 'json' in imports
        assert 'boto3' in imports
        assert 'os' in imports
        
        # Verify handler detection
        handlers = static_analysis['handlers']
        assert 'lambda_handler' in handlers
    
    def test_analyze_code_with_syntax_error(self, mock_client_manager, temp_dir):
        """Test code analysis with syntax error"""
        # Create invalid Python file
        invalid_file = temp_dir / "invalid.py"
        invalid_file.write_text("def invalid_syntax(:\n    pass")
        
        analyzer = LambdaCodeAnalyzer(mock_client_manager)
        
        # Should raise CodeAnalysisError
        with pytest.raises(CodeAnalysisError) as exc_info:
            analyzer.analyze_code(temp_dir)
        
        assert "Syntax error" in str(exc_info.value)
    
    def test_analyze_code_bedrock_fallback(self, mock_client_manager, sample_lambda_project):
        """Test fallback when Bedrock analysis fails"""
        # Setup Bedrock client to fail
        mock_bedrock_client = Mock()
        mock_bedrock_client.invoke_model.side_effect = Exception("Bedrock error")
        mock_client_manager.get_client.return_value = mock_bedrock_client
        
        analyzer = LambdaCodeAnalyzer(mock_client_manager)
        
        # Execute
        result = analyzer.analyze_code(sample_lambda_project)
        
        # Should still work with fallback analysis
        assert result['ai_analysis']['handler_function'] == 'lambda_function.lambda_handler'
        assert result['ai_analysis']['runtime_version'] == 'python3.12'
    
    def test_extract_dependencies(self, mock_client_manager):
        """Test dependency extraction from imports"""
        analyzer = LambdaCodeAnalyzer(mock_client_manager)
        
        imports = ['boto3', 'requests', 'json', 'os', 'numpy', 'unknown_package']
        dependencies = analyzer._extract_dependencies(imports)
        
        # Should include third-party packages
        assert 'boto3' in dependencies
        assert 'requests' in dependencies
        assert 'numpy' in dependencies
        assert 'unknown_package' in dependencies
        
        # Should not include built-in modules
        assert 'json' not in dependencies
        assert 'os' not in dependencies
    
    def test_generate_recommendations(self, mock_client_manager):
        """Test recommendation generation"""
        analyzer = LambdaCodeAnalyzer(mock_client_manager)
        
        static_analysis = {
            'complexity_score': 25,
            'imports': ['boto3', 'numpy'],
            'dependencies': ['boto3', 'numpy', 'requests'],
            'handlers': ['lambda_handler']
        }
        
        ai_analysis = {
            'estimated_memory': 1536,
            'estimated_timeout': 400,
            'security_recommendations': ['Use IAM roles'],
            'optimization_suggestions': ['Cache connections']
        }
        
        recommendations = analyzer._generate_recommendations(static_analysis, ai_analysis)
        
        # Should have memory recommendations due to high complexity and heavy packages
        assert 'memory_optimization' in recommendations
        assert len(recommendations['memory_optimization']) > 0
        
        # Should have performance recommendations
        assert 'performance_optimization' in recommendations
        
        # Should include AI recommendations
        assert 'security_recommendations' in recommendations
        assert 'Use IAM roles' in recommendations['security_recommendations']


class TestPythonAnalysisVisitor:
    """Test cases for PythonAnalysisVisitor"""
    
    def test_visit_import(self):
        """Test import detection"""
        import ast
        
        code = """
import json
import boto3.client
from datetime import datetime
from pathlib import Path
"""
        
        tree = ast.parse(code)
        visitor = PythonAnalysisVisitor()
        visitor.visit(tree)
        
        # Check detected imports
        assert 'json' in visitor.imports
        assert 'boto3' in visitor.imports
        assert 'datetime' in visitor.imports
        assert 'pathlib' in visitor.imports
    
    def test_visit_function_def(self):
        """Test function detection and handler identification"""
        import ast
        
        code = """
def lambda_handler(event, context):
    return {'statusCode': 200}

def helper_function():
    pass

def main_handler(event, context):
    pass
"""
        
        tree = ast.parse(code)
        visitor = PythonAnalysisVisitor()
        visitor.visit(tree)
        
        # Should detect handler functions
        assert 'lambda_handler' in visitor.handlers
        assert 'main_handler' in visitor.handlers
        assert 'helper_function' not in visitor.handlers
        
        # Should count complexity (number of functions)
        assert visitor.complexity == 3


class TestCodeAnalysisIntegration:
    """Integration tests for code analysis"""
    
    @pytest.mark.integration
    def test_real_bedrock_analysis(self, real_client_manager, sample_lambda_project):
        """Integration test with real Bedrock API"""
        analyzer = LambdaCodeAnalyzer(real_client_manager)
        
        # This test requires real AWS credentials and Bedrock access
        result = analyzer.analyze_code(sample_lambda_project)
        
        # Verify AI analysis results
        ai_analysis = result['ai_analysis']
        assert ai_analysis['handler_function']
        assert ai_analysis['runtime_version']
        assert isinstance(ai_analysis['estimated_memory'], int)
        assert isinstance(ai_analysis['estimated_timeout'], int)
        assert ai_analysis['base_image_recommendation']
    
    def test_empty_directory(self, mock_client_manager, temp_dir):
        """Test analysis of directory with no Python files"""
        analyzer = LambdaCodeAnalyzer(mock_client_manager)
        
        # Should raise CodeAnalysisError
        with pytest.raises(CodeAnalysisError):
            analyzer.analyze_code(temp_dir)
    
    def test_complex_project_structure(self, mock_client_manager, mock_bedrock_client, temp_dir):
        """Test analysis of complex project with multiple files"""
        # Setup complex project structure
        (temp_dir / 'src').mkdir()
        (temp_dir / 'src' / '__init__.py').write_text('')
        (temp_dir / 'src' / 'main.py').write_text('''
import json
import boto3
from src.utils import helper

def lambda_handler(event, context):
    return helper.process(event)
''')
        
        (temp_dir / 'src' / 'utils.py').write_text('''
import requests
import pandas as pd

def helper_process(data):
    return pd.DataFrame(data)
''')
        
        mock_client_manager.get_client.return_value = mock_bedrock_client
        analyzer = LambdaCodeAnalyzer(mock_client_manager)
        
        result = analyzer.analyze_code(temp_dir)
        
        # Should detect imports from multiple files
        imports = result['static_analysis']['imports']
        assert 'json' in imports
        assert 'boto3' in imports
        assert 'requests' in imports
        assert 'pandas' in imports
        
        # Should include dependencies
        dependencies = result['static_analysis']['dependencies']
        assert 'boto3' in dependencies
        assert 'requests' in dependencies
        assert 'pandas' in dependencies