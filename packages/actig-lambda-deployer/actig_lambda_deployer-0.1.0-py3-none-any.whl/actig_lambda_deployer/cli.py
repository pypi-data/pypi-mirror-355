import click
import logging
from pathlib import Path
from .config import Config
from .aws_clients import AWSClientManager
from .code_analyzer import LambdaCodeAnalyzer
from .artifact_generator import ArtifactGenerator
from .deployment_manager import DeploymentManager
from .utils.logging import setup_logging
from .utils.exceptions import DeploymentError

@click.group()
@click.option('--profile', default='default', help='AWS profile to use')
@click.option('--region', default='us-east-1', help='AWS region')
@click.option('--log-level', default='INFO', 
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']))
@click.option('--config-file', type=click.Path(), help='Configuration file path')
@click.pass_context
def cli(ctx, profile, region, log_level, config_file):
    """AWS Lambda Container Deployment CLI"""
    ctx.ensure_object(dict)
    
    # Setup logging
    logger = setup_logging(log_level)
    
    # Load configuration
    config = Config(config_file) if config_file else Config()
    config.aws_profile = profile
    config.aws_region = region
    
    # Initialize AWS clients
    client_manager = AWSClientManager(profile, region)
    
    ctx.obj.update({
        'config': config,
        'logger': logger,
        'client_manager': client_manager
    })

@cli.command()
@click.argument('source_path', type=click.Path(exists=True))
@click.option('--function-name', required=True, help='Lambda function name')
@click.option('--repository-name', help='ECR repository name')
@click.option('--dry-run', is_flag=True, help='Preview changes without deployment')
@click.pass_context
def deploy(ctx, source_path, function_name, repository_name, dry_run):
    """Analyze and deploy Lambda function as container image"""
    logger = ctx.obj['logger']
    config = ctx.obj['config']
    client_manager = ctx.obj['client_manager']
    
    try:
        source_path = Path(source_path)
        repository_name = repository_name or f"{function_name}-repo"
        
        # Check for required files
        requirements_path = source_path / 'requirements.txt'
        if not requirements_path.exists():
            click.echo(f"❌ Error: requirements.txt not found in {source_path}")
            click.echo("Please provide a requirements.txt file in your Lambda source directory.")
            ctx.exit(1)
        
        logger.info(f"Starting deployment for {function_name}")
        
        # Step 1: Analyze Lambda code
        analyzer = LambdaCodeAnalyzer(client_manager)
        analysis_result = analyzer.analyze_code(source_path)
        
        if dry_run:
            click.echo("=== DRY RUN MODE ===")
            click.echo(f"Analysis Result: {analysis_result}")
            return
        
        # Step 2: Generate artifacts using Bedrock Claude
        generator = ArtifactGenerator(client_manager)
        artifacts = generator.generate_artifacts(analysis_result)
        
        # Step 3: Deploy infrastructure and code
        deployment_manager = DeploymentManager(client_manager, config)
        deployment_result = deployment_manager.deploy(
            function_name=function_name,
            repository_name=repository_name,
            source_path=source_path,
            artifacts=artifacts
        )
        
        click.echo(f"✅ Deployment successful!")
        click.echo(f"Function ARN: {deployment_result['function_arn']}")
        click.echo(f"Image URI: {deployment_result['image_uri']}")
        
    except DeploymentError as e:
        logger.error(f"Deployment failed: {e}")
        click.echo(f"❌ Deployment failed: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.exception("Unexpected error during deployment")
        click.echo(f"❌ Unexpected error: {e}", err=True)
        raise click.Abort()

@cli.command()
@click.argument('function_name')
@click.pass_context
def status(ctx, function_name):
    """Check deployment status"""
    client_manager = ctx.obj['client_manager']
    
    lambda_client = client_manager.get_client('lambda')
    
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        function_config = response['Configuration']
        
        click.echo(f"Function: {function_config['FunctionName']}")
        click.echo(f"Runtime: {function_config.get('PackageType', 'Zip')}")
        click.echo(f"State: {function_config['State']}")
        click.echo(f"Last Modified: {function_config['LastModified']}")
        
        if function_config.get('PackageType') == 'Image':
            click.echo(f"Image URI: {function_config['Code']['ImageUri']}")
            
    except client_manager.get_client('lambda').exceptions.ResourceNotFoundException:
        click.echo(f"❌ Function {function_name} not found")
    except Exception as e:
        click.echo(f"❌ Error checking status: {e}")

if __name__ == '__main__':
    cli()