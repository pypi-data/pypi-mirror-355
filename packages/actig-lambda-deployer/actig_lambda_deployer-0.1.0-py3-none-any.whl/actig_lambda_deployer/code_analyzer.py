import json
import ast
from pathlib import Path
from typing import Dict, List, Any
from .utils.exceptions import CodeAnalysisError

class LambdaCodeAnalyzer:
    """Analyzes Lambda function code using AWS Bedrock Claude"""
    
    def __init__(self, client_manager):
        self.client_manager = client_manager
        self.bedrock_client = client_manager.get_client('bedrock-runtime')
    
    def analyze_code(self, source_path: Path) -> Dict[str, Any]:
        """Comprehensive Lambda code analysis"""
        try:
            # Read source files
            source_files = self._read_source_files(source_path)
            
            # Validate that we have Python files
            python_files = [f for f in source_files.keys() if f.endswith('.py')]
            if not python_files:
                raise CodeAnalysisError(f"No Python files found in source path: {source_path}")
            
            # Basic static analysis
            static_analysis = self._static_analysis(source_files)
            
            # AI-powered analysis using Claude
            ai_analysis = self._ai_analysis(source_files)
            
            # Combine results
            return {
                'source_path': str(source_path),
                'source_files': source_files,
                'static_analysis': static_analysis,
                'ai_analysis': ai_analysis,
                'recommendations': self._generate_recommendations(
                    static_analysis, ai_analysis
                )
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Code analysis failed: {e}")
    
    def _read_source_files(self, source_path: Path) -> Dict[str, str]:
        """Read all Python and configuration files"""
        source_files = {}
        
        for file_path in source_path.rglob('*.py'):
            with open(file_path, 'r', encoding='utf-8') as f:
                relative_path = file_path.relative_to(source_path)
                source_files[str(relative_path)] = f.read()
        
        # Check for existing requirements.txt
        req_file = source_path / 'requirements.txt'
        if req_file.exists():
            with open(req_file, 'r') as f:
                source_files['requirements.txt'] = f.read()
        
        return source_files
    
    def _static_analysis(self, source_files: Dict[str, str]) -> Dict[str, Any]:
        """Basic static analysis of Python code"""
        analysis = {
            'imports': set(),
            'handlers': [],
            'dependencies': [],
            'complexity_score': 0
        }
        
        for filename, content in source_files.items():
            if filename.endswith('.py'):
                try:
                    tree = ast.parse(content)
                    visitor = PythonAnalysisVisitor()
                    visitor.visit(tree)
                    
                    analysis['imports'].update(visitor.imports)
                    analysis['handlers'].extend(visitor.handlers)
                    analysis['complexity_score'] += visitor.complexity
                    
                except SyntaxError as e:
                    raise CodeAnalysisError(f"Syntax error in {filename}: {e}")
        
        analysis['imports'] = list(analysis['imports'])
        
        # Extract dependencies from imports
        analysis['dependencies'] = self._extract_dependencies(analysis['imports'])
        
        return analysis
    
    def _ai_analysis(self, source_files: Dict[str, str]) -> Dict[str, Any]:
        """AI-powered code analysis using Bedrock Claude"""
        
        # Prepare prompt for Claude
        source_code = '\n\n'.join([
            f"# File: {filename}\n{content}"
            for filename, content in source_files.items()
            if filename.endswith('.py')
        ])
        
        prompt = f"""
<task>
Analyze this AWS Lambda function code and provide deployment recommendations.
</task>

<requirements>
- Identify the Lambda handler function(s)
- Determine runtime requirements and dependencies
- Assess memory and timeout requirements
- Identify security considerations
- Suggest optimization opportunities
- Recommend container base image
</requirements>

<code>
{source_code}
</code>

<output_format>
Respond with a JSON object containing:
{{
"handler_function": "module.function_name",
"runtime_version": "python3.12",
"estimated_memory": 512,
"estimated_timeout": 30,
"base_image_recommendation": "public.ecr.aws/lambda/python:3.12",
"security_recommendations": ["recommendation1", "recommendation2"],
"optimization_suggestions": ["suggestion1", "suggestion2"],
"required_packages": ["package1", "package2"]
}}
</output_format>
"""
        
        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2048,
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": prompt}]
                    }
                ]
            }
            
            response = self.bedrock_client.invoke_model(
                modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in Claude response")
                
        except Exception as e:
            # Fallback to basic analysis if AI analysis fails
            return {
                "handler_function": "lambda_function.lambda_handler",
                "runtime_version": "python3.12",
                "estimated_memory": 512,
                "estimated_timeout": 60,
                "base_image_recommendation": "public.ecr.aws/lambda/python:3.12",
                "security_recommendations": ["Use environment variables for configuration"],
                "optimization_suggestions": ["Minimize cold start time"],
                "required_packages": []
            }
    
    def _extract_dependencies(self, imports: List[str]) -> List[str]:
        """Extract Python package dependencies from imports"""
        # Common Python packages that need to be installed via pip
        dependencies = []
        
        # Mapping of import names to package names
        import_to_package = {
            'boto3': 'boto3',
            'botocore': 'botocore',
            'requests': 'requests',
            'numpy': 'numpy',
            'pandas': 'pandas',
            'scipy': 'scipy',
            'sklearn': 'scikit-learn',
            'cv2': 'opencv-python',
            'PIL': 'Pillow',
            'yaml': 'PyYAML',
            'click': 'click',
            'flask': 'Flask',
            'fastapi': 'fastapi',
            'pydantic': 'pydantic',
            'sqlalchemy': 'SQLAlchemy',
            'psycopg2': 'psycopg2-binary',
            'pymongo': 'pymongo',
            'redis': 'redis',
            'celery': 'celery',
            'pytest': 'pytest',
            'unittest': None,  # Built-in
            'json': None,      # Built-in
            'os': None,        # Built-in
            'sys': None,       # Built-in
            'datetime': None,  # Built-in
            'time': None,      # Built-in
            'logging': None,   # Built-in
            'pathlib': None,   # Built-in (Python 3.4+)
            'typing': None,    # Built-in (Python 3.5+)
            'asyncio': None,   # Built-in (Python 3.4+)
            'functools': None, # Built-in
            'itertools': None, # Built-in
            'collections': None, # Built-in
            'dataclasses': None, # Built-in (Python 3.7+)
            're': None,        # Built-in
            'math': None,      # Built-in
            'random': None,    # Built-in
            'hashlib': None,   # Built-in
            'base64': None,    # Built-in
            'urllib': None,    # Built-in
            'http': None,      # Built-in
            'email': None,     # Built-in
            'io': None,        # Built-in
            'tempfile': None,  # Built-in
            'shutil': None,    # Built-in
            'subprocess': None, # Built-in
            'multiprocessing': None, # Built-in
            'threading': None, # Built-in
            'concurrent': None, # Built-in
            'contextlib': None, # Built-in
            'warnings': None,  # Built-in
            'pickle': None,    # Built-in
            'csv': None,       # Built-in
            'xml': None,       # Built-in
            'html': None,      # Built-in
            'gzip': None,      # Built-in
            'zipfile': None,   # Built-in
            'tarfile': None,   # Built-in
            'uuid': None,      # Built-in
        }
        
        for import_name in imports:
            package = import_to_package.get(import_name)
            if package and package not in dependencies:
                dependencies.append(package)
            elif import_name not in import_to_package:
                # Unknown import - might be a third-party package
                # Add it as-is for manual review
                if not import_name.startswith('_') and import_name not in dependencies:
                    dependencies.append(import_name)
        
        return sorted(dependencies)
    
    def _generate_recommendations(self, static_analysis: Dict[str, Any], 
                                 ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate deployment recommendations based on analysis"""
        recommendations = {
            'memory_optimization': [],
            'performance_optimization': [],
            'security_recommendations': [],
            'cost_optimization': [],
            'deployment_recommendations': []
        }
        
        # Memory recommendations based on complexity and imports
        complexity = static_analysis.get('complexity_score', 0)
        if complexity > 20:
            recommendations['memory_optimization'].append(
                "Consider increasing memory allocation due to high code complexity"
            )
        
        imports = static_analysis.get('imports', [])
        heavy_packages = ['numpy', 'pandas', 'scipy', 'tensorflow', 'torch', 'cv2']
        if any(pkg in imports for pkg in heavy_packages):
            recommendations['memory_optimization'].append(
                "Increase memory allocation for data processing libraries"
            )
        
        # Performance recommendations
        if 'boto3' in imports:
            recommendations['performance_optimization'].append(
                "Use boto3 client reuse pattern to reduce cold start time"
            )
        
        if len(static_analysis.get('dependencies', [])) > 10:
            recommendations['performance_optimization'].append(
                "Consider reducing dependencies to minimize deployment package size"
            )
        
        # Security recommendations
        handlers = static_analysis.get('handlers', [])
        if not handlers:
            recommendations['security_recommendations'].append(
                "No Lambda handler functions detected - verify handler configuration"
            )
        
        recommendations['security_recommendations'].extend(
            ai_analysis.get('security_recommendations', [])
        )
        
        # Cost optimization
        estimated_memory = ai_analysis.get('estimated_memory', 512)
        if estimated_memory > 1024:
            recommendations['cost_optimization'].append(
                "Consider if high memory allocation is necessary for cost optimization"
            )
        
        estimated_timeout = ai_analysis.get('estimated_timeout', 60)
        if estimated_timeout > 300:
            recommendations['cost_optimization'].append(
                "Long timeout may impact cost - consider optimizing execution time"
            )
        
        # Deployment recommendations
        base_image = ai_analysis.get('base_image_recommendation', '')
        if 'python' in base_image:
            python_version = ai_analysis.get('runtime_version', 'python3.12')
            recommendations['deployment_recommendations'].append(
                f"Use {base_image} base image for {python_version} runtime"
            )
        
        if ai_analysis.get('optimization_suggestions'):
            recommendations['deployment_recommendations'].extend(
                ai_analysis.get('optimization_suggestions', [])
            )
        
        # Remove empty categories
        return {k: v for k, v in recommendations.items() if v}

class PythonAnalysisVisitor(ast.NodeVisitor):
    """AST visitor for Python code analysis"""
    
    def __init__(self):
        self.imports = set()
        self.handlers = []
        self.complexity = 0
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])
    
    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.add(node.module.split('.')[0])
    
    def visit_FunctionDef(self, node):
        # Check if function could be a Lambda handler
        if (len(node.args.args) >= 2 and 
            any(keyword in node.name.lower() for keyword in ['handler', 'lambda', 'main'])):
            self.handlers.append(node.name)
        
        # Count complexity (simplified)
        self.complexity += 1
        self.generic_visit(node)