"""
Command-line interface for the evi package.
"""
import sys
import click
import os

from .core import EviGenerator


@click.command()
@click.argument('prompt')
@click.option(
    '--framework', '-f',
    type=click.Choice(['crewai', 'langgraph', 'react'], case_sensitive=False),
    default='crewai',
    help='The agent framework to use.'
)
@click.option(
    '--provider', '-p',
    type=click.Choice(['openai', 'gemini'], case_sensitive=False),
    default='openai',
    help='The LLM provider to use.'
)
@click.option(
    '--model', '-m',
    help='The specific model to use (overrides the provider default).'
)
@click.option(
    '--format',
    type=click.Choice(['code', 'json'], case_sensitive=False),
    default='code',
    help='The output format to generate.'
)
@click.option(
    '--output', '-o',
    help='Save the generated code to a file.'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Show additional information during generation.'
)
def main(prompt: str, framework: str, provider: str, model: str, format: str, output: str, verbose: bool):
    """
    Generate agent code or configurations based on natural language descriptions.
    
    PROMPT is the natural language description of the agent system you want to create.
    """
    try:
        # Initialize the generator
        generator = EviGenerator(provider=provider, framework=framework)
        
        # Set specific model if provided
        if model:
            try:
                generator.provider.set_model_id(model)
                if verbose:
                    click.echo(f"Using model: {model}")
            except Exception as e:
                click.echo(f"Warning: Could not set model to {model}. Using default.", err=True)
        
        if verbose:
            click.echo(f"Generating {format} for {framework} framework using {provider} provider...")
            click.echo(f"Provider model: {generator.provider.get_model_id()}")
        
        # Generate the output
        result = generator.generate(prompt=prompt, output_format=format)
        
        # Save to file or print to console
        if output:
            with open(output, 'w') as f:
                f.write(result)
            click.echo(f"Output saved to {output}")
        else:
            click.echo(result)
            
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
