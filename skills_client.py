"""
Claude Skills Client for Excel/Document Generation

Uses the Anthropic API with Skills beta to generate Excel files, PowerPoint,
Word documents, and PDFs using Claude's built-in skills.

Reference: https://platform.claude.com/docs/en/build-with-claude/skills-guide
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


class SkillsClient:
    """
    Client for Claude's Skills API (xlsx, pptx, docx, pdf).
    
    Supports:
    - xlsx: Excel spreadsheet generation and analysis
    - pptx: PowerPoint presentation creation
    - docx: Word document generation
    - pdf: PDF document creation
    
    Usage:
        client = SkillsClient(api_key="...")
        result = await client.generate_excel(
            prompt="Create a budget spreadsheet with categories...",
            output_dir="/path/to/output"
        )
    """
    
    # Beta headers required for Skills API
    BETA_HEADERS = [
        "code-execution-2025-08-25",  # Required for code execution
        "skills-2025-10-02",          # Required for Skills API
        "files-api-2025-04-14",       # Required for file download
    ]
    
    # Available Anthropic-managed skills
    ANTHROPIC_SKILLS = {
        "xlsx": "Excel spreadsheet generation and analysis",
        "pptx": "PowerPoint presentation creation",
        "docx": "Word document generation",
        "pdf": "PDF document creation",
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Skills client.
        
        Args:
            api_key: Anthropic API key. If not provided, uses ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY or pass api_key.")
        
        self._client = None
    
    def _get_client(self):
        """Lazy-load Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "anthropic package required for Skills API. "
                    "Install with: pip install anthropic"
                )
        return self._client
    
    async def generate_with_skills(
        self,
        prompt: str,
        skills: List[str],
        output_dir: str,
        model: str = "claude-sonnet-4-5-20250929",
        max_tokens: int = 4096,
        max_retries: int = 10,
    ) -> Dict[str, Any]:
        """
        Generate content using Claude Skills.
        
        Args:
            prompt: The user prompt describing what to create
            skills: List of skill IDs to use (e.g., ["xlsx", "pptx"])
            output_dir: Directory to save generated files
            model: Claude model to use
            max_tokens: Maximum tokens for response
            max_retries: Max retries for pause_turn handling
            
        Returns:
            Dict with:
                - success: bool
                - files: List of downloaded file paths
                - response: Raw API response text
                - error: Error message if failed
        """
        client = self._get_client()
        
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Build skills list
        skill_configs = [
            {"type": "anthropic", "skill_id": skill, "version": "latest"}
            for skill in skills
            if skill in self.ANTHROPIC_SKILLS
        ]
        
        if not skill_configs:
            return {
                "success": False,
                "files": [],
                "response": "",
                "error": f"No valid skills provided. Available: {list(self.ANTHROPIC_SKILLS.keys())}"
            }
        
        try:
            # Make initial request
            response = client.beta.messages.create(
                model=model,
                max_tokens=max_tokens,
                betas=self.BETA_HEADERS,
                container={
                    "skills": skill_configs
                },
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                tools=[{
                    "type": "code_execution_20250825",
                    "name": "code_execution"
                }]
            )
            
            # Handle pause_turn for long operations
            messages = [{"role": "user", "content": prompt}]
            for _ in range(max_retries):
                if response.stop_reason != "pause_turn":
                    break
                
                messages.append({"role": "assistant", "content": response.content})
                response = client.beta.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    betas=self.BETA_HEADERS,
                    container={
                        "id": response.container.id,
                        "skills": skill_configs
                    },
                    messages=messages,
                    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
                )
            
            # Extract file IDs and download files
            file_ids = self._extract_file_ids(response)
            downloaded_files = []
            
            for file_id in file_ids:
                try:
                    file_path = await self._download_file(client, file_id, output_path)
                    if file_path:
                        downloaded_files.append(str(file_path))
                except Exception as e:
                    print(f"Warning: Failed to download file {file_id}: {e}")
            
            # Extract text response
            response_text = self._extract_text_response(response)
            
            return {
                "success": True,
                "files": downloaded_files,
                "response": response_text,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "files": [],
                "response": "",
                "error": str(e)
            }
    
    def _extract_file_ids(self, response) -> List[str]:
        """Extract file IDs from API response."""
        file_ids = []
        
        for item in response.content:
            # Check for bash code execution results
            if hasattr(item, 'type') and item.type == 'bash_code_execution_tool_result':
                if hasattr(item, 'content'):
                    content = item.content
                    if hasattr(content, 'type') and content.type == 'bash_code_execution_result':
                        if hasattr(content, 'content'):
                            for file in content.content:
                                if hasattr(file, 'file_id'):
                                    file_ids.append(file.file_id)
            
            # Also check for direct file references
            if hasattr(item, 'file_id'):
                file_ids.append(item.file_id)
        
        return file_ids
    
    def _extract_text_response(self, response) -> str:
        """Extract text content from response."""
        text_parts = []
        
        for item in response.content:
            if hasattr(item, 'type') and item.type == 'text':
                if hasattr(item, 'text'):
                    text_parts.append(item.text)
        
        return "\n".join(text_parts)
    
    async def _download_file(self, client, file_id: str, output_dir: Path) -> Optional[Path]:
        """Download a file from Claude's file storage."""
        try:
            # Get file metadata
            file_metadata = client.beta.files.retrieve_metadata(
                file_id=file_id,
                betas=["files-api-2025-04-14"]
            )
            
            # Download file content
            file_content = client.beta.files.download(
                file_id=file_id,
                betas=["files-api-2025-04-14"]
            )
            
            # Save to disk
            output_file = output_dir / file_metadata.filename
            file_content.write_to_file(str(output_file))
            
            return output_file
            
        except Exception as e:
            print(f"Error downloading file {file_id}: {e}")
            return None
    
    async def generate_excel(
        self,
        prompt: str,
        output_dir: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate an Excel spreadsheet.
        
        Args:
            prompt: Description of the spreadsheet to create
            output_dir: Directory to save the Excel file
            
        Returns:
            Dict with success status, file paths, and response
        """
        return await self.generate_with_skills(
            prompt=prompt,
            skills=["xlsx"],
            output_dir=output_dir,
            **kwargs
        )
    
    async def generate_presentation(
        self,
        prompt: str,
        output_dir: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a PowerPoint presentation.
        
        Args:
            prompt: Description of the presentation to create
            output_dir: Directory to save the PowerPoint file
            
        Returns:
            Dict with success status, file paths, and response
        """
        return await self.generate_with_skills(
            prompt=prompt,
            skills=["pptx"],
            output_dir=output_dir,
            **kwargs
        )
    
    async def generate_document(
        self,
        prompt: str,
        output_dir: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a Word document.
        
        Args:
            prompt: Description of the document to create
            output_dir: Directory to save the Word file
            
        Returns:
            Dict with success status, file paths, and response
        """
        return await self.generate_with_skills(
            prompt=prompt,
            skills=["docx"],
            output_dir=output_dir,
            **kwargs
        )
    
    async def analyze_and_create_excel(
        self,
        data_description: str,
        analysis_request: str,
        output_dir: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze data and create an Excel report.
        
        Args:
            data_description: Description of the data (e.g., from IFC analysis)
            analysis_request: What analysis to perform
            output_dir: Directory to save the Excel file
            
        Returns:
            Dict with success status, file paths, and response
        """
        prompt = f"""Based on the following data:

{data_description}

Please perform this analysis and create an Excel file:
{analysis_request}

Create a well-formatted Excel spreadsheet with:
- Clear headers and data organization
- Appropriate formatting (bold headers, number formats, etc.)
- Summary statistics if relevant
- Charts or visualizations if helpful for the data
"""
        
        return await self.generate_excel(
            prompt=prompt,
            output_dir=output_dir,
            **kwargs
        )


# Convenience function for use in orchestrator
async def create_excel_report(
    data: Dict[str, Any],
    request: str,
    output_dir: str,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create an Excel report from data using Claude's Excel skill.
    
    Args:
        data: Dictionary of data to include in the report
        request: What kind of report to create
        output_dir: Where to save the Excel file
        api_key: Anthropic API key (optional, uses env var if not provided)
        
    Returns:
        Dict with success, files, response, and error
    """
    import json
    
    client = SkillsClient(api_key=api_key)
    
    # Format data as readable description
    data_description = json.dumps(data, indent=2, default=str)
    
    return await client.analyze_and_create_excel(
        data_description=data_description,
        analysis_request=request,
        output_dir=output_dir
    )


# CLI for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Claude Skills API")
    parser.add_argument("--prompt", required=True, help="Prompt for skill")
    parser.add_argument("--skill", default="xlsx", choices=["xlsx", "pptx", "docx", "pdf"])
    parser.add_argument("--output-dir", default="./workspace", help="Output directory")
    
    args = parser.parse_args()
    
    async def test():
        client = SkillsClient()
        result = await client.generate_with_skills(
            prompt=args.prompt,
            skills=[args.skill],
            output_dir=args.output_dir
        )
        print(f"Success: {result['success']}")
        print(f"Files: {result['files']}")
        if result['error']:
            print(f"Error: {result['error']}")
        print(f"Response:\n{result['response']}")
    
    asyncio.run(test())
